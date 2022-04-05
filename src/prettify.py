import re
from difflib import unified_diff
from typing import Optional, Callable, TypeVar, Type, Iterable, IO

from colorama.ansi import AnsiCodes, Fore, Style

_ANSI_decorations = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')


def __get_diff_color(line: str) -> Optional[str]:
    if line.startswith('+'):
        return Fore.GREEN

    elif line.startswith('-'):
        return Fore.RED
    elif line.startswith('@'):
        return Fore.BLUE
    else:
        return None


def decorate(input: str, *decorations: Optional[Iterable[AnsiCodes]]) -> str:
    if decorations is None or len(decorations) == 0:
        return input

    prefix = ''.join(map(str, filter(lambda dec: dec is not None, decorations)))
    return f'{prefix}{input}{Fore.RESET}{Style.RESET_ALL}'


def remove_decorations(input: str) -> str:
    return re.sub(_ANSI_decorations, '', input)


def pretty_diff(actual: str, expected: str) -> str:
    actual_lines = actual.replace('\n', '↵\n').splitlines()
    expected_lines = expected.replace('\n', '↵\n').splitlines()

    diff_lines = unified_diff(
        expected_lines,
        actual_lines,
        fromfile='got',
        tofile='expected',
        lineterm='',
    )
    colored_lines = [
        decorate(line, __get_diff_color(line)) for line in diff_lines
    ]

    return '\n'.join(colored_lines)


T = TypeVar('T')


def pretty_assert(name: str, actual: T, expected: T,
                  compare: Callable[[T, T], Optional[str]],
                  type: Type = str) -> bool:
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

    msg = compare(actual, expected)
    if msg is None:
        return True

    print(f'Different {decorate(name, Style.BRIGHT, Fore.BLUE)}: \n{msg}')

    if type is str:
        print()
    else:
        print(f'expected {decorate(expected, Fore.GREEN)}'
              f', got {decorate(actual, Fore.RED)}')

    return False


__print = print


def print(*args, sep: Optional[str] = ' ', end: Optional[str] = '\n',
          file: Optional[IO] = None, flush: bool = False,
          decorations: Iterable[str] = ()):
    __print(*map(lambda arg: decorate(arg, *decorations), args),
            sep=sep, end=end, file=file, flush=flush)
