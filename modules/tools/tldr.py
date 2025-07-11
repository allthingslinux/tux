import contextlib

import discord
from bot import Tux
from discord import app_commands
from discord.ext import commands
from loguru import logger
from ui.embeds import EmbedCreator
from ui.views.tldr import TldrPaginatorView
from utils.flags import TldrFlags
from utils.functions import generate_usage
from wrappers.tldr import SUPPORTED_PLATFORMS, TldrClient


class Tldr(commands.Cog):
    """Discord cog for TLDR command integration."""

    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.default_language: str = self.detect_bot_language()
        self.prefix_tldr.usage = generate_usage(self.prefix_tldr, TldrFlags)
        self._cache_checked = False  # Track if cache has been checked

    async def cog_load(self):
        """Check cache age and update if necessary when the cog is loaded (initial startup only)."""

        # Skip cache checks during hot reloads - only check on initial startup
        if self._cache_checked:
            logger.debug("TLDR Cog: Skipping cache check (hot reload detected)")
            return

        logger.debug("TLDR Cog: Checking cache status...")

        # Normalize detected language before adding to set
        normalized_default_lang = self.default_language
        if normalized_default_lang.startswith("en") and normalized_default_lang != "en":
            normalized_default_lang = "en"  # Treat en_US, en_GB as 'en' for tldr pages

        languages_to_check = {normalized_default_lang, "en"}

        for lang_code in languages_to_check:
            if TldrClient.cache_needs_update(lang_code):
                logger.info(f"TLDR Cog: Cache for '{lang_code}' is older than 168 hours, updating...")
                try:
                    result_msg = await self.bot.loop.run_in_executor(None, TldrClient.update_tldr_cache, lang_code)
                    if "Failed" in result_msg:
                        logger.error(f"TLDR Cog: Cache update for '{lang_code}' - {result_msg}")
                    else:
                        logger.debug(f"TLDR Cog: Cache update for '{lang_code}' - {result_msg}")
                except Exception as e:
                    logger.error(f"TLDR Cog: Exception during cache update for '{lang_code}': {e}", exc_info=True)
            else:
                logger.debug(f"TLDR Cog: Cache for '{lang_code}' is recent, skipping update.")

        self._cache_checked = True
        logger.debug("TLDR Cog: Cache check completed.")

    def detect_bot_language(self) -> str:
        """Detect the bot's default language. For Discord bots, default to English."""
        return "en"

    async def command_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for the command parameter."""
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
            filtered_commands = [app_commands.Choice(name=cmd, value=cmd) for cmd in commands_to_show]
        else:
            filtered_commands = [
                app_commands.Choice(name=cmd, value=cmd) for cmd in commands_to_show if current.lower() in cmd.lower()
            ]

        return filtered_commands[:25]

    async def platform_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for the platform parameter."""
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
        """Autocomplete for the language parameter."""
        common_languages = ["en", "es", "fr", "de", "pt", "zh", "ja", "ko", "ru", "it", "nl", "pl", "tr"]
        choices = [
            app_commands.Choice(name=lang, value=lang) for lang in common_languages if current.lower() in lang.lower()
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
        render_short, render_long, render_both = False, False, False

        if flags.show_both:
            render_both = True
        elif flags.show_short:
            render_short = True
        else:
            render_long = flags.show_long

        await self._handle_tldr_command_prefix(
            ctx=ctx,
            command_name=command,
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
        languages_to_try = TldrClient.get_language_priority(chosen_language)

        if result := TldrClient.fetch_tldr_page(command_norm, languages_to_try, platform):
            page_content, found_platform = result
            description = TldrClient.format_tldr_for_discord(page_content, show_short, show_long, show_both)
            embed_title = f"TLDR for {command_norm} ({found_platform}/{chosen_language})"

            # Add warning if page found on different platform than requested/detected
            expected_platform = platform or TldrClient.detect_platform()
            if found_platform not in (expected_platform, "common"):
                warning_msg = f"\n\n⚠️ **Note**: This page is from `{found_platform}` platform, not `{expected_platform}` as expected."
                description = warning_msg + "\n\n" + description

        else:
            description = TldrClient.not_found_message(command_norm)
            embed_title = f"TLDR for {command_norm}"
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
        languages_to_try = TldrClient.get_language_priority(chosen_language)

        if result := TldrClient.fetch_tldr_page(command_norm, languages_to_try, platform):
            page_content, found_platform = result
            description = TldrClient.format_tldr_for_discord(page_content, show_short, show_long, show_both)
            embed_title = f"TLDR for {command_norm} ({found_platform}/{chosen_language})"

            # Add warning if page found on different platform than requested/detected
            expected_platform = platform or TldrClient.detect_platform()
            if found_platform not in (expected_platform, "common"):
                warning_msg = f"\n\n⚠️ **Note**: This page is from `{found_platform}` platform, not `{expected_platform}` as expected."
                description = warning_msg + "\n\n" + description

        else:
            description = TldrClient.not_found_message(command_norm)
            embed_title = f"TLDR for {command_norm}"
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
