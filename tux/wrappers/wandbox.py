from typing import Any

import httpx

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

    payload = {"compiler": compiler, "code": code, "options": copt}

    try:
        uri = client.post(url, json=payload)
        uri.raise_for_status()
    except httpx.ReadTimeout:
        return None
    else:
        return uri.json() if uri.status_code == httpx.codes.OK else None
