"""
Godbolt API Wrapper for Tux Bot.

This module provides integration with the Godbolt API allowing code execution and compilation for various programming languages.
"""

from typing import TypedDict

import httpx

from tux.services.http_client import http_client
from tux.shared.constants import HTTP_NOT_FOUND, HTTP_OK
from tux.shared.exceptions import (
    TuxAPIConnectionError,
    TuxAPIRequestError,
    TuxAPIResourceNotFoundError,
)


class CompilerFilters(TypedDict):
    """
    Compiler filters.

    Parameters
    ----------
    TypedDict : Compiler filters.
        Dictionary of compiler filters.
    """

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
    """
    Compiler options.

    Parameters
    ----------
    TypedDict : Compiler options.
        Dictionary of compiler options.
    """

    skipAsm: bool
    executorRequest: bool


class Options(TypedDict):
    """
    Godbolt API options.

    Parameters
    ----------
    TypedDict : Options.
        Dictionary of options.
    """

    userArguments: str
    compilerOptions: CompilerOptions
    filters: CompilerFilters
    tools: list[str]
    libraries: list[str]


class Payload(TypedDict):
    """
    Payload for the Godbolt API.

    Parameters
    ----------
    TypedDict : Payload.
        Dictionary of payload.
    """

    source: str
    options: Options
    lang: str
    allowStoreCodeDebug: bool


url = "https://godbolt.org"


async def checkresponse(res: httpx.Response) -> str | None:
    """
    Check the response from the Godbolt API.

    Parameters
    ----------
    res : httpx.Response
        The response from the Godbolt API.

    Returns
    -------
    str | None
        The response from the Godbolt API if successful, otherwise None.
    """
    try:
        return res.text if res.status_code == HTTP_OK else None
    except httpx.ReadTimeout:
        return None
    except httpx.RequestError as e:
        raise TuxAPIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == HTTP_NOT_FOUND:
            raise TuxAPIResourceNotFoundError(service_name="Godbolt", resource_identifier=str(e.request.url)) from e
        raise TuxAPIRequestError(
            service_name="Godbolt",
            status_code=e.response.status_code,
            reason=e.response.text,
        ) from e


async def sendresponse(url: str) -> str | None:
    """
    Send the response from the Godbolt API.

    Parameters
    ----------
    url : str
        The URL to send the response from.

    Returns
    -------
    str | None
        The response from the Godbolt API if successful, otherwise None.
    """
    try:
        response = await http_client.get(url, timeout=15.0)
        response.raise_for_status()
    except httpx.ReadTimeout:
        return None
    except httpx.RequestError as e:
        raise TuxAPIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == HTTP_NOT_FOUND:
            raise TuxAPIResourceNotFoundError(service_name="Godbolt", resource_identifier=url) from e
        raise TuxAPIRequestError(
            service_name="Godbolt",
            status_code=e.response.status_code,
            reason=e.response.text,
        ) from e
    else:
        return response.text if response.status_code == HTTP_OK else None


async def getlanguages() -> str | None:
    """
    Get the languages from the Godbolt API.

    Returns
    -------
    str | None
        The languages from the Godbolt API if successful, otherwise None.
    """
    url_lang = f"{url}/api/languages"
    return await sendresponse(url_lang)


async def getcompilers() -> str | None:
    """
    Get the compilers from the Godbolt API.

    Returns
    -------
    str | None
        The compilers from the Godbolt API if successful, otherwise None.
    """
    url_comp = f"{url}/api/compilers"
    return await sendresponse(url_comp)


async def getspecificcompiler(lang: str) -> str | None:
    """
    Get a specific compiler from the Godbolt API.

    Parameters
    ----------
    lang : str
        The language to get the specific compiler for.

    Returns
    -------
    str | None
        The specific compiler from the Godbolt API if successful, otherwise None.
    """
    url_comp = f"{url}/api/compilers/{lang}"
    return await sendresponse(url_comp)


async def getoutput(code: str, lang: str, compileroptions: str | None = None) -> str | None:
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
    str | None
        The output of the code if successful, otherwise None.

    Raises
    ------
    httpx.ReadTimeout
        If the request times out.
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
        uri = await http_client.post(url_comp, json=payload, timeout=15.0)

    except httpx.ReadTimeout as e:
        raise TuxAPIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.RequestError as e:
        raise TuxAPIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == HTTP_NOT_FOUND:
            raise TuxAPIResourceNotFoundError(service_name="Godbolt", resource_identifier=lang) from e
        raise TuxAPIRequestError(
            service_name="Godbolt",
            status_code=e.response.status_code,
            reason=e.response.text,
        ) from e
    else:
        return uri.text if uri.status_code == 200 else None


async def generateasm(code: str, lang: str, compileroptions: str | None = None) -> str | None:
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
    str | None
        The assembly code if successful, otherwise None.

    Raises
    ------
    httpx.ReadTimeout
        If the request times out.
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
        uri = await http_client.post(url_comp, json=payload, timeout=15.0)

    except httpx.ReadTimeout as e:
        raise TuxAPIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.RequestError as e:
        raise TuxAPIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == HTTP_NOT_FOUND:
            raise TuxAPIResourceNotFoundError(service_name="Godbolt", resource_identifier=lang) from e
        raise TuxAPIRequestError(
            service_name="Godbolt",
            status_code=e.response.status_code,
            reason=e.response.text,
        ) from e
    else:
        return uri.text if uri.status_code == 200 else None
