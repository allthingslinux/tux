"""Helpers for interpreting ``asyncio.gather(..., return_exceptions=True)`` results."""

from typing import TypeVar

__all__ = ["handle_gather_result"]

T = TypeVar("T")


def handle_gather_result[T](result: T | BaseException, expected_type: type[T]) -> T:
    """Handle a result from asyncio.gather with return_exceptions=True.

    Parameters
    ----------
    result : T | BaseException
        The result from asyncio.gather
    expected_type : type[T]
        The expected type of the result

    Returns
    -------
    T
        The result if it matches the expected type

    Raises
    ------
    BaseException
        Re-raises if result is an exception instance.
    TypeError
        If the result is not of the expected type
    """
    if isinstance(result, BaseException):
        raise result
    if not isinstance(result, expected_type):
        msg = f"Expected {expected_type.__name__} but got {type(result).__name__}"
        raise TypeError(msg)
    return result
