from typing import Any

import httpx

client = httpx.Client(timeout=15)
url = "https://wandbox.org/api/compile.json"


def getoutput(code: str, compiler: str, options: str | None) -> dict[str, Any] | None:
    copt = options if options is not None else ""

    payload = {"compiler": compiler, "code": code, options: copt}

    uri = client.post(url, json=payload)

    try:
        return uri.json() if uri.status_code == httpx.codes.OK else None
    except httpx.ReadTimeout:
        return None
