from typing import Any

import httpx

from core.utils.exceptions import (
    APIConnectionError,
    APIRequestError,
    APIResourceNotFoundError,
)

client = httpx.Client(timeout=15)
url = "https://wandbox.org/api/compile.json"


def getoutput(code: str, compiler: str, options: str | None) -> dict[str, Any] | None:
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
    dict[str, Any] or None
        A dictionary containing the compiler output if the request is successful,
        otherwise `None`. Returns `None` on HTTP errors or read timeout.
    """

    copt = options if options is not None else ""
    headers = {
        "Content-Type": "application/json",
    }
    payload = {"compiler": compiler, "code": code, "options": copt}

    try:
        uri = client.post(url, json=payload, headers=headers)
        uri.raise_for_status()
    except httpx.ReadTimeout as e:
        # Changed to raise APIConnectionError for timeouts
        raise APIConnectionError(service_name="Wandbox", original_error=e) from e
    except httpx.RequestError as e:
        # General connection/request error
        raise APIConnectionError(service_name="Wandbox", original_error=e) from e
    except httpx.HTTPStatusError as e:
        # Specific HTTP status errors
        if e.response.status_code == 404:
            raise APIResourceNotFoundError(
                service_name="Wandbox",
                resource_identifier=compiler,
            ) from e  # Using compiler as resource identifier
        raise APIRequestError(service_name="Wandbox", status_code=e.response.status_code, reason=e.response.text) from e
    else:
        return uri.json() if uri.status_code == 200 else None
