import enum
from dataclasses import dataclass
from typing import Iterable

from rich.console import (
    Console,
    ConsoleOptions,
    RenderableType,
    RenderResult,
    escape,
)


class TestStatus(enum.Enum):
    """
    Status of a test case.
    """

    SUCCESS = "ok"
    FAILURE = "ko"
    ERROR = "error"
    SKIPPED = "skipped"

    @property
    def icon(self) -> str:
        match self:
            case TestStatus.SUCCESS:
                return "\u2714"  # Check mark
            case TestStatus.FAILURE:
                return "\u2718"  # X-mark
            case TestStatus.ERROR:
                return "\u203c"  # Double bang
            case TestStatus.SKIPPED:
                return "\u2298"  # Slashed circle

    @property
    def style(self) -> str:
        match self:
            case TestStatus.SUCCESS:
                return "green"
            case TestStatus.FAILURE:
                return "red"
            case TestStatus.ERROR:
                return "bold red"
            case TestStatus.SKIPPED:
                return "yellow"


@dataclass
class TestResult:
    """
    Result of a test case
    """

    name: str
    status: TestStatus
    command: str
    outputs: Iterable[RenderableType]

    def __post_init__(self):
        self.name = escape(self.name)

    def __rich_console__(
        self,
        _console: Console,
        _options: ConsoleOptions,
    ) -> RenderResult:

        yield f"[{self.status.style}]{self.status.icon} [i]{self.name}[/][/]"
        yield from self.outputs
