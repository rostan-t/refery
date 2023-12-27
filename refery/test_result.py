import enum
from dataclasses import dataclass, field
from typing import Iterable

from rich.console import (
    Console,
    ConsoleOptions,
    RenderableType,
    RenderResult,
    escape,
    group,
)
from rich.panel import Panel


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
                return "dim"


@dataclass
class TestResult:
    """
    Result of a test case.
    """

    name: str
    status: TestStatus
    outputs: Iterable[RenderableType] = field(default_factory=lambda: [])

    def __post_init__(self):
        self.name = escape(self.name)

    def __rich__(self) -> RenderResult:
        title = f"[{self.status.style}]{self.status.icon} [b]{self.name}[/][/]"

        panel = Panel(
            self.grouped_output,
            title=title,
            title_align="left",
            border_style=self.status.style,
        )
        children = panel.renderable.renderables

        if children:
            return panel

        return title

    @property
    @group()
    def grouped_output(self):
        yield from self.outputs
