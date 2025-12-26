"""
TLDR command integration for Discord.

This module provides TLDR (Too Long; Didn't Read) command documentation
lookup functionality, allowing users to search and view command summaries
from various platforms with interactive pagination.
"""

import asyncio
import contextlib

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.core.flags import TldrFlags
from tux.services.sentry import capture_exception_safe
from tux.services.wrappers.tldr import SUPPORTED_PLATFORMS, TldrClient
from tux.shared.functions import generate_usage
from tux.ui.embeds import EmbedCreator
from tux.ui.views.tldr import TldrPaginatorView


class Tldr(BaseCog):
    """Discord cog for TLDR command integration."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the TLDR cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)
        self.default_language: str = self.detect_bot_language()
        self.prefix_tldr.usage = generate_usage(self.prefix_tldr, TldrFlags)
        self._cache_checked = False
        self._cache_task: asyncio.Task[None] | None = None

    async def cog_load(self) -> None:
        """Schedule cache check when the cog is loaded (initial startup only)."""
        if self._cache_checked:
            logger.debug("Skipping cache check (hot reload detected)")
            return

        self._cache_task = asyncio.create_task(self._initialize_cache_async())
        logger.debug("Cache initialization scheduled")

    async def cog_unload(self) -> None:
        """Clean up resources when the cog is unloaded."""
        if self._cache_task and not self._cache_task.done():
            self._cache_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cache_task

    async def _initialize_cache_async(self) -> None:
        """Asynchronously initialize TLDR cache after event loop is ready."""
        try:
            logger.debug("Checking cache status")

            normalized_lang = (
                "en"
                if self.default_language.startswith("en")
                else self.default_language
            )
            languages_to_check = {normalized_lang, "en"}

            for lang_code in languages_to_check:
                if TldrClient.cache_needs_update(lang_code):
                    logger.info(f"Cache for '{lang_code}' needs update")
                    try:
                        result_msg = await asyncio.to_thread(
                            TldrClient.update_tldr_cache,
                            lang_code,
                        )
                        if result_msg.startswith("Failed"):
                            logger.error(
                                f"Cache update for '{lang_code}': {result_msg}",
                            )
                        else:
                            logger.debug(
                                f"Cache update for '{lang_code}': {result_msg}",
                            )
                    except Exception as e:
                        logger.error(
                            f"Exception during cache update for '{lang_code}': {e}",
                            exc_info=True,
                        )
                        capture_exception_safe(
                            e,
                            extra_context={
                                "tldr_cache_update": {
                                    "language": lang_code,
                                    "operation": "cache_update",
                                    "cache_needs_update": True,
                                },
                            },
                        )
                else:
                    logger.debug(f"Cache for '{lang_code}' is recent, skipping update")

            self._cache_checked = True
            logger.debug("Cache check completed")
        except Exception as e:
            logger.error(
                f"Critical error during cache initialization: {e}",
                exc_info=True,
            )

    def detect_bot_language(self) -> str:
        """
        Detect the bot's default language. For Discord bots, default to English.

        Returns
        -------
        str
            The language code (always "en" for this bot).
        """
        return "en"

    async def command_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """
        Autocomplete for the command parameter.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction triggering autocomplete.
        current : str
            Current input value.

        Returns
        -------
        list[app_commands.Choice[str]]
            List of command choices for autocomplete.
        """
        language_value: str | None = None
        platform_value: str | None = None

        with contextlib.suppress(AttributeError):
            if hasattr(interaction, "namespace") and interaction.namespace:
                language_value = interaction.namespace.language
                platform_value = interaction.namespace.platform
        final_language = language_value or self.default_language
        final_platform_for_list = platform_value or TldrClient.detect_platform()

        commands_to_show = TldrClient.list_tldr_commands(
            language=final_language,
            platform_filter=final_platform_for_list,
        )

        # Filter commands based on current input
        if not current:
            filtered_commands = [
                app_commands.Choice(name=cmd, value=cmd) for cmd in commands_to_show
            ]
        else:
            filtered_commands = [
                app_commands.Choice(name=cmd, value=cmd)
                for cmd in commands_to_show
                if current.lower() in cmd.lower()
            ]

        return filtered_commands[:25]

    async def platform_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """
        Autocomplete for the platform parameter.

        Returns
        -------
        list[app_commands.Choice[str]]
            List of platform choices for autocomplete.
        """
        choices = [
            app_commands.Choice(name=plat, value=plat)
            for plat in SUPPORTED_PLATFORMS
            if current.lower() in plat.lower()
        ]
        return choices[:25]

    async def language_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """
        Autocomplete for the language parameter.

        Returns
        -------
        list[app_commands.Choice[str]]
            List of language choices for autocomplete.
        """
        common_languages = [
            "en",
            "es",
            "fr",
            "de",
            "pt",
            "zh",
            "ja",
            "ko",
            "ru",
            "it",
            "nl",
            "pl",
            "tr",
        ]
        choices = [
            app_commands.Choice(name=lang, value=lang)
            for lang in common_languages
            if current.lower() in lang.lower()
        ]
        return choices[:25]

    @app_commands.command(name="tldr")
    @app_commands.guild_only()
    @app_commands.describe(
        command="The command to look up (e.g. tar, git-commit, etc)",
        platform="Platform (e.g. linux, osx, common)",
        language="Language code (e.g. en, es, fr)",
        show_short="Display shortform options over longform.",
        show_long="Display longform options over shortform.",
        show_both="Display both short and long options.",
    )
    @app_commands.autocomplete(
        platform=platform_autocomplete,
        language=language_autocomplete,
        command=command_autocomplete,
    )
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
        await self._handle_tldr_command(
            source=interaction,
            command_name=command,
            platform=platform,
            language=language,
            show_short=bool(show_short),
            show_long=bool(show_long) if show_long is not None else True,
            show_both=bool(show_both),
        )

    @commands.command(name="tldr", aliases=["man"])
    @commands.guild_only()
    async def prefix_tldr(
        self,
        ctx: commands.Context[Tux],
        command: str,
        *,
        flags: TldrFlags,
    ) -> None:
        """Show a TLDR page for a CLI command. If spaces are required, use hyphens instead.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        command : str
            The command to look up (e.g. tar, git-commit, etc).
        flags : TldrFlags
            The flags for the command. (platform: str | None, language: str | None, show_short: bool, show_long: bool, show_both: bool)
        """
        await self._handle_tldr_command(
            source=ctx,
            command_name=command,
            platform=flags.platform,
            language=flags.language,
            show_short=flags.show_short,
            show_long=flags.show_long,
            show_both=flags.show_both,
        )

    async def _handle_tldr_command(
        self,
        source: discord.Interaction | commands.Context[Tux],
        command_name: str,
        platform: str | None = None,
        language: str | None = None,
        show_short: bool = False,
        show_long: bool = True,
        show_both: bool = False,
    ) -> None:
        """Handle the TLDR command for both slash and prefix commands.

        Parameters
        ----------
        source : discord.Interaction | commands.Context[Tux]
            The interaction or context triggering the command.
        command_name : str
            The command name to look up.
        platform : str | None
            Platform preference.
        language : str | None
            Language preference.
        show_short : bool
            Show short options.
        show_long : bool
            Show long options.
        show_both : bool
            Show both options.
        """
        command_norm = TldrClient.normalize_page_name(command_name)
        chosen_language = language or self.default_language
        languages_to_try = TldrClient.get_language_priority(chosen_language)

        if result := TldrClient.fetch_tldr_page(
            command_norm,
            languages_to_try,
            platform,
        ):
            page_content, found_platform = result
            description = TldrClient.format_tldr_for_discord(
                page_content,
                show_short,
                show_long,
                show_both,
            )
            embed_title = (
                f"TLDR for {command_norm} ({found_platform}/{chosen_language})"
            )

            expected_platform = platform or TldrClient.detect_platform()
            if found_platform not in (expected_platform, "common"):
                warning_msg = (
                    f"\n\n⚠️ **Note**: This page is from `{found_platform}` platform, "
                    f"not `{expected_platform}` as expected."
                )
                description = warning_msg + "\n\n" + description
        else:
            description = TldrClient.not_found_message(command_norm)
            embed_title = f"TLDR for {command_norm}"

        pages = TldrClient.split_long_text(description)
        if not pages:
            error_msg = "Could not render TLDR page."
            if isinstance(source, discord.Interaction):
                await source.response.send_message(error_msg, ephemeral=True)
            else:
                await source.send(error_msg)
            return

        is_interaction = isinstance(source, discord.Interaction)
        user = source.user if is_interaction else source.author

        view = (
            TldrPaginatorView(pages, embed_title, user, self.bot)
            if len(pages) > 1
            else None
        )

        final_embed_title = (
            f"{embed_title} (Page 1/{len(pages)})" if len(pages) > 1 else embed_title
        )

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=user.name,
            user_display_avatar=user.display_avatar.url,
            title=final_embed_title,
            description=pages[0],
        )

        if view:
            if is_interaction:
                await source.response.send_message(embed=embed, view=view)
                view.message = await source.original_response()
            else:
                view.message = await source.send(embed=embed, view=view)
        elif is_interaction:
            await source.response.send_message(embed=embed)
        else:
            await source.send(embed=embed)


async def setup(bot: Tux) -> None:
    """Set up the Tldr cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Tldr(bot))
