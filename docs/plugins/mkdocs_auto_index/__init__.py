"""MkDocs plugin for auto-generating index pages from navigation structure.

This plugin automatically generates index page content based on the navigation
structure, creating organized lists of links for section index pages.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mkdocs.config import Config as MkDocsConfig
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

if TYPE_CHECKING:
    from mkdocs.structure.files import Files
    from mkdocs.structure.nav import Navigation
    from mkdocs.structure.pages import Page


class IndexGeneratorConfig(config_options.Config):  # type: ignore[misc]
    """Configuration options for the Index Generator plugin.

    Attributes
    ----------
    enabled : bool
        Whether to enable index page generation. Default is True.
    preserve_above_marker : str
        Marker comment that indicates content above should be preserved.
        Pages containing this marker will have auto-generated content added.
        Content below this marker will be replaced with auto-generated content.
        Default is "<!-- AUTO_INDEX_START -->".
    """

    enabled = config_options.Type(bool, default=True)
    preserve_above_marker = config_options.Type(str, default="<!-- AUTO_INDEX_START -->")


class IndexGeneratorPlugin(BasePlugin[IndexGeneratorConfig]):
    """MkDocs plugin for auto-generating index page content."""

    def __init__(self):
        """Initialize the plugin."""
        super().__init__()
        self.nav: Navigation | None = None

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:  # type: ignore[override]
        """Configure the plugin by adding plugins directory to sys.path.

        Parameters
        ----------
        config : MkDocsConfig
            The MkDocs configuration object.

        Returns
        -------
        MkDocsConfig | None
            The modified configuration object, or None to use original.
        """
        # Add plugins directory to Python path so MkDocs can find local plugins
        plugins_dir = Path(config["docs_dir"]) / "plugins"  # type: ignore[index]
        plugins_parent = plugins_dir.parent
        if str(plugins_parent) not in sys.path:
            sys.path.insert(0, str(plugins_parent))
        return config

    def _find_nav_item(self, nav_items: list[Any], target_url: str) -> Any | None:
        """Find a navigation item by its URL.

        Parameters
        ----------
        nav_items : list[Any]
            List of navigation items to search.
        target_url : str
            URL to find (e.g., "developer/index.html").

        Returns
        -------
        Any | None
            The navigation item if found, None otherwise.
        """
        for item in nav_items:
            if hasattr(item, "url") and item.url == target_url:
                return item
            if (
                hasattr(item, "children")
                and item.children
                and (result := self._find_nav_item(item.children, target_url))
            ):
                return result
        return None

    def _generate_markdown_from_nav(self, nav_item: Any, base_path: str = "", depth: int = 0) -> str:
        """Generate markdown content from a navigation item and its children.

        Parameters
        ----------
        nav_item : Any
            Navigation item (Page or Section) to process.
        base_path : str
            Base path for generating relative links. Default is "".
        depth : int
            Current nesting depth. Default is 0.

        Returns
        -------
        str
            Generated markdown content.
        """
        lines: list[str] = []

        # Process children
        if hasattr(nav_item, "children") and nav_item.children:
            for child in nav_item.children:
                # Skip the index page itself
                if hasattr(child, "url") and child.url.endswith("/index.html"):
                    # Process its children instead
                    if hasattr(child, "children") and child.children:
                        for grandchild in child.children:
                            lines.extend(self._generate_markdown_from_nav(grandchild, base_path, depth).splitlines())
                    continue

                # Get title and URL
                title = getattr(child, "title", "")
                url = getattr(child, "url", "")

                if not title or not url:
                    continue

                # Convert HTML URL to markdown path
                # Remove .html extension and leading slash
                md_path = url.replace(".html", ".md").lstrip("/")
                if md_path.startswith(base_path):
                    md_path = md_path[len(base_path) :].lstrip("/")

                # Generate markdown link
                indent = "  " * depth
                lines.append(f"{indent}- [{title}]({md_path})")

                # Recursively process children
                if hasattr(child, "children") and child.children:
                    lines.extend(self._generate_markdown_from_nav(child, base_path, depth + 1).splitlines())

        return "\n".join(lines)

    def _organize_by_sections(self, nav_item: Any, base_path: str = "") -> str:  # noqa: PLR0912
        # sourcery skip: low-code-quality
        """Organize navigation items into sections with headings.

        Parameters
        ----------
        nav_item : Any
            Navigation item to process.
        base_path : str
            Base path for generating relative links. Default is "".

        Returns
        -------
        str
            Generated markdown content organized by sections.
        """
        lines: list[str] = []

        if not hasattr(nav_item, "children") or not nav_item.children:
            return ""

        # Group children by their parent section
        sections: dict[str, list[Any]] = {}

        for child in nav_item.children:
            # Skip the index page itself
            if hasattr(child, "url") and child.url.endswith("/index.html"):
                # Process its children as top-level items
                if hasattr(child, "children") and child.children:
                    for grandchild in child.children:
                        if section_title := getattr(grandchild, "title", ""):
                            if section_title not in sections:
                                sections[section_title] = []
                            sections[section_title].append(grandchild)
                continue

            # For direct children, use their title as section
            if title := getattr(child, "title", ""):
                if title not in sections:
                    sections[title] = []
                sections[title].append(child)

        # Generate markdown for each section
        for section_title, items in sections.items():
            # Check if this is a section with an index page
            section_url = None
            section_children = []

            # Look for index page first
            for item in items:
                url = getattr(item, "url", "")
                if url.endswith("/index.html"):
                    section_url = url
                    # Get children of the index page
                    if hasattr(item, "children") and item.children:
                        children: list[Any] = list(item.children)
                        section_children.extend(children)  # type: ignore[arg-type]
                    break

            # If no index page found, use direct children
            if not section_url:
                section_children = items

            # Generate section heading with link if it has an index
            if section_url:
                md_path = section_url.replace(".html", ".md").lstrip("/")
                if md_path.startswith(base_path):
                    md_path = md_path[len(base_path) :].lstrip("/")
                lines.append(f"## [{section_title}]({md_path})")
            else:
                lines.append(f"## {section_title}")

            lines.append("")  # Empty line after heading

            # Generate links for items in this section (recursively)
            self._generate_section_items(section_children, base_path, lines, depth=0)

            lines.append("")  # Empty line after section

        return "\n".join(lines).rstrip()

    def _generate_section_items(self, items: list[Any], base_path: str, lines: list[str], depth: int = 0) -> None:
        """Recursively generate markdown links for section items.

        Parameters
        ----------
        items : list[Any]
            List of navigation items to process.
        base_path : str
            Base path for generating relative links.
        lines : list[str]
            List to append generated markdown lines to.
        depth : int
            Current nesting depth. Default is 0.
        """
        for item in items:
            title = getattr(item, "title", "")
            url = getattr(item, "url", "")

            if not title or not url:
                continue

            # Skip index pages in the list (they're already linked in heading)
            if url.endswith("/index.html"):
                # But process their children if they exist
                if hasattr(item, "children") and item.children:
                    self._generate_section_items(item.children, base_path, lines, depth)
                continue

            # Convert HTML URL to markdown path
            md_path = url.replace(".html", ".md").lstrip("/")
            if md_path.startswith(base_path):
                md_path = md_path[len(base_path) :].lstrip("/")

            # Generate markdown link with proper indentation
            indent = "  " * depth
            lines.append(f"{indent}- [{title}]({md_path})")

            # Recursively process children
            if hasattr(item, "children") and item.children:
                self._generate_section_items(item.children, base_path, lines, depth + 1)

    def on_nav(self, nav: Navigation, /, *, config: MkDocsConfig, files: Files) -> Navigation | None:
        """Store navigation structure for later use.

        Parameters
        ----------
        nav : Navigation
            Navigation structure.
        config : MkDocsConfig
            MkDocs configuration object.
        files : Files
            Files collection.

        Returns
        -------
        Navigation | None
            Unmodified navigation structure.
        """
        self.nav = nav
        return nav

    def on_page_markdown(self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Files) -> str | None:
        """Process markdown content to generate index page content.

        Automatically detects pages containing the marker comment and generates
        index content for them based on the navigation structure.

        Parameters
        ----------
        markdown : str
            Original markdown content.
        page : Page
            The page being processed.
        config : MkDocsConfig
            MkDocs configuration object.
        files : Files
            Files collection.

        Returns
        -------
        str | None
            Modified markdown content, or None to use original.
        """
        if not self.config["enabled"]:
            return None

        # Check if the page contains the marker comment
        marker: str = str(self.config["preserve_above_marker"])  # type: ignore[arg-type]
        if marker not in markdown:
            return None

        # Use stored navigation structure
        if self.nav is None:
            return None

        page_url = page.url

        # Find the nav item that corresponds to this page
        # Navigation.items is a list of navigation items
        nav_items: list[Any] = getattr(self.nav, "items", [])
        nav_item = self._find_nav_item(nav_items, page_url)
        if nav_item is None:
            return None

        # Generate markdown content from navigation
        base_path = page_url.rsplit("/", 1)[0] if "/" in page_url else ""
        generated_content = self._organize_by_sections(nav_item, base_path)
        if not generated_content:
            return None

        # Preserve content above marker, replace below
        parts = markdown.split(marker, 1)
        return f"{parts[0]}{marker}\n\n{generated_content}"
