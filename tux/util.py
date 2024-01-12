# tux/utils.py

from collections.abc import Callable
from datetime import UTC, datetime


def get_local_time() -> datetime:
    """Returns the current local time.

    Returns:
        Offset aware datetime object.
    """
    local_timezone = datetime.now(UTC).astimezone().tzinfo
    return datetime.now(local_timezone)


def days(day: str | int) -> str:
    """Humanize the number of days.

    Args:
      day: Union[int, str]
          The number of days passed.

    Returns:
      str
          A formatted string of the number of days passed.
    """
    day = int(day)
    if day == 0:
        return "**today**"
    return f"{day} day ago" if day == 1 else f"{day} days ago"


def truncate(text: str, max_len: int = 1024) -> str:
    """Truncate a paragraph to a specific length.

    Args:
        text: The paragraph to truncate.
        max_len: The maximum length of the paragraph.

    Returns:
        The truncated paragraph.
    """
    etc = "\n[…]"
    return (
        f"{text[:max_len - len(etc)]}{etc}" if len(text) > max_len - len(etc) else text
    )


def ordinal(n):
    """Return number with ordinal suffix eg. 1st, 2nd, 3rd, 4th..."""
    return str(n) + {1: "st", 2: "nd", 3: "rd"}.get(
        4 if 10 <= n % 100 < 20 else n % 10, "th"
    )


def is_convertible_to_type(string: str, type_func: Callable[..., object]) -> bool:
    """Checks if the string can be converted to a specific type

    Args:
      string (str): The string to check
      type_func (callable): The function to use for conversion

    Returns:
      Boolean: Whether the string could be converted to the specified type or not
    """
    try:
        type_func(string)
        return True
    except ValueError:
        return False


def is_integer(string):
    return is_convertible_to_type(string, int)


def is_float(string):
    return is_convertible_to_type(string, float)


class DummyParam:
    """
    A dummy parameter that can be used for MissingRequiredArgument.
    """

    def __init__(self, name):
        self.name = name
        self.displayed_name = name
