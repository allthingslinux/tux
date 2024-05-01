from typing import TypedDict

import httpx


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


def checkresponse(res: httpx.Response):
    try:
        return res.text if res.status_code == httpx.codes.OK else None
    except httpx.ReadTimeout:
        return None


def sendresponse(url: str) -> str | None:
    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.ReadTimeout:
        return None
    else:
        return response.text if response.status_code == httpx.codes.OK else None


def getlanguages() -> str | None:
    url_lang = f"{url}/api/languages"
    return sendresponse(url_lang)


def getcompilers() -> str | None:
    url_comp = f"{url}/api/compilers"
    return sendresponse(url_comp)


def getspecificcompiler(lang: str) -> str | None:
    url_comp = f"{url}/api/compilers/{lang}"
    return sendresponse(url_comp)


def getoutput(code: str, lang: str, compileroptions: str | None = None) -> str | None:
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
        return uri.text if uri.status_code == httpx.codes.OK else None

    except httpx.ReadTimeout:
        return "Could not get data back from the host in time"


def generateasm(code: str, lang: str, compileroptions: str | None = None) -> str | None:
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
        return uri.text if uri.status_code == httpx.codes.OK else None

    except httpx.ReadTimeout:
        return "Could not get data back from the host in time"
