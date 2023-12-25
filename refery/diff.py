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
        self.name = f"{escape(self.name)} differ"

    def __rich__(self) -> RenderableType:
        content = f"Expected [green]{self.expected}[/], got [red]{self.actual}[/]"

        return Panel(content, title=self.name)


@dataclass
class TextualDiff:
    """
    Difference between two multiline strings.
    """

    name: str
    expected: str
    actual: str

    def __post_init__(self):
        self.name = f"{escape(self.name)} differ"
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


# Useful shortcuts
def stdout_diff(*, expected: str, actual: str):
    return TextualDiff(
        name="Standard outputs",
        expected=expected,
        actual=actual,
    )


def stderr_diff(*, expected: str, actual: str):
    return TextualDiff(
        name="Standard errors",
        expected=expected,
        actual=actual,
    )


def return_diff(*, expected: T, actual: T):
    return ValueDiff(
        name="Return codes",
        expected=expected,
        actual=actual,
    )
