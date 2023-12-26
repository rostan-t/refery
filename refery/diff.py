import enum
from dataclasses import dataclass
from difflib import unified_diff
from itertools import filterfalse, islice
from typing import Generic, TypeVar

from rich.console import Group, RenderableType, escape
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

T = TypeVar("T")


@dataclass
class ValueDiff(Generic[T]):
    """
    Simple difference between any two objects.
    """

    name: str
    expected: T
    actual: T

    def __post_init__(self):
        self.name = escape(self.name)

    def __rich__(self) -> RenderableType:
        content = f"Expected [green]{self.expected}[/], got [red]{self.actual}[/]"

        return Panel(content, title=self.name, title_align="left", border_style="b")


@dataclass
class TextualDiff:
    """
    Difference between two multiline strings.
    """

    name: str
    expected: str
    actual: str

    def __post_init__(self):
        self.name = escape(self.name)
        self.expected = escape(self.expected)
        self.actual = escape(self.actual)

    def __rich__(self) -> RenderableType:
        # Whenever there is a possible ambiguity, explicitly display newlines
        pretty_newline = "\u21b5\n"
        if self.actual.endswith("\n") is self.expected.endswith("\n"):
            pretty_newline = "\n"

        actual_lines = self.actual.replace("\n", pretty_newline).splitlines()
        expected_lines = self.expected.replace("\n", pretty_newline).splitlines()

        diff_lines = unified_diff(actual_lines, expected_lines, lineterm="")
        # Remove the header lines
        diff_lines = islice(diff_lines, 2, None)
        diff_lines = filterfalse(lambda s: s.startswith("@"), diff_lines)

        diff_content = map(self.__format_line, diff_lines)

        header = "[red]--- got[/]\n[green]+++ expected[/]"

        return Panel(
            Group(header, Rule(style=""), *diff_content),
            title=self.name,
            title_align="left",
            border_style="b",
        )

    @staticmethod
    def __format_line(line) -> Text | str:
        """
        Apply necessary formatting to each diff line.
        This essentially consists in setting the right colors.
        """

        line = line.removesuffix("\n")

        diff_configs = [
            {"prefix": "-", "color": "red"},
            {"prefix": "+", "color": "green"},
        ]
        for config in diff_configs:
            color, prefix = config["color"], config["prefix"]
            if line.startswith(prefix):
                text = Text(prefix + " ", style=color, justify="left")
                text.append(
                    line.removeprefix(prefix),
                    style=f"on dark_{color}",
                )

                return text

        return " " + line


class OutputMode(enum.Enum):
    """
    The way the output is tested
    They are currently two possible modes:
        - strict: Compare the output with the expected result.
                  If their is are not the same, stop the test
        - exists: Fail if their is an expected output but the tested binary
                  outputs nothing, or if the tested outputs something but
                  nothing was expected.
    """

    STRICT = "strict"
    EXISTS = "exists"

    def compare(
        self,
        name: str,
        expected: str,
        actual: str,
    ) -> RenderableType | None:
        """
        Compare strings according to the output mode.

        :param diff: Name of the strings being compared -- typically stdout/stderr.
        :param expected: The expected output.
        :param actual: The actual output.
        :return: Returns the appropriate diff if the comparison fails, else None.
        """

        # If there is no value to compare to, assume a success
        if expected is None:
            return None

        match self:
            case OutputMode.EXISTS:
                if expected == "" and actual != "":
                    return ValueDiff(name, expected="nothing", actual="something")

                if expected != "" and actual == "":
                    return ValueDiff(name, expected="something", actual="nothing")

                return None
            case OutputMode.STRICT:
                if expected == actual:
                    return None

                return TextualDiff(name, expected=expected, actual=actual)
