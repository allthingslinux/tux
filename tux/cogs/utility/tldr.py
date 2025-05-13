import os
import re
import shutil
import sys
import time
import zipfile
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
from loguru import logger

from tux.bot import Tux
from tux.ui.embeds import EmbedCreator
from tux.utils.flags import generate_usage

# --- Constants ---
PAGES_SOURCE_LOCATION = "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages"
DOWNLOAD_CACHE_LOCATION = "https://github.com/tldr-pages/tldr/releases/latest/download/tldr-pages.{lang}.zip"
CACHE_DIR: Path = Path(".cache/tldr")
MAX_CACHE_AGE: int = 24 * 7  # hours

OS_DIRECTORIES = {
    "android": "android",
    "darwin": "osx",
    "freebsd": "freebsd",
    "linux": "linux",
    "macos": "osx",  # macos is an alias for osx
    "netbsd": "netbsd",
    "openbsd": "openbsd",
    "sunos": "sunos",
    "win32": "windows",
    "windows": "windows",
}
SUPPORTED_PLATFORMS = sorted([*list(set(OS_DIRECTORIES.values())), "common"])


class TldrClient:
    """Core TLDR client functionality for fetching and managing pages."""

    @staticmethod
    def normalize_page_name(name: str) -> str:
        """Normalize command name: lowercase, dash-join, trim spaces."""
        return "-".join(name.lower().strip().split())

    @staticmethod
    def get_cache_file_path(command: str, platform: str, language: str) -> Path:
        """Get the path to a cached page file."""
        pages_dir: str = f"pages{f'.{language}' if language != 'en' else ''}"
        return CACHE_DIR / pages_dir / platform / f"{command}.md"

    @staticmethod
    def have_recent_cache(command: str, platform: str, language: str) -> bool:
        """Check if we have a recent cache for this command/platform/language."""
        try:
            cache_file_path = TldrClient.get_cache_file_path(command, platform, language)
            # If file doesn't exist, silently return False without an error
            if not cache_file_path.exists():
                return False
            last_modified = cache_file_path.stat().st_mtime
            hours_passed = (time.time() - last_modified) / 3600
        except (FileNotFoundError, PermissionError):
            # Silently return False without logging an error
            return False
        else:
            return hours_passed <= MAX_CACHE_AGE

    @staticmethod
    def load_page_from_cache(command: str, platform: str, language: str) -> str | None:
        """Load a page from the cache if it exists."""
        try:
            cache_path = TldrClient.get_cache_file_path(command, platform, language)
            if not cache_path.exists():
                logger.debug(f"Cache file does not exist: {cache_path}")
                return None
            with cache_path.open("r", encoding="utf-8") as f:
                return f.read()
        except OSError as e:
            logger.debug(f"Failed to load page from cache: {e}")
            return None

    @staticmethod
    def store_page_to_cache(page: str, command: str, platform: str, language: str) -> None:
        """Store a page to the cache."""
        try:
            cache_file_path = TldrClient.get_cache_file_path(command, platform, language)
            cache_file_path.parent.mkdir(parents=True, exist_ok=True)
            with cache_file_path.open("w", encoding="utf-8") as f:
                f.write(page)
        except OSError as e:
            logger.warning(f"Failed to store to cache: {e}")

    @staticmethod
    def detect_platform() -> str:
        """Detect the current operating system platform."""
        return next((value for key, value in OS_DIRECTORIES.items() if sys.platform.startswith(key)), "linux")

    @staticmethod
    def get_language_priority(lang_env: str | None = None, language_env: str | None = None) -> list[str]:
        """Get a prioritized list of languages to try."""
        languages: list[str] = []
        if language_env:
            languages.extend([lang for lang in language_env.split(":") if lang and lang not in ("C", "POSIX")])
        if lang_env and lang_env not in ("C", "POSIX") and lang_env not in languages:
            languages.append(lang_env)
        if "en" not in languages:
            languages.append("en")
        return languages

    @staticmethod
    def get_platform_priority(user_platform_input: str | None = None) -> list[str]:
        """Determine platform search order based on user input or detected OS."""
        platforms_to_try: list[str] = []

        # If user specified a platform, use that first
        if user_platform_input and user_platform_input.lower() in SUPPORTED_PLATFORMS:
            platforms_to_try.append(user_platform_input.lower())
            if user_platform_input.lower() == "macos" and "osx" not in platforms_to_try:
                platforms_to_try.append("osx")

        # Then try the detected platform if different from user specified
        detected_os = TldrClient.detect_platform()
        if detected_os not in platforms_to_try:
            platforms_to_try.append(detected_os)

        # Always ensure 'common' is included as a fallback
        if "common" not in platforms_to_try:
            platforms_to_try.append("common")

        logger.debug(f"Platform priority: {platforms_to_try}")
        return platforms_to_try

    @staticmethod
    def fetch_tldr_page(command: str, languages: list[str], platform_preference: str | None = None) -> str | None:
        """
        Try to fetch a TLDR page, considering platform priority and language fallback.
        Returns the page content or None.
        """
        platforms_to_try: list[str] = TldrClient.get_platform_priority(platform_preference)

        for language in languages:
            for platform in platforms_to_try:
                # First check cache
                if TldrClient.have_recent_cache(command, platform, language) and (
                    cache_content := TldrClient.load_page_from_cache(command, platform, language)
                ):
                    logger.debug(f"Found in cache: {command} for {platform}/{language}")
                    return cache_content

                # Then try to fetch from remote
                url: str = (
                    f"{PAGES_SOURCE_LOCATION}{f'.{language}' if language != 'en' else ''}/{platform}/{command}.md"
                )
                try:
                    req = Request(url, headers={"User-Agent": "tldr-python-client"})
                    with urlopen(req, timeout=10) as resp:
                        page_content = resp.read().decode("utf-8")
                        TldrClient.store_page_to_cache(page_content, command, platform, language)
                        logger.debug(f"Fetched from remote: {command} for {platform}/{language}")
                        return page_content
                except (HTTPError, URLError):
                    logger.debug(f"Command not found in {platform}/{language}, trying next platform")
                    continue

        # If we get here, we didn't find the page in any platform or language
        logger.debug(f"Command not found: {command} in any platform/language combination")
        return None

    @staticmethod
    def list_tldr_commands(language: str = "en", platform_filter: str | None = "linux") -> list[str]:
        """Lists available TLDR commands for a given language and platform filter."""
        commands_set: set[str] = set()

        normalized_lang_for_dir = "en" if language.startswith("en") else language
        pages_dir_name = f"pages.{normalized_lang_for_dir}" if normalized_lang_for_dir != "en" else "pages"

        effective_platform_filter = platform_filter or "common"  # Default to linux if None

        platforms_to_scan: list[str] = [effective_platform_filter]
        # Always include common unless it was explicitly requested
        if effective_platform_filter != "common":
            platforms_to_scan.append("common")

        # Remove duplicates while keeping original order
        unique_platforms_to_scan: list[str] = []
        seen_platforms: set[str] = set()
        for platform in platforms_to_scan:
            if platform not in seen_platforms:
                unique_platforms_to_scan.append(platform)
                seen_platforms.add(platform)

        logger.debug(
            f"[list_tldr_commands] Language: '{language}', NormDir: '{normalized_lang_for_dir}', "
            f"PageDir: '{pages_dir_name}', PlatFilterIn: '{platform_filter}', "
            f"EffectivePlat: '{effective_platform_filter}', Scanning: {unique_platforms_to_scan}",
        )

        for platform in unique_platforms_to_scan:
            path: Path = CACHE_DIR / pages_dir_name / platform
            logger.debug(f"[list_tldr_commands] Checking path: {path}")

            try:
                # Skip if path doesn't exist
                if not path.exists() or not path.is_dir():
                    logger.debug(f"[list_tldr_commands] Path not found or not a directory: {path}")
                    continue

                # Collect all .md files
                found_in_platform: set[str] = {file.stem for file in path.iterdir() if file.suffix == ".md"}
                logger.debug(f"[list_tldr_commands] Found {len(found_in_platform)} commands in {path}")
                commands_set.update(found_in_platform)
            except OSError as e:
                logger.debug(f"[list_tldr_commands] Error scanning directory {path}: {e}")
                continue

        logger.debug(
            f"[list_tldr_commands] Total {len(commands_set)} unique commands found for "
            f"lang='{language}', plat_filter='{platform_filter}' before sorting.",
        )
        return sorted(commands_set)

    @staticmethod
    def parse_placeholders(
        line: str,
        show_short: bool = False,
        show_long: bool = True,
        show_both: bool = False,
        highlight: bool = True,
    ) -> str:
        """Parse and format placeholder text in TLDR pages."""
        line = line.replace(r"\{\{", "__TEMP_ESCAPED_OPEN__")
        line = line.replace(r"\}\}", "__TEMP_ESCAPED_CLOSE__")

        def repl(match: re.Match[str]) -> str:
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
    def format_tldr_for_discord(
        md: str,
        show_short: bool = False,
        show_long: bool = True,
        show_both: bool = False,
    ) -> str:
        """Format a TLDR markdown page for Discord output."""
        lines = md.splitlines()
        formatted: list[str] = []
        command_name = None
        i = 0
        n = len(lines)

        # Find and render the title
        while i < n:
            line = lines[i].rstrip()
            if line.startswith("# "):
                # Skip adding the command name to formatted, since it's in the embed title
                command_name = line[2:].strip()
                i += 1
                break
            i += 1

        # Collect all consecutive description lines (starting with '>')
        description_lines: list[str] = []
        while i < n:
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
        if description_lines:
            formatted.append("> " + "\n> ".join(description_lines))

        # Skip any standalone command name line after the description
        if i < n and command_name and lines[i].strip() == command_name:
            i += 1

        # Render the rest as before
        while i < n:
            current_line = lines[i].rstrip()
            if not current_line:
                formatted.append("")
                i += 1
                continue
            if current_line.startswith("- "):
                current_line = TldrClient.parse_placeholders(
                    current_line,
                    show_short,
                    show_long,
                    show_both,
                    highlight=True,
                )
                formatted.append(current_line)
            elif current_line.startswith("`") and current_line.endswith("`"):
                current_line = TldrClient.parse_placeholders(
                    current_line,
                    show_short,
                    show_long,
                    show_both,
                    highlight=False,
                )
                formatted.append(f"`{current_line[1:-1]}`")
            else:
                current_line = TldrClient.parse_placeholders(
                    current_line,
                    show_short,
                    show_long,
                    show_both,
                    highlight=True,
                )
                formatted.append(current_line)
            i += 1

        return "\n".join(formatted)

    @staticmethod
    def not_found_message(command: str) -> str:
        """Generate a message for when a page is not found."""
        url = f"https://github.com/tldr-pages/tldr/issues/new?title=page%20request:{command}"
        return f"No TLDR page found for `{command}`.\n[Request it on GitHub]({url})"

    @staticmethod
    def update_tldr_cache(language: str = "en") -> str:
        """Update the TLDR cache for a specific language."""
        if language.startswith("en"):
            archive_name = "tldr-pages.zip"
            # For English, pages are stored directly under a 'pages' directory in the cache
            pages_dir_name_for_language = "pages"
        else:
            archive_name = f"tldr-pages.{language}.zip"
            # For other languages, pages are stored under 'pages.<lang>'
            pages_dir_name_for_language = f"pages.{language}"

        url = f"https://github.com/tldr-pages/tldr/releases/latest/download/{archive_name}"
        logger.debug(f"TLDR Cog: Attempting to download cache from {url}")

        try:
            req = Request(url, headers={"User-Agent": "tldr-python-client", "Accept": "application/zip"})
            with urlopen(req, timeout=30) as resp:
                logger.debug(f"TLDR Cog: Response status: {resp.status}")
                logger.debug(f"TLDR Cog: Response headers: {resp.getheaders()}")
                content = resp.read()

                if content.strip().lower().startswith(b"<!doctype html") or content.strip().lower().startswith(
                    b"<html>",
                ):
                    logger.error(f"TLDR Cog: Downloaded content appears to be HTML, not a zip file. URL: {url}")
                    logger.debug(f"TLDR Cog: HTML Snippet: {content[:500]}")
                    return f"Failed to update cache for '{language}': Downloaded content was HTML, not a zip file."

                target_pages_full_path = CACHE_DIR / pages_dir_name_for_language

                # 1. Clear the target pages directory if it exists from a previous run
                if target_pages_full_path.exists():
                    logger.info(f"TLDR Cog: Clearing old cache directory: {target_pages_full_path}")
                    shutil.rmtree(target_pages_full_path)

                # 2. Ensure the target_pages_full_path for extraction exists
                target_pages_full_path.mkdir(parents=True, exist_ok=True)

                try:
                    with zipfile.ZipFile(BytesIO(content)) as z:
                        logger.debug(f"TLDR Cog: Extracting all to: {target_pages_full_path}")
                        z.extractall(target_pages_full_path)
                except zipfile.BadZipFile as bzfe:
                    logger.error(
                        f"TLDR Cog: BadZipFile error for '{language}' from {url}: {bzfe}. Content length: {len(content)}",
                        exc_info=True,
                    )
                    if len(content) < 1024:
                        logger.debug(f"TLDR Cog: Content snippet (possibly corrupted zip): {content[:500]}")
                    return f"Failed to update cache for '{language}': File is not a valid zip file or is corrupted."
                else:
                    return f"Cache updated for language `{language}` (all platforms) from {url}."

        except HTTPError as e:
            if e.code == 404:
                logger.warning(f"TLDR Cog: Cache archive not found for language '{language}' at {url} (HTTP 404).")
                return f"Failed to update cache for '{language}': Archive not found (404). Check if a tldr archive exists for this language."
            logger.error(f"TLDR Cog: HTTPError during cache update for '{language}' from {url}: {e}", exc_info=True)
            return f"Failed to update cache for '{language}': {e}"
        except Exception as e:
            logger.error(f"TLDR Cog: Exception during cache update for '{language}' from {url}: {e}", exc_info=True)
            return f"Failed to update cache for '{language}': {e}"

    @staticmethod
    def split_long_text(text: str, max_len: int = 4000) -> list[str]:
        """Split long text into pages for Discord embeds."""
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


# --- Discord-specific classes ---


class TldrPaginatorView(View):
    """Paginator view for navigating through long TLDR pages."""

    def __init__(self, pages: list[str], title: str, user: discord.abc.User, bot: Tux):
        super().__init__(timeout=120)
        self.pages = pages
        self.page = 0
        self.title = title
        self.user = user
        self.bot = bot
        self.message: discord.Message | None = None
        self.add_item(Button[View](label="Previous", style=discord.ButtonStyle.secondary, custom_id="prev"))
        self.add_item(Button[View](label="Next", style=discord.ButtonStyle.secondary, custom_id="next"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="prev")
    async def prev(self, interaction: discord.Interaction, button: Button[View]):
        if self.page > 0:
            self.page -= 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next(self, interaction: discord.Interaction, button: Button[View]):
        if self.page < len(self.pages) - 1:
            self.page += 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    async def update_message(self, interaction: discord.Interaction):
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=self.user.name,
            user_display_avatar=self.user.display_avatar.url,
            title=f"{self.title} (Page {self.page + 1}/{len(self.pages)})",
            description=self.pages[self.page],
        )
        await interaction.response.edit_message(embed=embed, view=self)


# Define FlagConverter for prefix command options
class TldrFlags(commands.FlagConverter, prefix="-", delimiter=" "):
    command_words: tuple[str, ...] = commands.flag(name="_command_words", positional=True, default=())
    platform: str | None = commands.flag(description="Platform (e.g., linux, osx, common)", default=None)
    language: str | None = commands.flag(description="Language code (e.g., en, es, fr)", default=None)
    show_short: bool = commands.flag(description="Show only short options for placeholders", default=False)
    show_long: bool = commands.flag(
        description="Show only long options for placeholders (default if others false)",
        default=True,
    )
    show_both: bool = commands.flag(description="Show both short and long options for placeholders", default=False)


class Tldr(commands.Cog):
    """Discord cog for TLDR command integration."""

    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.default_language: str = self.detect_bot_language()
        self.prefix_tldr.usage = generate_usage(self.prefix_tldr)

    async def cog_load(self):
        """Automatically update TLDR cache when the cog is loaded."""
        logger.info("TLDR Cog: Starting automatic cache update.")
        # Normalize detected language before adding to set
        normalized_default_lang = self.default_language
        if normalized_default_lang.startswith("en") and normalized_default_lang != "en":
            normalized_default_lang = "en"  # Treat en_US, en_GB as 'en' for tldr pages

        languages_to_update = {normalized_default_lang, "en"}

        for lang_code in languages_to_update:
            logger.info(f"TLDR Cog: Updating cache for language '{lang_code}'...")
            try:
                result_msg = await self.bot.loop.run_in_executor(None, TldrClient.update_tldr_cache, lang_code)
                if "Failed" in result_msg:
                    logger.error(f"TLDR Cog: Cache update for '{lang_code}' - {result_msg}")
                else:
                    logger.info(f"TLDR Cog: Cache update for '{lang_code}' - {result_msg}")
            except Exception as e:
                logger.error(f"TLDR Cog: Exception during cache update for '{lang_code}': {e}", exc_info=True)
        logger.info("TLDR Cog: Automatic cache update process finished.")

    def detect_bot_language(self) -> str:
        """Detect the bot's language from environment variables."""
        lang_env = os.environ.get("LANG", "en_US.UTF-8")
        lang_code_full = lang_env.split(".")[0]  # Extracts 'en_US' or 'pt_BR' etc.

        if lang_code_full.startswith("en"):
            return "en"  # Standardize all English variants to 'en' for tldr logic
        return "en" if lang_code_full in ("C", "POSIX", "") else lang_code_full

    async def command_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for the command parameter."""
        language_value: str | None = None
        platform_value: str | None = None

        try:
            if hasattr(interaction, "namespace") and interaction.namespace:
                language_value = interaction.namespace.language
                platform_value = interaction.namespace.platform
        except AttributeError:
            logger.debug("TLDR Autocomplete: interaction.namespace not available or options not set.")

        final_language = language_value or self.default_language
        final_platform_for_list = platform_value or "linux"

        logger.debug(
            f"TLDR Autocomplete: UserLang: '{language_value}', UserPlat: '{platform_value}', "
            f"CurrentCmdQuery: '{current}' -> FinalLang: '{final_language}', "
            f"FinalPlatForList: '{final_platform_for_list}'",
        )

        commands_to_show = TldrClient.list_tldr_commands(
            language=final_language,
            platform_filter=final_platform_for_list,
        )

        logger.debug(
            f"TLDR Autocomplete: Found {len(commands_to_show)} potential commands "
            f"(lang='{final_language}', plat_filter='{final_platform_for_list}') "
            f"before filtering for query '{current}'.",
        )

        # Filter commands based on current input
        if not current:
            filtered_commands = [app_commands.Choice(name=cmd, value=cmd) for cmd in commands_to_show]
        else:
            filtered_commands = [
                app_commands.Choice(name=cmd, value=cmd) for cmd in commands_to_show if current.lower() in cmd.lower()
            ]

        logger.debug(f"TLDR Autocomplete: Returning {len(filtered_commands)} filtered choices.")
        return filtered_commands[:25]

    async def platform_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for the platform parameter."""
        logger.debug(f"TLDR Platform Autocomplete: current query='{current}'")
        choices = [
            app_commands.Choice(name=plat, value=plat)
            for plat in SUPPORTED_PLATFORMS
            if current.lower() in plat.lower()
        ]
        logger.debug(f"TLDR Platform Autocomplete: Returning {len(choices)} choices.")
        return choices[:25]

    @app_commands.command(name="tldr")
    @app_commands.guild_only()
    @app_commands.describe(
        command="The command to look up",
        platform="Platform (e.g., linux, osx, common)",
        language="Language code (e.g., en, es, fr)",
        show_short="Show only short options for placeholders",
        show_long="Show only long options for placeholders",
        show_both="Show both short and long options for placeholders",
    )
    @app_commands.autocomplete(command=command_autocomplete, platform=platform_autocomplete)
    async def slash_tldr(
        self,
        interaction: discord.Interaction,
        command: str,
        platform: str | None = None,
        language: str | None = None,
        show_short: bool | None = False,
        show_long: bool | None = True,
        show_both: bool | None = False,
    ) -> None:
        """Show a TLDR page for a CLI command."""
        await self._handle_tldr_command_slash(
            interaction=interaction,
            command_name=command,
            platform=platform,
            language=language,
            show_short=show_short or False,
            show_long=show_long or True,
            show_both=show_both or False,
        )

    @commands.command(name="tldr", aliases=["man"])
    @commands.guild_only()
    async def prefix_tldr(self, ctx: commands.Context[Tux], *, flags: TldrFlags):
        """Show a TLDR page for a CLI command.
        Command name can include spaces. Flags must come after the command name.

        Usage examples:
          >tldr git commit
          >tldr git -platform linux
          >tldr tar -show_both -platform osx
        """
        if not flags.command_words:
            await ctx.send_help(ctx.command)
            return

        command_name_str = " ".join(flags.command_words)
        logger.debug(
            f"[prefix_tldr] Command words from flags: {flags.command_words}, "
            f"Joined command_name_str: '{command_name_str}'",
        )
        logger.debug(
            f"[prefix_tldr] Flags received: platform='{flags.platform}', language='{flags.language}', "
            f"show_short='{flags.show_short}', show_long='{flags.show_long}', show_both='{flags.show_both}'",
        )

        render_short, render_long, render_both = False, False, False
        if flags.show_both:
            render_both = True
        elif flags.show_short:
            render_short = True
        else:
            render_long = flags.show_long

        await self._handle_tldr_command_prefix(
            ctx=ctx,
            command_name=command_name_str,
            platform=flags.platform,
            language=flags.language,
            show_short=render_short,
            show_long=render_long,
            show_both=render_both,
        )

    async def _handle_tldr_command_slash(
        self,
        interaction: discord.Interaction,
        command_name: str,
        platform: str | None = None,
        language: str | None = None,
        show_short: bool = False,
        show_long: bool = True,
        show_both: bool = False,
    ) -> None:
        """Handle the TLDR command for slash commands."""
        command_norm = TldrClient.normalize_page_name(command_name)
        chosen_language = language or self.default_language
        languages_to_try = TldrClient.get_language_priority(chosen_language, os.environ.get("LANGUAGE"))

        md = TldrClient.fetch_tldr_page(command_norm, languages_to_try, platform)

        display_platform = platform or TldrClient.detect_platform()

        if not md:
            description = TldrClient.not_found_message(command_norm)
            embed_title = f"TLDR for {command_norm}"
        else:
            description = TldrClient.format_tldr_for_discord(md, show_short, show_long, show_both)
            embed_title = f"TLDR for {command_norm} ({display_platform}/{chosen_language})"

        pages = TldrClient.split_long_text(description)
        if not pages:
            await interaction.response.send_message("Could not render TLDR page.", ephemeral=True)
            return

        view = TldrPaginatorView(pages, embed_title, interaction.user, self.bot) if len(pages) > 1 else None

        final_embed_title = f"{embed_title} (Page 1/{len(pages)})" if len(pages) > 1 else embed_title

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=interaction.user.name,
            user_display_avatar=interaction.user.display_avatar.url,
            title=final_embed_title,
            description=pages[0],
        )

        if view:
            await interaction.response.send_message(embed=embed, view=view)
            view.message = await interaction.original_response()
        else:
            await interaction.response.send_message(embed=embed)

    async def _handle_tldr_command_prefix(
        self,
        ctx: commands.Context[Tux],
        command_name: str,
        platform: str | None = None,
        language: str | None = None,
        show_short: bool = False,
        show_long: bool = True,
        show_both: bool = False,
    ) -> None:
        """Handle the TLDR command for prefix commands."""
        command_norm = TldrClient.normalize_page_name(command_name)
        chosen_language = language or self.default_language
        languages_to_try = TldrClient.get_language_priority(chosen_language, os.environ.get("LANGUAGE"))

        md = TldrClient.fetch_tldr_page(command_norm, languages_to_try, platform)

        display_platform = platform or TldrClient.detect_platform()

        if not md:
            description = TldrClient.not_found_message(command_norm)
            embed_title = f"TLDR for {command_norm}"
        else:
            description = TldrClient.format_tldr_for_discord(md, show_short, show_long, show_both)
            embed_title = f"TLDR for {command_norm} ({display_platform}/{chosen_language})"

        pages = TldrClient.split_long_text(description)
        if not pages:
            await ctx.send("Could not render TLDR page.")
            return

        view = TldrPaginatorView(pages, embed_title, ctx.author, self.bot) if len(pages) > 1 else None

        final_embed_title = f"{embed_title} (Page 1/{len(pages)})" if len(pages) > 1 else embed_title

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title=final_embed_title,
            description=pages[0],
        )

        if view:
            view.message = await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Tldr(bot))
