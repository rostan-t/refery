from dataclasses import dataclass
from typing import Generic, TypeVar

from rich.console import RenderableType, escape
from rich.panel import Panel

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
