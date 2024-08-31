from typing import Any

import httpx
from repology_client import exceptions as repology_exceptions
from repology_client.types import Package, ResolvePackageType


class RepologyWrapper:
    BASE_API_V1_URL = "https://repology.org/api/v1"
    TOOL_PROJECT_BY_URL = "https://repology.org/tools/project-by"
    API_EXP_URL = "https://repology.org/api/experimental"

    def __init__(self):
        pass

    async def get_packages(self, project: str) -> set[Package]:
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.BASE_API_V1_URL}/project/{project}"
                response: httpx.Response = await client.get(url)
                response.raise_for_status()
                json_data = response.json()
                if not json_data:
                    self._raise_empty_response_error("Empty response from get_packages")
                return {Package(**pkg) for pkg in json_data}
            except httpx.HTTPStatusError as e:
                raise repology_exceptions.InvalidInput(str(e)) from e
            except Exception as e:
                raise repology_exceptions.InvalidInput(str(e)) from e

    async def get_projects(
        self,
        start: str = "",
        end: str = "",
        count: int = 200,
        *,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, set[Package]]:
        async with httpx.AsyncClient() as client:
            try:
                params = {"start": start, "end": end, "count": count}
                if filters:
                    params |= filters
                url = f"{self.BASE_API_V1_URL}/projects/"
                response: httpx.Response = await client.get(url, params=params)
                response.raise_for_status()
                json_data = response.json()
                if not json_data:
                    self._raise_empty_response_error("Empty response from get_projects")
                return {project: {Package(**pkg) for pkg in pkgs} for project, pkgs in json_data.items()}
            except httpx.HTTPStatusError as e:
                raise repology_exceptions.InvalidInput(str(e)) from e
            except Exception as e:
                raise repology_exceptions.InvalidInput(str(e)) from e

    async def resolve_package(
        self,
        repo: str,
        name: str,
        name_type: ResolvePackageType = ResolvePackageType.SOURCE,
        *,
        autoresolve: bool = True,
    ) -> set[Package]:
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.TOOL_PROJECT_BY_URL}/{repo}/{name_type.value}/{name}"
                response: httpx.Response = await client.get(url)
                response.raise_for_status()
                json_data = response.json()
                if not json_data:
                    self._raise_empty_response_error(f"Empty response from resolve_package for {repo}:{name}")
                if isinstance(json_data, list) and not autoresolve:
                    self._raise_invalid_input_error(f"Multiple packages found for {repo}:{name}")
                return {Package(**pkg) for pkg in json_data}  # type: ignore
            except httpx.HTTPStatusError as e:
                raise repology_exceptions.InvalidInput(str(e)) from e
            except Exception as e:
                raise repology_exceptions.InvalidInput(str(e)) from e

    async def get_distromap(self, fromrepo: str, torepo: str) -> Any:
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.API_EXP_URL}/distromap/{fromrepo}/{torepo}"
                response: httpx.Response = await client.get(url)
                response.raise_for_status()
                if json_data := response.json():
                    return json_data
                self._raise_empty_response_error("Empty response from get_distromap")
            except httpx.HTTPStatusError as e:
                raise repology_exceptions.InvalidInput(str(e)) from e
            except Exception as e:
                raise repology_exceptions.InvalidInput(str(e)) from e

    def _raise_empty_response_error(self, message: str):
        raise repology_exceptions.EmptyResponse(message)

    def _raise_invalid_input_error(self, message: str):
        raise repology_exceptions.InvalidInput(message)
