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


client = httpx.Client()
url = "https://godbolt.org"


def checkresponse(res: httpx.Response) -> str | None:
    if res.status_code == httpx.codes.OK:
        return res.text
    return None


def getlanguages() -> str | None:
    url_lang = f"{url}/api/languages"
    response = client.get(url_lang)
    return checkresponse(response)


def getcompilers() -> str | None:
    url_comp = f"{url}/api/compilers"
    response = client.get(url_comp)
    return checkresponse(response)


def getspecificcompiler(lang: str) -> str | None:
    url_comp = f"{url}/api/compilers/{lang}"
    response = client.get(url_comp)
    return checkresponse(response)


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
    return checkresponse(uri)


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
    return checkresponse(uri)
