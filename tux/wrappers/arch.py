from typing import Any

import httpx
from loguru import logger
from pydantic import BaseModel


class Package(BaseModel):
    pkgname: str
    pkgbase: str
    repo: str
    arch: str
    pkgver: str
    pkgrel: str
    epoch: int
    pkgdesc: str
    url: str | None
    filename: str
    compressed_size: int
    installed_size: int
    build_date: str
    last_update: str
    flag_date: str | None
    maintainers: list[str]
    packager: str | None
    groups: list[str]
    licenses: list[str]
    conflicts: list[str]
    provides: list[str]
    replaces: list[str]
    depends: list[str]
    optdepends: list[str]
    makedepends: list[str]
    checkdepends: list[str]


class SearchResult(BaseModel):
    version: int
    limit: int
    valid: bool
    results: list[Package]
    num_pages: int | None = None
    page: int | None = None


class ArchRepoClient:
    BASE_URL = "https://archlinux.org"

    @staticmethod
    async def get_arch_pkg_details(term: str, arch: str = "x86_64") -> dict[str, Any] | None:
        try:
            pkg_search_result = await ArchRepoClient.search_package(term, arch)
            if not pkg_search_result:
                pkg_search_result = await ArchRepoClient.search_package(term, "any")
                if not pkg_search_result:
                    return None
                arch = "any"

            repo_name = pkg_search_result.repo
            pkg_result = await ArchRepoClient.get_package_details(repo_name, arch, term)
            return pkg_result.model_dump()
        except Exception as e:
            logger.error(e)
            return None

    @staticmethod
    async def get_package_details(repo: str, arch: str, package: str) -> Package:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ArchRepoClient.BASE_URL}/packages/{repo}/{arch}/{package}/json/")
            logger.debug(f"Received package details response: {response.json()}")
            response.raise_for_status()
            return Package(**response.json())

    @staticmethod
    async def search_package(term: str, arch: str = "x86_64") -> Package | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ArchRepoClient.BASE_URL}/packages/search/json/",
                params={"name": term, "arch": arch},
            )
            logger.debug(f"Received search response: {response.json()}")
            response.raise_for_status()
            search_result = SearchResult(**response.json())
            logger.debug(f"Search result: {search_result}")
            return search_result.results[0] if search_result.results else None

    @staticmethod
    async def get_package_files(repo: str, arch: str, package: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ArchRepoClient.BASE_URL}/packages/{repo}/{arch}/{package}/files/json/")
            logger.debug(f"Received package files response: {response.json()}")
            response.raise_for_status()
            return response.json()
