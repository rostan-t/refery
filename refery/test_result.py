import enum
import itertools
from collections.abc import Iterable
from dataclasses import dataclass, field

from rich.console import RenderableType, RenderResult, escape, group
from rich.panel import Panel


class Verbosity(enum.Enum):
    """
    Verbosity of the output.
    - SILENT: only the test results i.e. failure/success are printed
    - NORMAL: everything except the command being executed is printed
    - VERBOSE: everything is printed, including the command being executed
    """

    SILENT = "silent"
    NORMAL = "normal"
    VERBOSE = "verbose"


class TestStatus(enum.Enum):
    """
    Status of a test case.
    - SUCCESS: everything went well
    - FAILURE: the test failed without any error
    - ERROR: an error occurred while running the test
    - SKIPPED: the test has not been run
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
    verbosity: Verbosity = Verbosity.NORMAL
    command: str | None = None

    def __post_init__(self):
        self.name = escape(self.name)

    def __rich__(self) -> RenderResult:
        title = f"[{self.status.style}]{self.status.icon} [b]{self.name}[/][/]"

        itered_outputs = iter(self.outputs)
        try:
            first = next(itered_outputs)
        except StopIteration:  # There is no output
            return title

        # Restore so as not to alter future calls
        if self.outputs is itered_outputs:
            self.outputs = itertools.chain([first], self.outputs)

        panel = Panel(
            self.grouped_output,
            title=title,
            title_align="left",
            border_style=self.status.style,
        )
        children = panel.renderable.renderables

        if children:
            return panel

    @property
    @group()
    def grouped_output(self):
        if self.command is not None and self.verbosity is Verbosity.VERBOSE:
            yield f"[blue]$ [u]{self.command}[/][/]\n"

        yield from self.outputs
