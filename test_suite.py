import argparse
import pathlib
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

import yaml


class OutputMode(Enum):
    """
    The way the output is tested.
    They are currently two possible modes:
        - strict: Compare the output with the expected result.
                  If their is are not the same, stop the test.
        - exists: Fail if their is an expected output but the tested binary
                  outputs nothing, or if the tested outputs something but
                  nothing was expected.
    """

    STRICT = auto(),
    EXISTS = auto(),


@dataclass
class TestCase:
    """
    A test case

    Arguments
    ---------
        args            The arguments passed to the executable
        ref             (optional) Path to a binary with the expected outputs
        stdout          (optional) The expected standard output
        stderr          (optional) The expected standard error
        exit_code       (optional) The expected exit code
        stdout_mode     See `OutputMode` - Default value: STRICT
        stderr_mode     See `OutputMode` - Default value: STRICT
    """

    args: str
    ref: Optional[pathlib.Path] = None

    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None

    stdout_mode: OutputMode = OutputMode.STRICT
    stderr_mode: OutputMode = OutputMode.STRICT

    def __post_init__(self):
        if isinstance(self.stdout_mode, str):
            self.stderr_mode = OutputMode[self.stdout_mode.upper()]
        if isinstance(self.stderr_mode, str):
            self.stderr_mode = OutputMode[self.stderr_mode.upper()]


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
        """Add a test case at the end of the test suite."""
        self.tests.append(test)


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
                test_case = TestCase(**test_suite[test])
                testsuite.add_test(test_case)
        except yaml.YAMLError as error:
            print(error, file=sys.stderr)
            exit(1)

    return testsuite
