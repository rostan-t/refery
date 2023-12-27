import argparse
import pathlib
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional

import junit_xml as jxml
import yaml
from rich.console import Console, escape

from refery.diff import OutputMode, ValueDiff
from refery.test_result import TestResult, TestStatus, Verbosity


@dataclass
class TestCase:
    """
    A test case

    Arguments
    ---------
        binary          Path to the tested binary
        name            The name of the test case
        args            (optional) The arguments passed to the executable
        ref             (optional) Path to a binary with the expected outputs
        stdin           (optional) String to pass in the standard input
        stdout          (optional) Expected standard output
        stderr          (optional) Expected standard error
        exit_code       (optional) Expected exit code
        stdout_mode     See `OutputMode` - defaults to STRICT
        stderr_mode     See `OutputMode` - defaults STRICT
        skipped         (optional) Indicates if the test is ignored
        timeout         (optional) Timeout in seconds
    """

    binary: pathlib.Path
    name: str

    args: List[str] = field(default_factory=lambda: [])
    ref: str = None

    stdin: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None

    stdout_mode: OutputMode = OutputMode.STRICT
    stderr_mode: OutputMode = OutputMode.STRICT

    skipped: bool = False
    timeout: Optional[float] = None

    init_error: str | None = None

    def __post_init__(self):
        if isinstance(self.binary, str):
            self.binary = pathlib.Path(self.binary).resolve()
        if isinstance(self.stdout_mode, str):
            self.stderr_mode = OutputMode[self.stdout_mode.upper()]
        if isinstance(self.stderr_mode, str):
            self.stderr_mode = OutputMode[self.stderr_mode.upper()]

        # The ref overrides undefined outputs
        if not self.skipped and self.ref is not None:
            ref = pathlib.Path(self.ref).resolve()
            try:
                process = subprocess.Popen(
                    [ref, *self.args],
                    stdin=subprocess.PIPE if self.stdin is not None else None,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except FileNotFoundError:
                self.init_error = f"No such file or directory: [b]{self.ref}[/]"
                return

            if self.stdin is not None:
                process.stdin.write(self.stdin.encode())
                process.stdin.close()
                process.wait()

            self.stdout = (
                process.stdout.read().decode() if self.stdout is None else self.stdout
            )
            self.stderr = (
                process.stderr.read().decode() if self.stderr is None else self.stderr
            )
            self.exit_code = (
                process.returncode if self.exit_code is None else self.exit_code
            )

            process.terminate()

    def run(self, verbosity: Verbosity) -> TestResult:
        """
        Run the test case.

        :param verbosity: Output verbosity.
        :return: A TestResult representing the outcome of the test.
        """

        if self.skipped:
            return TestResult(self.name, TestStatus.SKIPPED)

        if self.init_error is not None:
            return TestResult(
                name=self.name,
                status=TestStatus.ERROR,
                outputs=(self.init_error,),
                verbosity=verbosity,
                command=self.__get_command(verbosity),
            )

        try:
            process = subprocess.Popen(
                [self.binary, *self.args],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            return TestResult(
                name=self.name,
                status=TestStatus.ERROR,
                outputs=(f"No such file or directory: [b]{self.binary}[/]",),
                verbosity=verbosity,
                command=self.__get_command(verbosity),
            )

        try:
            stdin = None if self.stdin is None else self.stdin.encode()
            stdout, stderr = process.communicate(stdin, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            return TestResult(
                name=self.name,
                status=TestStatus.FAILURE,
                outputs=(f"[b]{self.timeout}s[/] timeout exceeded.",),
                verbosity=verbosity,
                command=self.__get_command(verbosity),
            )
        else:
            return self.__run_assertions(
                stdout=stdout.decode(),
                stderr=stderr.decode(),
                exit_code=process.returncode,
                verbosity=verbosity,
            )
        finally:
            process.terminate()

    def __run_assertions(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
        verbosity: Verbosity,
    ) -> TestResult:
        diffs = []

        if (
            diff := self.stdout_mode.compare(
                "Standard outputs", expected=self.stdout, actual=stdout
            )
        ) is not None:
            diffs.append(diff)

        if (
            diff := self.stderr_mode.compare(
                "Standard errors", expected=self.stderr, actual=stderr
            )
        ) is not None:
            diffs.append(diff)

        if self.exit_code is not None and self.exit_code != exit_code:
            diffs.append(
                ValueDiff(
                    "Return codes",
                    expected=self.exit_code,
                    actual=exit_code,
                )
            )

        status = TestStatus.SUCCESS if not diffs else TestStatus.FAILURE
        result = TestResult(
            self.name,
            status,
            outputs=diffs,
            verbosity=verbosity,
            command=self.__get_command(verbosity),
        )

        return result

    def __get_command(self, verbosity: Verbosity):
        command = None
        if verbosity is Verbosity.VERBOSE:
            command = shlex.join(["./" + self.binary.name] + self.args)

        return command


@dataclass
class TestSuite:
    """
    A simple test suite containing test cases.

    Arguments
    ---------
        name        Name of the test suite.
        tests       (optional) List of test cases.
        setup       (optional) Command to execute before each test case.
        teardown    (optional) Command to execute after each test case.
        fatal       Indicates if a failure in a test case means an abortion of the runner - defaults to false.
        verbosity   Output's verbosity - defaults to NORMAL
    """

    name: str
    tests: List[TestCase] = field(default_factory=lambda: [])

    setup: Optional[str] = None
    teardown: Optional[str] = None

    fatal: bool = False
    verbosity: Verbosity = Verbosity.NORMAL

    def __post_init__(self):
        self._console = Console(width=80)
        self.junit_test_suite = jxml.TestSuite(name=self.name)

    def __setup(self):
        if self.setup is not None:
            # TODO: Handle errors
            subprocess.run(self.setup.split(), check=False)

    def __teardown(self):
        if self.teardown is not None:
            subprocess.run(self.teardown.split(), check=False)

    def add_test(self, test: TestCase):
        """Add a test case at the end of the test suite"""

        self.tests.append(test)

    def run(self) -> int:
        """
        Run all the tests in the testsuite

        :return: Returns 0 if all tests succeeded, else 1
        """

        console = self._console
        console.print()

        title = escape(self.name.title())
        line_char = "\u2501"
        console.rule(
            f"{line_char * 2} {title}",
            style="default",
            characters=line_char,
            align="left",
        )

        exit_code = 0
        for test in self.tests:
            start_time = time.time()

            with console.status(f"Running {test.name}"):
                self.__setup()
                result = test.run(self.verbosity)
                self.__teardown()

            console.print(result)

            stop_time = time.time()
            elapsed_time = (stop_time - start_time) / 1000

            jxml_testcase = jxml.TestCase(
                name=test.name,
                classname=f"{self.name}.{test.name}",
                elapsed_sec=elapsed_time,
            )

            self.junit_test_suite.test_cases.append(jxml_testcase)

        return exit_code


def get_testsuites():
    """
    Read the arguments from the command line and generate a test suite.

    :return: Returns the generated test suite.
    """

    # 1- Parse the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--test-file",
        type=pathlib.Path,
        required=True,
        metavar="<path>",
        help="Path to the YAML test file.",
    )
    parser.add_argument(
        "--verbosity",
        type=Verbosity,
        required=False,
        default=Verbosity.NORMAL,
        metavar=f"<{'|'.join([v.value.lower() for v in Verbosity])}>",
        help="Output's verbosity, defaults to 'normal'.",
    )
    parser.add_argument(
        "--junit-file",
        type=pathlib.Path,
        required=False,
        metavar="<path>",
        help="Optional path to a JUnit XML file in which to write the output.",
    )

    cmd_args = parser.parse_args()

    # 2- Read the YAML file
    with open(cmd_args.test_file.resolve(), "r") as file:
        try:
            yaml_content = yaml.safe_load(file)
        except yaml.YAMLError as error:
            print(error, file=sys.stderr)
            exit(1)

    # 3- Setup the tests
    testsuites = []
    defaults = yaml_content.get("default", {})
    for yaml_testsuite in yaml_content["testsuites"]:
        yaml_testsuite["tests"] = [
            TestCase(**{**defaults, **test}) for test in yaml_testsuite["tests"]
        ]
        testsuite = TestSuite(verbosity=cmd_args.verbosity, **yaml_testsuite)
        testsuites.append(testsuite)

    return testsuites, cmd_args.junit_file
