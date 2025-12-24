"""
Wandbox API Wrapper for Tux Bot.

This module provides integration with the Wandbox online compiler API,
allowing code execution and compilation for various programming languages
within the Tux Discord bot.
"""

from typing import Any

import httpx

from tux.services.http_client import http_client
from tux.shared.exceptions import (
    TuxAPIConnectionError,
    TuxAPIRequestError,
    TuxAPIResourceNotFoundError,
)

url = "https://wandbox.org/api/compile.json"


async def getoutput(
    code: str,
    compiler: str,
    options: str | None,
) -> dict[str, Any]:
    """
    Compile and execute code using a specified compiler and return the output.

    Parameters
    ----------
    code : str
        The source code to be compiled and executed.
    compiler : str
        The identifier or name of the compiler to use.
    options : str or None
        Additional compiler options or flags. If None, an empty string is used.

    Returns
    -------
    dict[str, Any]
        A dictionary containing the compiler output if the request is successful.

    Raises
    ------
    TuxAPIConnectionError
        If connection/request fails or times out.
    TuxAPIRequestError
        If HTTP request fails with non-404 status code.
    TuxAPIResourceNotFoundError
        If compiler is not found (404).
    """
    copt = options if options is not None else ""
    headers = {
        "Content-Type": "application/json",
    }
    payload = {"compiler": compiler, "code": code, "options": copt}

    try:
        response = await http_client.post(
            url,
            json=payload,
            headers=headers,
            timeout=15.0,
        )
        response.raise_for_status()
    except httpx.ReadTimeout as e:
        raise TuxAPIConnectionError(service_name="Wandbox", original_error=e) from e
    except httpx.RequestError as e:
        raise TuxAPIConnectionError(service_name="Wandbox", original_error=e) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise TuxAPIResourceNotFoundError(
                service_name="Wandbox",
                resource_identifier=compiler,
            ) from e
        raise TuxAPIRequestError(
            service_name="Wandbox",
            status_code=e.response.status_code,
            reason=e.response.text,
        ) from e
    else:
        return response.json()
