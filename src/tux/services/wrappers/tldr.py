"""
TLDR Pages Client Wrapper.

A pure Python implementation of the TLDR client specification v2.3,
providing command documentation lookup with proper caching, localization, and platform support.
This wrapper contains no Discord dependencies and can be used independently.
"""

import contextlib
import os
import re
import shutil
import time
import zipfile
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Configuration constants following 12-factor app principles
# Resolve relative paths to absolute to avoid permission issues
_cache_dir = os.getenv("TLDR_CACHE_DIR", ".cache/tldr")
CACHE_DIR: Path = (
    Path(_cache_dir).resolve()
    if not Path(_cache_dir).is_absolute()
    else Path(_cache_dir)
)
MAX_CACHE_AGE_HOURS: int = int(os.getenv("TLDR_CACHE_AGE_HOURS", "168"))
REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("TLDR_REQUEST_TIMEOUT", "10"))
ARCHIVE_DOWNLOAD_TIMEOUT_SECONDS: int = 30
DISCORD_EMBED_MAX_LENGTH: int = 4000

# TLDR API endpoints
PAGES_SOURCE_URL = "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages"
ARCHIVE_URL_TEMPLATE = (
    "https://github.com/tldr-pages/tldr/releases/latest/download/tldr-pages{suffix}.zip"
)

# Platform mappings following TLDR spec
PLATFORM_MAPPINGS = {
    "android": "android",
    "darwin": "osx",
    "freebsd": "freebsd",
    "linux": "linux",
    "macos": "osx",  # alias
    "netbsd": "netbsd",
    "openbsd": "openbsd",
    "sunos": "sunos",
    "win32": "windows",
    "windows": "windows",
}

SUPPORTED_PLATFORMS = sorted([*set(PLATFORM_MAPPINGS.values()), "common"])


class TldrClient:
    """
    Core TLDR client functionality for fetching and managing pages.

    Implements the TLDR client specification v2.3 with proper caching,
    platform detection, and language fallback mechanisms.
    """

    @staticmethod
    def normalize_page_name(name: str) -> str:
        """
        Normalize command name according to TLDR specification.

        Parameters
        ----------
        name : str
            Raw command name that may contain spaces or mixed case.

        Returns
        -------
        str
            Normalized command name: lowercase, dash-separated, trimmed.

        Examples
        --------
        >>> TldrClient.normalize_page_name("git status")
        "git-status"
        >>> TldrClient.normalize_page_name("GyE D3")
        "gye-d3"
        """
        return "-".join(name.lower().strip().split())

    @staticmethod
    def get_cache_file_path(command: str, platform: str, language: str) -> Path:
        """
        Generate the file system path for a cached TLDR page.

        Parameters
        ----------
        command : str
            Normalized command name.
        platform : str
            Target platform (linux, osx, windows, etc.).
        language : str
            Language code (en, es, fr, etc.).

        Returns
        -------
        Path
            Full path to the cached page file.
        """
        pages_dir = f"pages{f'.{language}' if language != 'en' else ''}"
        return CACHE_DIR / pages_dir / platform / f"{command}.md"

    @staticmethod
    def have_recent_cache(command: str, platform: str, language: str) -> bool:
        """
        Check if a recent cached version of a page exists.

        Parameters
        ----------
        command : str
            Command name to check.
        platform : str
            Platform to check.
        language : str
            Language to check.

        Returns
        -------
        bool
            True if cached file exists and is within MAX_CACHE_AGE_HOURS.
        """
        try:
            cache_file_path = TldrClient.get_cache_file_path(
                command,
                platform,
                language,
            )
            if not cache_file_path.exists():
                return False
            last_modified = cache_file_path.stat().st_mtime
            hours_passed = (time.time() - last_modified) / 3600
        except OSError:
            return False
        else:
            return hours_passed <= MAX_CACHE_AGE_HOURS

    @staticmethod
    def load_page_from_cache(command: str, platform: str, language: str) -> str | None:
        """
        Load a TLDR page from local cache.

        Parameters
        ----------
        command : str
            Command name.
        platform : str
            Platform name.
        language : str
            Language code.

        Returns
        -------
        str | None
            Page content if available, None if not found or on error.
        """
        with contextlib.suppress(OSError):
            cache_path = TldrClient.get_cache_file_path(command, platform, language)
            if cache_path.exists():
                return cache_path.read_text(encoding="utf-8")
        return None

    @staticmethod
    def store_page_to_cache(
        page: str,
        command: str,
        platform: str,
        language: str,
    ) -> None:
        """
        Store a TLDR page to local cache.

        Parameters
        ----------
        page : str
            Page content to store.
        command : str
            Command name.
        platform : str
            Platform name.
        language : str
            Language code.
        """
        with contextlib.suppress(OSError):
            cache_file_path = TldrClient.get_cache_file_path(
                command,
                platform,
                language,
            )
            cache_file_path.parent.mkdir(parents=True, exist_ok=True)
            cache_file_path.write_text(page, encoding="utf-8")

    @staticmethod
    def detect_platform() -> str:
        """
        Detect the default platform for Discord bot context.

        Returns
        -------
        str
            Platform identifier, defaults to 'linux' for container environments.
        """
        return "linux"  # Default for containerized Discord bots

    @staticmethod
    def get_language_priority(user_language: str | None = None) -> list[str]:
        """
        Get prioritized list of languages for Discord bot context.

        Parameters
        ----------
        user_language : str | None
            User-specified language preference.

        Returns
        -------
        list[str]
            Ordered list of languages to try, always ending with 'en'.
        """
        languages: list[str] = []
        if user_language:
            languages.append(user_language)
        if "en" not in languages:
            languages.append("en")
        return languages

    @staticmethod
    def get_platform_priority(user_platform_input: str | None = None) -> list[str]:
        """
        Determine platform search order based on user input and TLDR spec.

        Parameters
        ----------
        user_platform_input : str | None
            User-specified platform preference.

        Returns
        -------
        list[str]
            Ordered list of platforms to search, following TLDR specification.

        Notes
        -----
        Implementation follows TLDR spec v2.3:
        - If user specifies "common", only return "common"
        - Otherwise: [user_platform, detected_platform, common, all_other_platforms]
        """
        platforms_to_try: list[str] = []

        # Handle explicit "common" request per TLDR spec
        if user_platform_input == "common":
            return ["common"]

        # Add user-specified platform first
        if user_platform_input and user_platform_input in SUPPORTED_PLATFORMS:
            platforms_to_try.append(user_platform_input)
            # Handle macos alias
            if user_platform_input == "macos" and "osx" not in platforms_to_try:
                platforms_to_try.append("osx")

        # Add detected platform if different
        detected_os = TldrClient.detect_platform()
        if detected_os not in platforms_to_try:
            platforms_to_try.append(detected_os)

        # Add common as fallback
        if "common" not in platforms_to_try:
            platforms_to_try.append("common")

        # Add all other platforms as final fallback per TLDR spec
        for platform in SUPPORTED_PLATFORMS:
            if platform not in platforms_to_try:
                platforms_to_try.append(platform)

        return platforms_to_try

    @staticmethod
    def fetch_tldr_page(
        command: str,
        languages: list[str],
        platform_preference: str | None = None,
    ) -> tuple[str, str] | None:
        """
        Fetch a TLDR page with platform priority and language fallback.

        Parameters
        ----------
        command : str
            Normalized command name to fetch.
        languages : list[str]
            Ordered list of languages to try.
        platform_preference : str | None
            User's platform preference.

        Returns
        -------
        tuple[str, str] | None
            Tuple of (page_content, found_platform) if successful, None if not found.

        Notes
        -----
        Follows TLDR spec priority: platform takes precedence over language.
        Tries cache first, then remote fetch with automatic caching.
        """
        platforms_to_try = TldrClient.get_platform_priority(platform_preference)

        for language in languages:
            for platform in platforms_to_try:
                # Check cache first
                if TldrClient.have_recent_cache(command, platform, language) and (
                    cache_content := TldrClient.load_page_from_cache(
                        command,
                        platform,
                        language,
                    )
                ):
                    return (cache_content, platform)

                # Fetch from remote
                suffix = f".{language}" if language != "en" else ""
                url = f"{PAGES_SOURCE_URL}{suffix}/{platform}/{command}.md"

                try:
                    req = Request(url, headers={"User-Agent": "tldr-python-client"})
                    with urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                        page_content = resp.read().decode("utf-8")
                        TldrClient.store_page_to_cache(
                            page_content,
                            command,
                            platform,
                            language,
                        )
                        return (page_content, platform)
                except (HTTPError, URLError):
                    continue  # Try next platform/language combination

        return None

    @staticmethod
    def list_tldr_commands(
        language: str = "en",
        platform_filter: str | None = "linux",
    ) -> list[str]:
        """
        List available TLDR commands for a given language and platform filter.

        Parameters
        ----------
        language : str
            Language code to search.
        platform_filter : str | None
            Platform to filter by. If None, searches linux + common platforms.

        Returns
        -------
        list[str]
            Sorted list of available command names.
        """
        commands_set: set[str] = set()

        normalized_lang_for_dir = "en" if language.startswith("en") else language
        pages_dir_name = (
            f"pages.{normalized_lang_for_dir}"
            if normalized_lang_for_dir != "en"
            else "pages"
        )

        # Handle platform filtering logic
        if platform_filter is None:
            # When no filter specified, search linux + common
            platforms_to_scan = ["linux", "common"]
        else:
            # Use the specified platform
            platforms_to_scan = [platform_filter]
            # Always include common unless it was explicitly requested
            if platform_filter != "common":
                platforms_to_scan.append("common")

        unique_platforms_to_scan = list(dict.fromkeys(platforms_to_scan))

        for platform in unique_platforms_to_scan:
            path: Path = CACHE_DIR / pages_dir_name / platform

            try:
                # Skip if path doesn't exist
                if not path.exists() or not path.is_dir():
                    continue

                # Collect all .md files
                found_in_platform: set[str] = {
                    file.stem for file in path.iterdir() if file.suffix == ".md"
                }
                commands_set.update(found_in_platform)
            except OSError:
                continue

        return sorted(commands_set)

    @staticmethod
    def parse_placeholders(
        line: str,
        show_short: bool = False,
        show_long: bool = True,
        show_both: bool = False,
        highlight: bool = True,
    ) -> str:
        """
        Parse and format placeholder text in TLDR pages.

        Parameters
        ----------
        line : str
            Line containing TLDR placeholder syntax.
        show_short : bool
            Show only short options for placeholders.
        show_long : bool
            Show only long options for placeholders.
        show_both : bool
            Show both short and long options.
        highlight : bool
            Whether to apply highlighting markup.

        Returns
        -------
        str
            Processed line with placeholders resolved.
        """
        line = line.replace(r"\{\{", "__TEMP_ESCAPED_OPEN__")
        line = line.replace(r"\}\}", "__TEMP_ESCAPED_CLOSE__")

        def repl(match: re.Match[str]) -> str:
            """Process individual placeholder matches for replacement.

            Parameters
            ----------
            match : re.Match[str]
                Regex match object containing the placeholder content.

            Returns
            -------
            str
                The processed placeholder replacement.
            """
            content = match.group(1)
            if content.startswith("[") and content.endswith("]") and "|" in content:
                short, long = content[1:-1].split("|", 1)
                if show_both:
                    chosen = f"{short}|{long}"
                elif show_short:
                    chosen = short
                else:
                    chosen = long
            else:
                chosen = content
            # Only underline if not a literal option (doesn't start with '-')
            if highlight and not chosen.lstrip().startswith("-"):
                return f"__{chosen}__"
            return chosen

        line = re.sub(r"\{\{(.*?)\}\}", repl, line)
        line = line.replace("__TEMP_ESCAPED_OPEN__", "{{")
        return line.replace("__TEMP_ESCAPED_CLOSE__", "}}")

    @staticmethod
    def _process_description_lines(
        lines: list[str],
        i: int,
        show_short: bool,
        show_long: bool,
        show_both: bool,
    ) -> tuple[list[str], int]:
        """Process consecutive description lines starting with '>'.

        Parameters
        ----------
        lines : list[str]
            All lines from the TLDR page.
        i : int
            Current line index.
        show_short : bool
            Show short options.
        show_long : bool
            Show long options.
        show_both : bool
            Show both options.

        Returns
        -------
        tuple[list[str], int]
            Tuple of (parsed description lines, updated line index).
        """
        description_lines: list[str] = []
        while i < len(lines):
            line = lines[i].rstrip()
            if not line.startswith(">"):
                break
            parsed_line = TldrClient.parse_placeholders(
                line[1:].strip(),
                show_short,
                show_long,
                show_both,
                highlight=True,
            )
            description_lines.append(parsed_line)
            i += 1
        return description_lines, i

    @staticmethod
    def _process_command_examples(
        lines: list[str],
        i: int,
        show_short: bool,
        show_long: bool,
        show_both: bool,
    ) -> tuple[list[str], int]:
        """Process command examples and descriptions.

        Parameters
        ----------
        lines : list[str]
            All lines from the TLDR page.
        i : int
            Current line index.
        show_short : bool
            Show short options.
        show_long : bool
            Show long options.
        show_both : bool
            Show both options.

        Returns
        -------
        tuple[list[str], int]
            Tuple of (formatted command lines, updated line index).
        """
        formatted: list[str] = []
        last_was_command = False
        first_description_found = False

        while i < len(lines):
            current_line = lines[i].rstrip()
            if not current_line:
                i += 1
                continue

            if current_line.startswith("- "):
                if not first_description_found:
                    formatted.append("")
                    first_description_found = True
                elif last_was_command:
                    formatted.append("")

                current_line = TldrClient.parse_placeholders(
                    current_line,
                    show_short,
                    show_long,
                    show_both,
                    highlight=True,
                )
                formatted.append(current_line[2:])
                last_was_command = False

            elif current_line.startswith("`") and current_line.endswith("`"):
                current_line = TldrClient.parse_placeholders(
                    current_line,
                    show_short,
                    show_long,
                    show_both,
                    highlight=False,
                )
                formatted.append(f"- `{current_line[1:-1]}`")
                last_was_command = True

            else:
                current_line = TldrClient.parse_placeholders(
                    current_line,
                    show_short,
                    show_long,
                    show_both,
                    highlight=True,
                )
                formatted.append(current_line)
                last_was_command = False
            i += 1

        return formatted, i

    @staticmethod
    def format_tldr_for_discord(
        md: str,
        show_short: bool = False,
        show_long: bool = True,
        show_both: bool = False,
    ) -> str:
        """
        Format a TLDR markdown page for Discord output.

        Parameters
        ----------
        md : str
            Raw TLDR markdown content.
        show_short : bool
            Show only short options for placeholders.
        show_long : bool
            Show only long options for placeholders.
        show_both : bool
            Show both short and long options.

        Returns
        -------
        str
            Formatted content suitable for Discord display.
        """
        lines = md.splitlines()
        formatted: list[str] = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i].rstrip()
            if line.startswith("# "):
                i += 1
                break
            i += 1

        description_lines, i = TldrClient._process_description_lines(
            lines,
            i,
            show_short,
            show_long,
            show_both,
        )
        if description_lines:
            formatted.append("> " + "\n> ".join(description_lines))

        if i < n and lines[i].strip():
            i += 1

        command_formatted, _ = TldrClient._process_command_examples(
            lines,
            i,
            show_short,
            show_long,
            show_both,
        )
        formatted.extend(command_formatted)

        return "\n".join(formatted)

    @staticmethod
    def not_found_message(command: str) -> str:
        """
        Generate a message for when a page is not found.

        Parameters
        ----------
        command : str
            Command that was not found.

        Returns
        -------
        str
            Formatted not found message with GitHub link.
        """
        url = f"https://github.com/tldr-pages/tldr/issues/new?title=page%20request:{command}"
        return f"No TLDR page found for `{command}`.\n[Request it on GitHub]({url})"

    @staticmethod
    def update_tldr_cache(language: str = "en") -> str:
        """
        Update the TLDR cache for a specific language.

        Parameters
        ----------
        language : str
            Language code to update cache for.

        Returns
        -------
        str
            Status message indicating success or failure.

        Notes
        -----
        Downloads from GitHub releases following TLDR spec v2.3.
        Replaces existing cache completely to ensure consistency.
        """
        suffix = "" if language.startswith("en") else f".{language}"
        pages_dir_name = "pages" if language.startswith("en") else f"pages.{language}"

        url = ARCHIVE_URL_TEMPLATE.format(suffix=suffix)

        try:
            req = Request(
                url,
                headers={
                    "User-Agent": "tldr-python-client",
                    "Accept": "application/zip",
                },
            )

            with urlopen(req, timeout=ARCHIVE_DOWNLOAD_TIMEOUT_SECONDS) as resp:
                content = resp.read()

                if content.strip().lower().startswith((b"<!doctype html", b"<html>")):
                    return f"Failed to update cache for '{language}': Invalid content received"

                target_path = CACHE_DIR / pages_dir_name

                if target_path.exists():
                    try:
                        shutil.rmtree(target_path)
                    except OSError:
                        for item in target_path.rglob("*"):
                            try:
                                if item.is_file():
                                    item.unlink()
                                elif item.is_dir():
                                    item.rmdir()
                            except OSError:
                                continue
                        with contextlib.suppress(OSError):
                            target_path.rmdir()

                target_path.mkdir(parents=True, exist_ok=True)

                with zipfile.ZipFile(BytesIO(content)) as archive:
                    archive.extractall(target_path)

                return f"Cache updated for language `{language}` from {url}"

        except HTTPError as e:
            if e.code == 404:
                return (
                    f"Failed to update cache for '{language}': Archive not found (404)"
                )
            return f"Failed to update cache for '{language}': {e}"
        except zipfile.BadZipFile:
            return f"Failed to update cache for '{language}': Invalid zip file"
        except Exception as e:
            return f"Failed to update cache for '{language}': {e}"

    @staticmethod
    def cache_needs_update(language: str = "en") -> bool:
        """
        Check if the cache needs updating based on age.

        Parameters
        ----------
        language : str
            Language to check cache for.

        Returns
        -------
        bool
            True if cache is missing or older than MAX_CACHE_AGE_HOURS.
        """
        pages_dir_name = "pages" if language.startswith("en") else f"pages.{language}"
        cache_dir = CACHE_DIR / pages_dir_name

        if not cache_dir.exists():
            return True

        try:
            last_modified = cache_dir.stat().st_mtime
            hours_passed = (time.time() - last_modified) / 3600
        except (FileNotFoundError, PermissionError):
            return True
        else:
            return hours_passed > MAX_CACHE_AGE_HOURS

    @staticmethod
    def split_long_text(
        text: str,
        max_len: int = DISCORD_EMBED_MAX_LENGTH,
    ) -> list[str]:
        """
        Split long text into pages for Discord embeds.

        Parameters
        ----------
        text : str
            Text to split.
        max_len : int
            Maximum length per page.

        Returns
        -------
        list[str]
            List of text chunks within max_len limits.
        """
        lines = text.splitlines(keepends=True)
        pages: list[str] = []
        current_text_chunk = ""
        for line_content in lines:
            if len(current_text_chunk) + len(line_content) > max_len:
                pages.append(current_text_chunk)
                current_text_chunk = ""
            current_text_chunk += line_content
        if current_text_chunk:
            pages.append(current_text_chunk)
        return pages
