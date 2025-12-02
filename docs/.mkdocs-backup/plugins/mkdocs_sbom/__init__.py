"""MkDocs plugin for generating Software Bill of Materials (SBOM).

This plugin generates license information for project dependencies using licensecheck.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import tomli
from mkdocs.config import Config as MkDocsConfig
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.utils import log

if TYPE_CHECKING:
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page


class SbomPluginConfig(config_options.Config):  # type: ignore[misc]
    """Configuration options for the SBOM plugin."""

    requirements_path = config_options.Type(str, default=".")
    groups = config_options.ListOfItems(config_options.Type(str), default=[])


class SbomPlugin(BasePlugin[SbomPluginConfig]):
    """MkDocs plugin for generating SBOM/license information."""

    def on_page_markdown(
        self,
        markdown: str,
        /,
        *,
        page: Page,
        config: MkDocsConfig,
        files: Files,
    ) -> str:
        """Process markdown to replace ::sbom blocks with license information.

        Parameters
        ----------
        markdown : str
            The markdown content.
        page : Page
            The MkDocs page object.
        config : MkDocsConfig
            The MkDocs configuration.
        files : Files
            The MkDocs files collection.

        Returns
        -------
        str
            The processed markdown with SBOM blocks replaced.
        """
        pattern = r"::sbom\s*\n((?:\s*[\w-]+:\s*.+\s*\n)*)"

        def replace_block(match: re.Match[str]) -> str:
            """Replace a single ::sbom block with license information.

            Parameters
            ----------
            match : re.Match[str]
                The regex match object for the SBOM block.

            Returns
            -------
            str
                The generated SBOM markdown.
            """
            params: dict[str, str] = {}
            param_lines = match.group(1).strip().split("\n")
            for line in param_lines:
                if ":" in line and line.strip():
                    key, value = line.split(":", 1)
                    params[key.strip()] = value.strip()

            base_indent = int(params.get("base_indent", "2"))
            groups = params.get("groups", "").split(",") if params.get("groups") else []
            groups = [g.strip() for g in groups if g.strip()]

            # Get requirements path relative to docs directory
            docs_dir = Path(config["docs_dir"])  # type: ignore[index]
            try:
                req_path_str: str = self.config["requirements_path"]  # type: ignore[index]
            except (KeyError, TypeError):
                req_path_str = ".."
            req_path = Path(req_path_str)  # type: ignore[arg-type]
            if not req_path.is_absolute():
                req_path = docs_dir.parent / req_path

            # Use groups from params, or fall back to config, or empty list
            try:
                config_groups: list[str] = self.config["groups"]  # type: ignore[index]
            except (KeyError, TypeError):
                config_groups = []
            final_groups: list[str] = groups or config_groups  # type: ignore[assignment]

            return self._generate_sbom_markdown(
                base_indent=base_indent,
                groups=final_groups,  # type: ignore[arg-type]
                requirements_path=req_path,
            )

        return re.sub(pattern, replace_block, markdown, flags=re.MULTILINE)

    def _generate_sbom_markdown(
        self,
        base_indent: int,
        groups: list[str],
        requirements_path: Path,
    ) -> str:
        """Generate markdown for SBOM.

        Parameters
        ----------
        base_indent : int
            Base indentation level for the output.
        groups : list[str]
            Dependency groups to include (e.g., ['dev', 'test']).
        requirements_path : Path
            Path to the directory containing pyproject.toml.

        Returns
        -------
        str
            Generated markdown for the SBOM.
        """
        indent = " " * base_indent

        try:
            # Get packages grouped by source (main vs groups)
            packages_by_source = self._get_packages_by_source(requirements_path, groups)

            if not packages_by_source:
                return f"{indent}*No dependencies found.*\n"

            lines: list[str] = []

            # Helper function to create a table from packages
            def create_table(
                packages: list[dict[str, str | list[str]]],
                title: str | None = None,
            ) -> list[str]:
                """Create a markdown table from a list of packages."""
                table_lines: list[str] = []

                if title:
                    table_lines.append(f"### {title}")
                    table_lines.append("")

                if not packages:
                    table_lines.append(f"{indent}*No packages in this group.*")
                    table_lines.append(f"{indent}")
                    return table_lines

                # Table header
                table_lines.append(f"{indent}| Package | Licenses | Version | Author |")
                table_lines.append(f"{indent}|---------|----------|---------|--------|")

                # Table rows
                for package in sorted(
                    packages,
                    key=lambda p: str(p.get("name", "")).lower(),
                ):
                    name = str(package.get("name") or "Unknown Package")
                    version = str(package.get("version") or "Unknown Version")
                    licenses = package.get("licenses", [])
                    if isinstance(licenses, str):
                        licenses = [licenses]
                    author = str(package.get("author", "")).strip()
                    homepage = str(package.get("homePage", "")).strip()

                    # Format licenses
                    license_str = (
                        ", ".join(f"`{lic}`" for lic in licenses)
                        if licenses
                        else "*License Unknown*"
                    )

                    # Format package name with optional link
                    if homepage and homepage.strip() and homepage.upper() != "UNKNOWN":
                        name_cell = f"[{name}]({homepage})"
                    else:
                        name_cell = name

                    # Format author (handle unknown/empty)
                    author_cell = (
                        author
                        if author and author.lower() not in ("unknown", "n/a", "")
                        else "—"
                    )

                    # Escape pipe characters in cells
                    name_cell = name_cell.replace("|", "\\|")
                    license_str = license_str.replace("|", "\\|")
                    version = version.replace("|", "\\|")
                    author_cell = author_cell.replace("|", "\\|")

                    table_lines.append(
                        f"{indent}| {name_cell} | {license_str} | {version} | {author_cell} |",
                    )

                table_lines.append(f"{indent}")
                return table_lines

            # Create table for main dependencies
            if packages_by_source.get("main"):
                lines.extend(
                    create_table(packages_by_source["main"], "Main Dependencies"),
                )

            # Create tables for each group
            for group in groups:
                if packages_by_source.get(group):
                    group_title = f"{group.capitalize()} Dependencies"
                    lines.extend(create_table(packages_by_source[group], group_title))

            return "\n".join(lines)

        except Exception as e:
            return f"{indent}<!-- Error generating SBOM: {e} -->\n"

    def _get_direct_dependencies(self, pyproject_path: Path) -> dict[str, set[str]]:
        """Extract direct dependencies from pyproject.toml.

        Parameters
        ----------
        pyproject_path : Path
            Path to pyproject.toml file.

        Returns
        -------
        dict[str, set[str]]
            Dictionary mapping source names ("main" or group names) to sets of package names.
        """
        direct_deps: dict[str, set[str]] = {}

        try:
            with pyproject_path.open("rb") as f:
                data = tomli.load(f)

            # Get main dependencies
            project_deps = data.get("project", {}).get("dependencies", [])
            main_packages: set[str] = set()
            for dep in project_deps:
                # Extract package name (handle extras like "package[extra]")
                # Remove version specifiers and extras
                name = re.split(r"[\[<>=!]", dep)[0].strip().lower()
                main_packages.add(name)
            if main_packages:
                direct_deps["main"] = main_packages

            # Get group dependencies
            dependency_groups = data.get("dependency-groups", {})
            for group_name, group_deps in dependency_groups.items():
                group_packages: set[str] = set()
                for dep in group_deps:
                    # Extract package name (handle extras and version specifiers)
                    name = re.split(r"[\[<>=!]", dep)[0].strip().lower()
                    group_packages.add(name)
                if group_packages:
                    direct_deps[group_name] = group_packages

        except Exception as e:
            log.warning(f"Failed to parse pyproject.toml: {e}")

        return direct_deps

    def _get_packages_by_source(
        self,
        requirements_path: Path,
        groups: list[str],
    ) -> dict[str, list[dict[str, str | list[str]]]]:
        """Get package information grouped by source (main vs groups).

        Only includes direct dependencies, not transitive ones.

        Parameters
        ----------
        requirements_path : Path
            Path to the directory containing pyproject.toml.
        groups : list[str]
            Dependency groups to include.

        Returns
        -------
        dict[str, list[dict[str, str | list[str]]]]
            Dictionary mapping source names ("main" or group names) to lists of packages.
        """
        packages_by_source: dict[str, list[dict[str, str | list[str]]]] = {}
        pyproject_path = requirements_path / "pyproject.toml"

        # Get direct dependencies from pyproject.toml
        direct_deps = self._get_direct_dependencies(pyproject_path)
        main_package_names: set[str] = direct_deps.get("main", set())

        # Helper function to get packages from licensecheck and filter to direct deps
        def get_filtered_packages(
            direct_dep_names: set[str],
            cmd: list[str],
        ) -> list[dict[str, str | list[str]]]:
            """Get packages from licensecheck and filter to only direct dependencies."""
            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(requirements_path),
                    capture_output=True,
                    text=True,
                    check=True,
                )
                data = json.loads(result.stdout)
                # Create a map of all packages returned by licensecheck
                all_packages_map: dict[str, dict[str, str | list[str]]] = {}
                for pkg in data.get("packages", []):
                    name = pkg.get("name", "")
                    if name:
                        all_packages_map[name.lower()] = {
                            "name": name,
                            "version": pkg.get("version", ""),
                            "licenses": pkg.get("license", "").split(";;")
                            if pkg.get("license")
                            else [],
                            "author": pkg.get("author", ""),
                            "homePage": pkg.get("homePage", ""),
                        }
                # Filter to only direct dependencies
                return [
                    all_packages_map[dep_name]
                    for dep_name in direct_dep_names
                    if dep_name in all_packages_map
                ]
            except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                log.warning(f"Failed to get packages: {e}")
                return []

        # Get main dependencies (direct only)
        main_direct_deps = direct_deps.get("main", set())
        if main_direct_deps:
            cmd_main = [
                "uv",
                "run",
                "python",
                "-m",
                "licensecheck",
                "--format",
                "json",
                "--requirements-paths",
                str(pyproject_path),
            ]
            main_packages = get_filtered_packages(main_direct_deps, cmd_main)
            if main_packages:
                packages_by_source["main"] = main_packages

        # Get group dependencies (direct only, excluding main)
        for group in groups:
            group_direct_deps = direct_deps.get(group, set())
            if group_direct_deps:
                cmd_group = [
                    "uv",
                    "run",
                    "python",
                    "-m",
                    "licensecheck",
                    "--format",
                    "json",
                    "--requirements-paths",
                    str(pyproject_path),
                    "--groups",
                    group,
                ]
                # Get all packages for this group, then filter to direct deps
                group_packages = get_filtered_packages(group_direct_deps, cmd_group)
                # Filter out packages that are also in main
                group_packages_filtered = [
                    pkg
                    for pkg in group_packages
                    if str(pkg.get("name", "")).lower() not in main_package_names
                ]
                if group_packages_filtered:
                    packages_by_source[group] = group_packages_filtered

        return packages_by_source
