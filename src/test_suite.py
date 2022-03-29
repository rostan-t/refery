import argparse
import pathlib
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

import yaml
from colorama import Fore, Style

import src.custom_io as io
from src.prettify import print, decorate, pretty_assert, pretty_diff


class OutputMode(Enum):
    """
    The way the output is tested
    They are currently two possible modes:
        - strict: Compare the output with the expected result.
                  If their is are not the same, stop the test
        - exists: Fail if their is an expected output but the tested binary
                  outputs nothing, or if the tested outputs something but
                  nothing was expected.
    """

    STRICT = 'strict',
    EXISTS = 'exists',

    def compare_outputs(self, expected: str, actual: str) -> Optional[str]:
        """
        Compare strings according to the output mode.

        :param expected: The expected output.
        :param actual: The actual output.
        :return: Returns string containing the reason for failure if the comparison fails, else <code>None</code>.
        """

        if self.value[0] == 'exists':
            return 'expected nothing, got something' if expected == '' and actual != '' \
                else 'expected something, got nothing' if expected != '' and actual == '' \
                else None

        return None if expected == actual else pretty_diff(actual, expected)


@dataclass
class TestCase:
    """
    A test case

    Arguments
    ---------
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

    def __post_init__(self):
        if isinstance(self.stdout_mode, str):
            self.stderr_mode = OutputMode[self.stdout_mode.upper()]
        if isinstance(self.stderr_mode, str):
            self.stderr_mode = OutputMode[self.stderr_mode.upper()]

        # The ref overrides undefined outputs
        if self.ref is not None:
            ref = pathlib.Path(self.ref).resolve()
            process = subprocess.Popen(
                [ref, *self.args],
                stdin=subprocess.PIPE if self.stdin is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if self.stdin is not None:
                process.stdin.write(self.stdin.encode())
                process.stdin.close()
            process.wait()

            self.stdout = process.stdout.read().decode() \
                if self.stdout is None else self.stdout
            self.stderr = process.stderr.read().decode() \
                if self.stderr is None else self.stderr
            self.exit_code = process.returncode \
                if self.exit_code is None else self.exit_code

    @staticmethod
    def _print_command(name: str, args: List[str]):
        """
        Print a command execution

        :param name: Name of the command
        :param args: Arguments passed to the command
        """

        decorations = (Style.DIM,)
        print('$', name, end='\t', decorations=decorations)
        if len(args) != 0:
            print(end=' ')
            escaped = [arg if ' ' not in arg else f'"{arg}"' for arg in args]
            print(' '.join(escaped), decorations=decorations)

    def run(self, binary: pathlib.Path) -> bool:
        """
        Run the test case

        :param binary: Path to the tested executable
        :return: Returns `True` if everything passes, `False` instead
        """

        process = subprocess.Popen(
            [binary, *self.args],
            stdin=subprocess.PIPE if self.stdin is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if self.stdin is not None:
            process.stdin.write(self.stdin.encode())
            process.stdin.close()

        print('testing:', decorations=(Style.DIM,))
        self._print_command(binary.name, self.args)
        if self.ref is not None:
            print('against:', decorations=(Style.DIM,))
            self._print_command(self.ref, self.args)

        try:
            process.wait(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            print('⏱  sh'
                  'TIMEOUT', decorations=(Style.BRIGHT, Fore.RED))
            return False

        stdout = process.stdout.read().decode()
        stderr = process.stderr.read().decode()
        exit_code = process.returncode

        return self.__run_assertions(stdout, stderr, exit_code)

    def __run_assertions(self, stdout: str, stderr: str,
                         exit_code: int) -> bool:
        passing = True

        # I use & instead of `and` because I don't want any assertion skipped
        if self.stdout is not None:
            passing &= pretty_assert(
                'standard outputs',
                actual=stdout,
                expected=self.stdout,
                compare=self.stdout_mode.compare_outputs
            )
        if self.stderr is not None:
            passing &= pretty_assert(
                'standard errors',
                actual=stderr,
                expected=self.stderr,
                compare=self.stderr_mode.compare_outputs
            )

        passing &= pretty_assert(
            'exit codes',
            actual=exit_code,
            expected=self.exit_code,
            compare=lambda actual, expected: None if actual == expected
            else f'expected {decorate(expected, Fore.GREEN)}, '
                 f'got {decorate(actual, Fore.RED)}'
        )

        return passing


@dataclass
class TestSuite:
    """
    A simple test suite

    Arguments
    ---------
        exec    Path to the tested executable
        tests   List of test cases
    """

    exec: pathlib.Path
    tests: List[TestCase] = field(default_factory=lambda: [])

    def add_test(self, test: TestCase):
        """Add a test case at the end of the test suite"""

        self.tests.append(test)

    def run(self):
        """
        Run all the tests in the testsuite

        :return: Returns 0 if all tests succeeded, else 1
        """

        total = len(self.tests)
        exit_code = 0
        for no, test in enumerate(self.tests):
            print(f'{no + 1}/{total}', decorate(test.name, Style.BRIGHT),
                  end='\t\t')

            if test.skipped:
                print(decorate('SKIPPED', Style.BRIGHT, Fore.BLUE))
                continue

            io.disable_stdout()
            success = test.run(self.exec)
            test_output = sys.stdout.read()
            io.enable_stdout()

            if success:
                print(decorate('OK', Style.BRIGHT, Fore.LIGHTGREEN_EX))
            else:
                print(decorate('KO', Style.BRIGHT, Fore.LIGHTRED_EX))
                print(test_output)
                exit_code = 1
        return exit_code


def get_testsuite() -> TestSuite:
    """
    Read the arguments from the command line and generate a test suite.

    :return: Returns the generated test suite.
    """

    # 1- Parse the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--exec', type=pathlib.Path, required=True,
                        help='path to the tested executable')
    parser.add_argument('--test-file', type=pathlib.Path, required=True,
                        help='path to the yaml test file')
    cmd_args = parser.parse_args()

    # 2- Setup the tests
    testsuite = TestSuite(exec=cmd_args.exec.resolve())
    with open(cmd_args.test_file.resolve(), 'r') as file:
        try:
            test_suite = yaml.safe_load(file)
            for test in test_suite:
                test_case = TestCase(name=test, **test_suite[test])
                testsuite.add_test(test_case)
        except yaml.YAMLError as error:
            print(error, file=sys.stderr)
            exit(1)

    return testsuite
