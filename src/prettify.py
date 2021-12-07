from difflib import unified_diff
from typing import Optional, Callable, TypeVar, Type, Iterable

from colorama.ansi import AnsiCodes, Fore, Style


def __get_diff_color(line: str) -> Optional[AnsiCodes]:
    if line.startswith('+'):
        return Fore.GREEN
    elif line.startswith('-'):
        return Fore.RED
    elif line.startswith('^'):
        return Fore.BLUE
    else:
        return None


def decorate(input: str, *decorations: Iterable[AnsiCodes]) -> str:
    if len(decorations) == 0:
        return input

    prefix = ''.join(map(str, decorations))
    return f'{prefix}{input}{Fore.RESET}{Style.RESET_ALL}'


def __pretty_diff(actual: str, expected: str) -> str:
    actual_lines = actual.replace('\n', '↵\n').splitlines()
    expected_lines = expected.replace('\n', '↵\n').splitlines()

    diff_lines = unified_diff(
        actual_lines,
        expected_lines,
        fromfile='actual',
        tofile='expected',
        lineterm='',
    )
    diff_lines = list(diff_lines)
    colored_lines = [
        decorate(line, __get_diff_color(line)) for line in diff_lines
    ]

    return '\n'.join(colored_lines)


T = TypeVar('T')


def pretty_assert(name: str, actual: T, expected: T,
                  compare: Callable[[T, T], bool], type: Type = str) -> bool:
    """
    Execute the `compare` function on `actual` and `expected`
    and pretty-print a report.


    :param name: The name of the assertion
    :param actual: The actual value
    :param expected: The expected value
    :param compare: The comparison function.
                    Takes the actual value and the expected value as parameters
    :param type: The type of the arguments - defaults to `str`
    :return: The value of the compare function applied to actual and expected
    """

    if compare(actual, expected):
        return True

    print(f'Different {name}:', end='')

    if type is str:
        print()
        print(__pretty_diff(actual=actual, expected=expected))
    else:
        print(f'expected {expected}, got {actual}')
