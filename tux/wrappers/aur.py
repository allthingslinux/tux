import httpx
from loguru import logger
from pydantic import BaseModel, Field, RootModel


class BaseResult(BaseModel):
    resultcount: int
    type: str
    version: int


class PackageBasic(BaseModel):
    ID: int
    Name: str | None = None
    Description: str | None = None
    PackageBaseID: int | None = None
    PackageBase: str | None = None
    Maintainer: str | None = None
    NumVotes: int | None = None
    Popularity: float | None = None
    FirstSubmitted: int | None = None
    LastModified: int | None = None
    OutOfDate: int | None = None
    Version: str | None = None
    URLPath: str | None = None
    URL: str | None = None


class PackageDetailed(PackageBasic):
    Submitter: str | None = None
    License: list[str] = Field(default_factory=list)
    Depends: list[str] = Field(default_factory=list)
    MakeDepends: list[str] = Field(default_factory=list)
    OptDepends: list[str] = Field(default_factory=list)
    CheckDepends: list[str] = Field(default_factory=list)
    Provides: list[str] = Field(default_factory=list)
    Conflicts: list[str] = Field(default_factory=list)
    Replaces: list[str] = Field(default_factory=list)
    Groups: list[str] = Field(default_factory=list)
    Keywords: list[str] = Field(default_factory=list)
    CoMaintainers: list[str] = Field(default_factory=list)


class SearchResult(BaseResult):
    results: list[PackageBasic]


class InfoResult(BaseResult):
    results: list[PackageDetailed]


class ErrorResult(BaseResult):
    error: str
    results: list[dict[str, str]] = Field(default_factory=list)


class PackageNames(RootModel[list[str]]):
    @classmethod
    def from_list(cls, lst: list[str]):
        return cls(root=lst)


class AURClient:
    BASE_URL = "https://aur.archlinux.org"

    @staticmethod
    async def search(term: str, search_by: str = "name-desc") -> SearchResult | ErrorResult:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AURClient.BASE_URL}/rpc/v5/search",
                params={"v": "5", "arg": term, "by": search_by},
            )
            if response.status_code == 200:
                response_data = response.json()
                logger.debug(f"Received search response: {response_data}")
                if response_data.get("type") == "error":
                    return ErrorResult(**response_data)
                return SearchResult(**response_data)
            return ErrorResult(type="error", error="Failed to connect", resultcount=0, version=5)

    @staticmethod
    async def get_package_info(pkg_name: str) -> InfoResult | ErrorResult:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AURClient.BASE_URL}/rpc/v5/info", params={"v": "5", "arg[]": pkg_name})
            if response.status_code == 200:
                response_data = response.json()
                logger.debug(f"Received package info response: {response_data}")
                try:
                    if response_data.get("type") == "error":
                        return ErrorResult(**response_data)
                    return InfoResult(**response_data)
                except Exception as e:
                    logger.error(f"Error parsing InfoResult: {e} - Response: {response_data}")
                    raise
            return ErrorResult(type="error", error="Failed to connect", resultcount=0, version=5)

    @staticmethod
    async def get_packages_info(pkg_names: list[str]) -> InfoResult | ErrorResult:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AURClient.BASE_URL}/rpc/v5/info", params={"v": "5", "arg[]": pkg_names})
            if response.status_code == 200:
                response_data = response.json()
                logger.debug(f"Received packages info response: {response_data}")
                try:
                    if response_data.get("type") == "error":
                        return ErrorResult(**response_data)
                    return InfoResult(**response_data)
                except Exception as e:
                    logger.error(f"Error parsing InfoResult: {e} - Response: {response_data}")
                    raise
            return ErrorResult(type="error", error="Failed to connect", resultcount=0, version=5)

    @staticmethod
    async def suggest_packages(term: str) -> PackageNames:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AURClient.BASE_URL}/rpc/v5/suggest", params={"v": "5", "arg": term})
            response_json = response.json()
            logger.debug(f"Received suggest packages response: {response_json}")
            return PackageNames.from_list(response_json)

    @staticmethod
    async def suggest_package_bases(term: str) -> PackageNames:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AURClient.BASE_URL}/rpc/v5/suggest-pkgbase", params={"v": "5", "arg": term})
            response_json = response.json()
            logger.debug(f"Received suggest package bases response: {response_json}")
            return PackageNames.from_list(response_json)
