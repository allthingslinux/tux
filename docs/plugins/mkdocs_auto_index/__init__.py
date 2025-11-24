"""MkDocs plugin for auto-generating index pages from navigation structure.

This plugin automatically generates index page content based on the navigation
structure, creating organized lists of links for section index pages.

Note: This plugin works in conjunction with mkdocs-section-index, which normalizes
URLs (e.g., bot-token.md becomes bot-token/index.html). This plugin handles the
URL normalization to correctly generate links for both directories and single files.
"""

from __future__ import annotations

import contextlib
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
    preserve_above_marker = config_options.Type(
        str,
        default="<!-- AUTO_INDEX_START -->",
    )


class IndexGeneratorPlugin(BasePlugin[IndexGeneratorConfig]):
    """MkDocs plugin for auto-generating index page content."""

    def __init__(self):
        """Initialize the plugin."""
        super().__init__()
        self.nav: Navigation | None = None
        self.files: Files | None = None
        self.docs_dir: Path | None = None

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
        # Store docs_dir for file system checks
        self.docs_dir = Path(config["docs_dir"])  # type: ignore[index]

        # Add plugins directory to Python path so MkDocs can find local plugins
        plugins_dir = self.docs_dir / "plugins"
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

    def _is_directory(self, md_path: str, base_path: str = "") -> bool:
        """Check if a markdown path represents a directory by checking if index.md exists.

        Parameters
        ----------
        md_path : str
            Markdown path to check (e.g., "shared" or "concepts/shared").
        base_path : str
            Base path to prepend (e.g., "developer/concepts/").

        Returns
        -------
        bool
            True if the path is a directory (has index.md), False otherwise.
        """
        # Construct full path relative to docs_dir
        full_path = (
            f"{base_path.rstrip('/')}/{md_path}/index.md"
            if base_path
            else f"{md_path}/index.md"
        )

        # Normalize path (remove leading slash, ensure forward slashes)
        full_path = full_path.lstrip("/").replace("\\", "/")

        # First try MkDocs files collection if available
        if self.files is not None:
            # Try without .md extension (MkDocs format)
            path_without_ext = full_path[:-3]  # Remove .md
            with contextlib.suppress(Exception):
                file_obj = self.files.get_file_from_path(path_without_ext)
                if file_obj is not None:
                    return True

        # Fallback: check file system directly
        # This is more reliable when files collection isn't populated yet
        if self.docs_dir is None:
            return False
        try:
            file_path = self.docs_dir / full_path
            return file_path.exists()
        except Exception:
            return False

    def _has_hyphen_or_underscore(self, path: str) -> bool:
        """Check if path contains hyphens or underscores in the last segment.

        Parameters
        ----------
        path : str
            Path to check.

        Returns
        -------
        bool
            True if last segment contains hyphens or underscores.
        """
        last_segment = path.split("/")[-1]
        return "-" in last_segment or "_" in last_segment

    def _is_single_file(self, md_path: str, base_path: str = "") -> bool:
        """Check if a markdown path represents a single file (not a directory).

        Parameters
        ----------
        md_path : str
            Markdown path to check (without .md extension).
        base_path : str
            Base path for file system checks.

        Returns
        -------
        bool
            True if the path represents a single file, False otherwise.
        """
        # Construct full path relative to docs_dir
        full_path = (
            f"{base_path.rstrip('/')}/{md_path}.md" if base_path else f"{md_path}.md"
        )
        full_path = full_path.lstrip("/").replace("\\", "/")

        # First try MkDocs files collection if available
        if self.files is not None:
            with contextlib.suppress(Exception):
                file_obj = self.files.get_file_from_path(md_path)
                if file_obj is not None:
                    return True

        # Fallback: check file system directly
        if self.docs_dir is None:
            return False
        try:
            file_path = self.docs_dir / full_path
            return file_path.exists()
        except Exception:
            return False

    def _handle_index_html_url(self, md_path: str, has_children: bool) -> str:
        # sourcery skip: hoist-statement-from-if, reintroduce-else
        """Handle URLs ending with /index.html (section-index normalization).

        Parameters
        ----------
        md_path : str
            Markdown path to process.
        has_children : bool
            Whether the navigation item has children.

        Returns
        -------
        str
            Resolved markdown path.
        """
        # If md_path already ends with /index.md or /index, it's a directory
        if md_path.endswith("/index.md"):
            return md_path  # Already correct
        if md_path.endswith("/index"):
            return f"{md_path}.md"  # Add .md extension

        # Check if this looks like a single file (has hyphens/underscores)
        # Directories like 'shared', 'services', 'core' don't have these
        path_before_index = md_path.replace("/index.md", "").replace("/index", "")
        looks_like_single_file = self._has_hyphen_or_underscore(path_before_index)

        if has_children or not looks_like_single_file:
            # Directory with index - ensure /index.md is appended
            return (
                f"{md_path}index.md" if md_path.endswith("/") else f"{md_path}/index.md"
            )

        # Single file normalized by section-index: bot-token/index.html -> bot-token.md
        return f"{md_path}.md"

    def _handle_trailing_slash_url(
        self,
        md_path: str,
        original_url: str,
        base_path: str = "",
    ) -> str:
        """Handle URLs ending with trailing slash.

        Parameters
        ----------
        md_path : str
            Markdown path to process.
        original_url : str
            Original HTML URL.
        base_path : str
            Base path for file system checks.

        Returns
        -------
        str
            Resolved markdown path.
        """
        path_without_slash = md_path.rstrip("/")

        # If URL ends with /index.html, it's from section-index normalization
        if original_url.endswith("/index.html"):
            has_hyphen = self._has_hyphen_or_underscore(path_without_slash)
            return f"{path_without_slash}.md" if has_hyphen else f"{md_path}index.md"

        # Check if a single .md file exists first (section-index normalized single files)
        if self._is_single_file(path_without_slash, base_path):
            return f"{path_without_slash}.md"

        # URLs ending with / are typically directories
        # Check if path has no hyphens (likely a directory like 'shared', 'services')
        if not self._has_hyphen_or_underscore(path_without_slash):
            # No hyphens - treat as directory
            return f"{md_path}index.md"

        # Has hyphens - check file system to be sure it's a directory
        if self._is_directory(path_without_slash, base_path):
            return f"{md_path}index.md"

        # Default to single file
        return f"{path_without_slash}.md"

    def _resolve_path_without_extension(
        self,
        original_url: str,
        md_path: str,
        base_path: str,
    ) -> str:
        """Resolve path without extension by checking file system and URL format.

        Parameters
        ----------
        original_url : str
            Original HTML URL.
        md_path : str
            Markdown path to resolve.
        base_path : str
            Base path for file system checks.

        Returns
        -------
        str
            Resolved markdown path.
        """
        # Check file system first - most reliable check
        # This handles directories like 'shared', 'services', 'core' that don't have hyphens
        if self._is_directory(md_path, base_path):
            return f"{md_path}/index.md"

        # If URL ends with /, it's likely a directory (even if file system check failed)
        if original_url.endswith("/"):
            return f"{md_path}/index.md"

        # If no hyphens/underscores, treat as directory (common pattern for directories)
        # This is a heuristic fallback for directories without children
        # Directories like 'shared', 'services', 'core', 'tasks' don't have hyphens
        has_hyphen = self._has_hyphen_or_underscore(md_path)
        if not has_hyphen:
            # No hyphens = likely a directory, always treat as directory
            return f"{md_path}/index.md"

        # Has hyphens/underscores - likely a single file (e.g., 'bot-token', 'first-run')
        return f"{md_path}.md"

    def _resolve_markdown_path(
        self,
        original_url: str,
        md_path: str,
        base_path: str,
        has_children: bool,
    ) -> str:
        """Resolve a markdown path, determining if it's a directory or single file.

        Parameters
        ----------
        original_url : str
            Original HTML URL from navigation.
        md_path : str
            Markdown path (relative to base_path).
        base_path : str
            Base path for generating relative links.
        has_children : bool
            Whether the navigation item has children.

        Returns
        -------
        str
            Resolved markdown path with proper extension.
        """
        # Already has .md extension - check if it's actually a directory
        if md_path.endswith(".md"):
            # If it ends with /index.md, it's correct
            if md_path.endswith("/index.md"):
                return md_path
            # Check if this .md file is actually a directory (has index.md)
            # Remove .md and check if directory exists
            path_without_md = md_path[:-3]  # Remove .md
            # If path has no hyphens/underscores, it's likely a directory
            # Directories like 'shared', 'services', 'core', 'tasks' don't have hyphens
            if not self._has_hyphen_or_underscore(path_without_md):
                # No hyphens - always treat as directory
                return f"{path_without_md}/index.md"
            # Has hyphens - check file system but default to single file
            if self._is_directory(path_without_md, base_path):
                return f"{path_without_md}/index.md"
            return md_path

        # Handle URLs ending with /index.html (section-index normalization)
        if original_url.endswith("/index.html"):
            return self._handle_index_html_url(md_path, has_children)

        # Handle URLs ending with /
        if md_path.endswith("/"):
            if has_children:
                return f"{md_path}index.md"
            return self._handle_trailing_slash_url(md_path, original_url, base_path)

        # Handle URLs without extension - check file system
        if has_children:
            return f"{md_path}/index.md"

        return self._resolve_path_without_extension(original_url, md_path, base_path)

    def _generate_markdown_from_nav(
        self,
        nav_item: Any,
        base_path: str = "",
        depth: int = 0,
    ) -> str:
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
                            lines.extend(
                                self._generate_markdown_from_nav(
                                    grandchild,
                                    base_path,
                                    depth,
                                ).splitlines(),
                            )
                    continue

                # Get title and URL
                title = getattr(child, "title", "")
                url = getattr(child, "url", "")

                if not title or not url:
                    continue

                # Convert HTML URL to markdown path
                original_url = url
                has_children = hasattr(child, "children") and child.children
                md_path = url.replace(".html", ".md").lstrip("/")
                if md_path.startswith(base_path):
                    md_path = md_path[len(base_path) :].lstrip("/")

                # Resolve path (directory vs single file)
                md_path = self._resolve_markdown_path(
                    original_url,
                    md_path,
                    base_path,
                    has_children,
                )

                # Generate markdown link
                indent = "  " * depth
                lines.append(f"{indent}- [{title}]({md_path})")

                # Recursively process children
                if hasattr(child, "children") and child.children:
                    child_lines = self._generate_markdown_from_nav(
                        child,
                        base_path,
                        depth + 1,
                    )
                    lines.extend(child_lines.splitlines())

        return "\n".join(lines)

    def _organize_by_sections(self, nav_item: Any, base_path: str = "") -> str:  # noqa: PLR0912
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

        # Add "Sections" header at the top
        lines.append("## Sections")
        lines.append("")  # Empty line after heading

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
                has_children = hasattr(item, "children") and item.children
                # Check for index page (either /index.html with children, or trailing / with children)
                # Only treat as directory if it has children
                if (url.endswith("/index.html") and has_children) or (
                    url.endswith("/") and url != "/" and has_children
                ):
                    section_url = url
                    # Get children of the index page
                    if has_children:
                        children: list[Any] = list(item.children)
                        section_children.extend(children)  # type: ignore[arg-type]
                    break

            # If no index page found, use direct children
            if not section_url:
                section_children = items

            # Generate section heading with link if it has an index
            if section_url:
                # Check original URL format to determine if it's a directory or file
                original_section_url = section_url
                md_path = section_url.replace(".html", ".md").lstrip("/")
                if md_path.startswith(base_path):
                    md_path = md_path[len(base_path) :].lstrip("/")
                # Section URLs should be directories (they have children)
                # But check original URL to be safe
                if original_section_url.endswith("/index.html"):
                    # Directory with index - ensure index.md is present
                    md_path = (
                        f"{md_path}index.md"
                        if md_path.endswith("/")
                        else f"{md_path}/index.md"
                    )
                elif md_path.endswith("/"):
                    # URL ends with / - for sections, this should be a directory
                    md_path = f"{md_path}index.md"
                elif not md_path.endswith(".md"):
                    # Shouldn't happen for section URLs, but add .md just in case
                    md_path = f"{md_path}.md"
                lines.append(f"### [{section_title}]({md_path})")
            else:
                lines.append(f"### {section_title}")

            lines.append("")  # Empty line after heading

            # Generate links for items in this section (recursively)
            # Children start at depth 1 (indented under the section heading)
            self._generate_section_items(section_children, base_path, lines, depth=1)

            lines.append("")  # Empty line after section

        return "\n".join(lines).rstrip()

    def _generate_section_items(
        self,
        items: list[Any],
        base_path: str,
        lines: list[str],
        depth: int = 0,
    ) -> None:
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
            original_url = url
            has_children = hasattr(item, "children") and item.children
            md_path = url.replace(".html", ".md").lstrip("/")
            if md_path.startswith(base_path):
                md_path = md_path[len(base_path) :].lstrip("/")

            # Resolve path (directory vs single file)
            md_path = self._resolve_markdown_path(
                original_url,
                md_path,
                base_path,
                has_children,
            )

            # Generate markdown link with proper indentation
            indent = "  " * depth
            lines.append(f"{indent}- [{title}]({md_path})")

            # Recursively process children
            if hasattr(item, "children") and item.children:
                self._generate_section_items(item.children, base_path, lines, depth + 1)

    def on_nav(
        self,
        nav: Navigation,
        /,
        *,
        config: MkDocsConfig,
        files: Files,
    ) -> Navigation | None:
        """Store navigation structure and files collection for later use.

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
        self.files = files
        return nav

    def on_page_markdown(
        self,
        markdown: str,
        /,
        *,
        page: Page,
        config: MkDocsConfig,
        files: Files,
    ) -> str | None:
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
