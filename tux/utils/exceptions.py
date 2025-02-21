from typing import TypeVar

from prisma.models import Case


class PermissionLevelError(Exception):
    """Raised when a user doesn't have the required permission level."""

    def __init__(self, permission: str) -> None:
        self.permission = permission
        super().__init__(f"Missing required permission: {permission}")


class AppCommandPermissionLevelError(Exception):
    """Raised when a user doesn't have the required permission level for an app command."""

    def __init__(self, permission: str) -> None:
        self.permission = permission
        super().__init__(f"Missing required permission: {permission}")


T = TypeVar("T")


def handle_gather_result(result: T | BaseException, expected_type: type[T]) -> T:
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
        If the result is an exception
    TypeError
        If the result is not of the expected type
    """
    if isinstance(result, BaseException):
        raise result
    if not isinstance(result, expected_type):
        msg = f"Expected {expected_type.__name__} but got {type(result).__name__}"
        raise TypeError(msg)
    return result


def handle_case_result(case_result: Case | BaseException) -> Case:
    """Handle a case result from asyncio.gather with return_exceptions=True.

        Parameters
        ----------
    case_result : Case | BaseException
        The case result from asyncio.gather

    Returns
    -------
    Case
        The case if valid

    Raises
    ------
    BaseException
        If the result is an exception
    TypeError
        If the result is not a Case
    """
    return handle_gather_result(case_result, Case)
