from typing import TypedDict

import httpx

from core.utils.exceptions import (
    APIConnectionError,
    APIRequestError,
    APIResourceNotFoundError,
)


class CompilerFilters(TypedDict):
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
    skipAsm: bool
    executorRequest: bool


class Options(TypedDict):
    userArguments: str
    compilerOptions: CompilerOptions
    filters: CompilerFilters
    tools: list[str]
    libraries: list[str]


class Payload(TypedDict):
    source: str
    options: Options
    lang: str
    allowStoreCodeDebug: bool


client = httpx.Client(timeout=15)
url = "https://godbolt.org"


def checkresponse(res: httpx.Response) -> str | None:
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
        return res.text if res.status_code == 200 else None
    except httpx.ReadTimeout:
        return None
    except httpx.RequestError as e:
        raise APIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise APIResourceNotFoundError(service_name="Godbolt", resource_identifier=str(e.request.url)) from e
        raise APIRequestError(service_name="Godbolt", status_code=e.response.status_code, reason=e.response.text) from e


def sendresponse(url: str) -> str | None:
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
        response = client.get(url)
        response.raise_for_status()
    except httpx.ReadTimeout:
        return None
    except httpx.RequestError as e:
        raise APIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise APIResourceNotFoundError(service_name="Godbolt", resource_identifier=url) from e
        raise APIRequestError(service_name="Godbolt", status_code=e.response.status_code, reason=e.response.text) from e
    else:
        return response.text if response.status_code == 200 else None


def getlanguages() -> str | None:
    """
    Get the languages from the Godbolt API.

    Returns
    -------
    str | None
        The languages from the Godbolt API if successful, otherwise None.
    """
    url_lang = f"{url}/api/languages"
    return sendresponse(url_lang)


def getcompilers() -> str | None:
    """
    Get the compilers from the Godbolt API.

    Returns
    -------
    str | None
        The compilers from the Godbolt API if successful, otherwise None.
    """

    url_comp = f"{url}/api/compilers"
    return sendresponse(url_comp)


def getspecificcompiler(lang: str) -> str | None:
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
    return sendresponse(url_comp)


def getoutput(code: str, lang: str, compileroptions: str | None = None) -> str | None:
    """
    This function sends a POST request to the Godbolt API to get the output of the given code.

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
    uri = client.post(url_comp, json=payload)

    try:
        return uri.text if uri.status_code == 200 else None

    except httpx.ReadTimeout as e:
        raise APIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.RequestError as e:
        raise APIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise APIResourceNotFoundError(service_name="Godbolt", resource_identifier=lang) from e
        raise APIRequestError(service_name="Godbolt", status_code=e.response.status_code, reason=e.response.text) from e


def generateasm(code: str, lang: str, compileroptions: str | None = None) -> str | None:
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

    uri = client.post(url_comp, json=payload)

    try:
        return uri.text if uri.status_code == 200 else None

    except httpx.ReadTimeout as e:
        raise APIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.RequestError as e:
        raise APIConnectionError(service_name="Godbolt", original_error=e) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise APIResourceNotFoundError(service_name="Godbolt", resource_identifier=lang) from e
        raise APIRequestError(service_name="Godbolt", status_code=e.response.status_code, reason=e.response.text) from e
