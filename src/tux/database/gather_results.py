"""Helpers for asyncio gather results that involve ORM models."""

from tux.database.models import Case
from tux.shared.asyncio_gather import handle_gather_result

__all__ = ["handle_case_result"]


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
    """
    return handle_gather_result(case_result, Case)
