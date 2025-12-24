"""
Godbolt API Wrapper for Tux Bot.

This module provides integration with the Godbolt API allowing code execution and compilation for various programming languages.
"""

from typing import TypedDict

import httpx

from tux.services.http_client import http_client
from tux.shared.constants import HTTP_NOT_FOUND
from tux.shared.exceptions import (
    TuxAPIConnectionError,
    TuxAPIRequestError,
    TuxAPIResourceNotFoundError,
)


class CompilerFilters(TypedDict):
    """Compiler filter options for Godbolt API."""

    binary: bool
    binaryObject: bool
    commentOnly: bool
    demangle: bool
    directives: bool
    execute: bool
    intel: bool
    labels: bool
    libraryCode: bool
    trim: bool
    debugCalls: bool


class CompilerOptions(TypedDict):
    """Compiler options for Godbolt API."""

    skipAsm: bool
    executorRequest: bool


class Options(TypedDict):
    """Godbolt API request options."""

    userArguments: str
    compilerOptions: CompilerOptions
    filters: CompilerFilters
    tools: list[str]
    libraries: list[str]


class Payload(TypedDict):
    """Payload structure for Godbolt API compilation requests."""

    source: str
    options: Options
    lang: str
    allowStoreCodeDebug: bool


url = "https://godbolt.org"


async def sendresponse(url: str) -> str:
    """
    Send a GET request to the Godbolt API and return the response text.

    Parameters
    ----------
    url : str
        The URL to send the request to.

    Returns
    -------
    str
        The response text if successful.

    Raises
    ------
    TuxAPIConnectionError
        If connection to Godbolt API fails or times out.
    TuxAPIRequestError
        If the API request fails with non-404 status code.
    TuxAPIResourceNotFoundError
        If the resource is not found (404).
    """
    try:
        response = await http_client.get(url, timeout=15.0)
        response.raise_for_status()
    except httpx.ReadTimeout as e:
        raise TuxAPIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.RequestError as e:
        raise TuxAPIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == HTTP_NOT_FOUND:
            raise TuxAPIResourceNotFoundError(
                service_name="Godbolt",
                resource_identifier=url,
            ) from e
        raise TuxAPIRequestError(
            service_name="Godbolt",
            status_code=e.response.status_code,
            reason=e.response.text,
        ) from e
    else:
        return response.text


async def getlanguages() -> str:
    """
    Get the languages from the Godbolt API.

    Returns
    -------
    str
        The languages from the Godbolt API if successful.

    Raises
    ------
    TuxAPIConnectionError
        If connection to Godbolt API fails or times out.
    TuxAPIRequestError
        If the API request fails with non-404 status code.
    TuxAPIResourceNotFoundError
        If the resource is not found (404).
    """
    url_lang = f"{url}/api/languages"
    return await sendresponse(url_lang)


async def getcompilers() -> str:
    """
    Get the compilers from the Godbolt API.

    Returns
    -------
    str
        The compilers from the Godbolt API if successful.

    Raises
    ------
    TuxAPIConnectionError
        If connection to Godbolt API fails or times out.
    TuxAPIRequestError
        If the API request fails with non-404 status code.
    TuxAPIResourceNotFoundError
        If the resource is not found (404).
    """
    url_comp = f"{url}/api/compilers"
    return await sendresponse(url_comp)


async def getspecificcompiler(lang: str) -> str:
    """
    Get a specific compiler from the Godbolt API.

    Parameters
    ----------
    lang : str
        The language to get the specific compiler for.

    Returns
    -------
    str
        The specific compiler from the Godbolt API if successful.

    Raises
    ------
    TuxAPIConnectionError
        If connection to Godbolt API fails or times out.
    TuxAPIRequestError
        If the API request fails with non-404 status code.
    TuxAPIResourceNotFoundError
        If the resource is not found (404).
    """
    url_comp = f"{url}/api/compilers/{lang}"
    return await sendresponse(url_comp)


async def getoutput(
    code: str,
    lang: str,
    compileroptions: str | None = None,
) -> str:
    """
    Send a POST request to the Godbolt API to get the output of the given code.

    Parameters
    ----------
    code : str
        The code to compile.
    lang : str
        The language of the code.
    compileroptions : str | None, optional
        The compiler options, by default None

    Returns
    -------
    str
        The output of the code if successful.

    Raises
    ------
    TuxAPIConnectionError
        If connection to Godbolt API fails.
    TuxAPIRequestError
        If the API request fails.
    TuxAPIResourceNotFoundError
        If the resource is not found.
    """
    url_comp = f"{url}/api/compiler/{lang}/compile"

    copt = compileroptions if compileroptions is not None else ""

    payload: Payload = {
        "source": code,
        "options": {
            "userArguments": copt,
            "compilerOptions": {"skipAsm": True, "executorRequest": False},
            "filters": {
                "binary": False,
                "binaryObject": False,
                "commentOnly": True,
                "demangle": True,
                "directives": True,
                "execute": True,
                "intel": True,
                "labels": True,
                "libraryCode": True,
                "trim": True,
                "debugCalls": True,
            },
            "tools": [],
            "libraries": [],
        },
        "lang": f"{lang}",
        "allowStoreCodeDebug": True,
    }

    try:
        response = await http_client.post(url_comp, json=payload, timeout=15.0)
        response.raise_for_status()
    except httpx.ReadTimeout as e:
        raise TuxAPIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.RequestError as e:
        raise TuxAPIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == HTTP_NOT_FOUND:
            raise TuxAPIResourceNotFoundError(
                service_name="Godbolt",
                resource_identifier=lang,
            ) from e
        raise TuxAPIRequestError(
            service_name="Godbolt",
            status_code=e.response.status_code,
            reason=e.response.text,
        ) from e
    else:
        return response.text


async def generateasm(
    code: str,
    lang: str,
    compileroptions: str | None = None,
) -> str:
    """
    Generate assembly code from the given code.

    Parameters
    ----------
    code : str
        The code to generate assembly from.
    lang : str
        The language of the code.
    compileroptions : str | None, optional
        The compiler options, by default None

    Returns
    -------
    str
        The assembly code if successful.

    Raises
    ------
    TuxAPIConnectionError
        If connection to Godbolt API fails.
    TuxAPIRequestError
        If the API request fails.
    TuxAPIResourceNotFoundError
        If the resource is not found.
    """
    url_comp = f"{url}/api/compiler/{lang}/compile"

    copt = compileroptions if compileroptions is not None else ""

    payload: Payload = {
        "source": code,
        "options": {
            "userArguments": copt,
            "compilerOptions": {"skipAsm": False, "executorRequest": False},
            "filters": {
                "binary": False,
                "binaryObject": False,
                "commentOnly": True,
                "demangle": True,
                "directives": True,
                "execute": False,
                "intel": True,
                "labels": True,
                "libraryCode": True,
                "trim": True,
                "debugCalls": True,
            },
            "tools": [],
            "libraries": [],
        },
        "lang": f"{lang}",
        "allowStoreCodeDebug": True,
    }

    try:
        response = await http_client.post(url_comp, json=payload, timeout=15.0)
        response.raise_for_status()
    except httpx.ReadTimeout as e:
        raise TuxAPIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.RequestError as e:
        raise TuxAPIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == HTTP_NOT_FOUND:
            raise TuxAPIResourceNotFoundError(
                service_name="Godbolt",
                resource_identifier=lang,
            ) from e
        raise TuxAPIRequestError(
            service_name="Godbolt",
            status_code=e.response.status_code,
            reason=e.response.text,
        ) from e
    else:
        return response.text
