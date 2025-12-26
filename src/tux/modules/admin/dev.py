"""Development and administrative commands for the Tux bot.

This module provides various administrative commands for bot management,
including command synchronization, emoji management, and system information.
"""

from pathlib import Path

import discord
from discord.ext import commands
from loguru import logger
from reactionmenu import ViewButton, ViewMenu

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.core.checks import requires_command_permission


class Dev(BaseCog):
    """Discord cog for development and administrative commands.

    This cog provides various administrative commands for bot management
    and development tasks, including command synchronization and emoji management.
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the Dev cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    def _resolve_cog_path(self, cog_name: str) -> str:
        """
        Resolve a short cog name to a full module path.

        This method attempts to resolve short names like "ping" to full paths
        like "tux.modules.utility.ping" or "tux.plugins.atl.mock" by recursively
        searching through both the modules and plugins directories (including all
        subdirectories). It also handles partial paths like "modules.utility.ping"
        by prepending "tux." as needed.

        Examples
        --------
        - "ping" → "tux.modules.utility.ping"
        - "mock" → "tux.plugins.atl.mock"
        - "modules.utility.ping" → "tux.modules.utility.ping"
        - "plugins.atl.mock" → "tux.plugins.atl.mock"
        - "tux.modules.utility.ping" → "tux.modules.utility.ping" (unchanged)
        - "something" → "tux.plugins.xyz.something" (if in plugins/xyz/)

        Parameters
        ----------
        cog_name : str
            The cog name to resolve (can be short or full path).

        Returns
        -------
        str
            The resolved full module path, or the original name if already a full path
            or if resolution fails.
        """
        # Handle different path formats
        if "." in cog_name:
            return cog_name if cog_name.startswith("tux.") else f"tux.{cog_name}"

        # Try to find the cog in modules and plugins directories
        tux_dir = Path(__file__).parent.parent.parent  # Go up to tux/

        # Search directories in order of priority: modules first, then plugins
        search_dirs = [
            tux_dir / "modules",  # tux/modules/
            tux_dir / "plugins",  # tux/plugins/
        ]

        for search_dir in search_dirs:
            # Search for the cog file recursively (handles nested subdirectories)
            for py_file in search_dir.rglob(f"{cog_name}.py"):
                # Convert path to module path
                try:
                    relative_path = py_file.relative_to(tux_dir)  # From tux/
                    return f"tux.{str(relative_path).replace('/', '.').replace('\\', '.')[:-3]}"
                except ValueError:
                    continue

        # If not found, return the original name (might be a full path already)
        return cog_name

    @commands.hybrid_group(
        name="dev",
        aliases=["d"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def dev(self, ctx: commands.Context[Tux]) -> None:
        """
        Dev related commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("dev")

    @dev.command(
        name="sync_tree",
        aliases=["st", "sync", "s"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def sync_tree(self, ctx: commands.Context[Tux], guild: discord.Guild) -> None:
        """
        Sync the app command tree.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        guild : discord.Guild
            The guild to sync application commands to.
        """
        assert ctx.guild

        # Copy the global tree to the guild
        self.bot.tree.copy_global_to(guild=ctx.guild)
        # Sync the guild tree
        await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send("Application command tree synced.")

    @dev.command(
        name="clear_tree",
        aliases=["ct", "clear", "c"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def clear_tree(self, ctx: commands.Context[Tux]) -> None:
        """
        Clear the app command tree.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        """
        assert ctx.guild

        # Clear the slash command tree for the guild.
        self.bot.tree.clear_commands(guild=ctx.guild)
        # Copy the global slash commands to the guild.
        self.bot.tree.copy_global_to(guild=ctx.guild)
        # Sync the slash command tree for the guild.
        await self.bot.tree.sync(guild=ctx.guild)

        await ctx.send("Slash command tree cleared.")

    @dev.group(
        name="emoji",
        aliases=["e"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def emoji(self, ctx: commands.Context[Tux]) -> None:
        """
        Emoji management commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("dev emoji")

    @emoji.command(
        name="sync",
        aliases=["s"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def sync_emojis(self, ctx: commands.Context[Tux]) -> None:
        """
        Synchronize emojis from the local assets directory to the application.

        This command:
        1. Scans the emoji assets directory
        2. Uploads any missing emojis to the application
        3. Reports which emojis were created and which were skipped

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        """
        try:
            async with ctx.typing():
                created, skipped = await self.bot.emoji_manager.sync_emojis()

                created_count = len(created)
                skipped_count = len(skipped)

                embed = discord.Embed(
                    title="Emoji Synchronization Results",
                    color=discord.Color.green()
                    if created_count > 0
                    else discord.Color.blue(),
                )

                embed.add_field(
                    name="Status",
                    value=f"✅ Created: **{created_count}**\n⏭️ Skipped/Failed: **{skipped_count}**",
                    inline=False,
                )

                if created_count > 0:
                    created_names = [e.name for e in created]
                    created_str = ", ".join(created_names[:10])
                    if len(created_names) > 10:
                        created_str += f" and {len(created_names) - 10} more"
                    embed.add_field(
                        name="Created Emojis",
                        value=created_str,
                        inline=False,
                    )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in sync_emojis command: {e}")
            await ctx.send(f"Error synchronizing emojis: {e}")

    @emoji.command(
        name="resync",
        aliases=["r"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def resync_emoji(self, ctx: commands.Context[Tux], emoji_name: str) -> None:
        """
        Resync a specific emoji from the local assets directory.

        This command:
        1. Deletes the existing emoji with the given name (if it exists)
        2. Creates a new emoji using the local file with the same name
        3. Reports the results

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        emoji_name : str
            The name of the emoji to resync.
        """
        try:
            async with ctx.typing():
                new_emoji = await self.bot.emoji_manager.resync_emoji(emoji_name)

                if new_emoji:
                    embed = discord.Embed(
                        title="Emoji Resync Successful",
                        description=f"Emoji `{emoji_name}` has been resynced successfully!",
                        color=discord.Color.green(),
                    )
                    embed.add_field(name="Emoji", value=str(new_emoji))
                    embed.set_thumbnail(url=new_emoji.url)
                else:
                    embed = discord.Embed(
                        title="Emoji Resync Failed",
                        description=f"Failed to resync emoji `{emoji_name}`. Check logs for details.",
                        color=discord.Color.red(),
                    )

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in resync_emoji command: {e}")
            await ctx.send(f"Error resyncing emoji: {e}")

    @emoji.command(
        name="delete_all",
        aliases=["da", "clear"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def delete_all_emojis(self, ctx: commands.Context[Tux]) -> None:
        """
        Delete all application emojis that match names from the emoji assets directory.

        This command:
        1. Scans the emoji assets directory for valid emoji names
        2. Deletes all application emojis with matching names
        3. Reports which emojis were deleted and which failed

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        """
        # Ask for confirmation before proceeding
        await ctx.send(
            "⚠️ **WARNING**: This will delete all application emojis matching the emoji assets directory.\n"
            "Are you sure you want to continue? (yes/no)",
        )

        def check(m: discord.Message) -> bool:
            """Check if a message is a valid confirmation response.

            Parameters
            ----------
            m : discord.Message
                The message to check.

            Returns
            -------
            bool
                True if the message is a valid 'yes' or 'no' response from the command author.
            """
            return (
                m.author == ctx.author
                and m.channel == ctx.channel
                and m.content.lower() in ["yes", "no"]
            )

        try:
            response = await self.bot.wait_for("message", check=check, timeout=30.0)

            if response.content.lower() != "yes":
                await ctx.send("Operation cancelled.")
                return

            async with ctx.typing():
                deleted, failed = await self.bot.emoji_manager.delete_all_emojis()

                deleted_count = len(deleted)
                failed_count = len(failed)

                embed = discord.Embed(
                    title="Emoji Deletion Results",
                    color=discord.Color.orange(),
                )

                embed.add_field(
                    name="Status",
                    value=f"🗑️ Deleted: **{deleted_count}**\n❌ Failed/Not Found: **{failed_count}**",
                    inline=False,
                )

                if deleted_count > 0:
                    deleted_str = ", ".join(deleted[:10])
                    if len(deleted) > 10:
                        deleted_str += f" and {len(deleted) - 10} more"
                    embed.add_field(
                        name="Deleted Emojis",
                        value=deleted_str,
                        inline=False,
                    )

                if failed_count > 0:
                    failed_str = ", ".join(failed[:10])
                    if len(failed) > 10:
                        failed_str += f" and {len(failed) - 10} more"
                    embed.add_field(
                        name="Failed Emoji Deletions",
                        value=failed_str,
                        inline=False,
                    )

            await ctx.send(embed=embed)
        except TimeoutError:
            await ctx.send("Confirmation timed out. Operation cancelled.")
        except Exception as e:
            logger.error(f"Error in delete_all_emojis command: {e}")
            await ctx.send(f"Error deleting emojis: {e}")

    @emoji.command(
        name="list",
        aliases=["ls", "l"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def list_emojis(self, ctx: commands.Context[Tux]) -> None:
        """
        List all emojis currently in the emoji manager's cache.

        This command:
        1. Shows all emojis in the bot's emoji cache
        2. Displays emoji count and names

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        """
        try:
            # Check if emoji manager is initialized by examining the cache
            if not self.bot.emoji_manager.cache:
                await ctx.send(
                    "Emoji manager cache is empty. It might not be initialized yet.",
                )
                return

            # Get all emojis and sort them by name
            emojis = sorted(self.bot.emoji_manager.cache.values(), key=lambda e: e.name)
            emoji_count = len(emojis)

            if emoji_count == 0:
                await ctx.send("No emojis found in the emoji manager's cache.")
                return

            # Create a ViewMenu for pagination

            menu = ViewMenu(
                ctx,
                menu_type=ViewMenu.TypeEmbed,
                all_can_click=True,
                delete_on_timeout=True,
            )

            # Paginate emojis
            emojis_per_page = 10

            for i in range(0, emoji_count, emojis_per_page):
                page_emojis = emojis[i : i + emojis_per_page]

                embed = discord.Embed(
                    title="Application Emojis",
                    description=f"Found **{emoji_count}** emojis in the emoji manager's cache.",
                    color=discord.Color.blue(),
                )

                # Add server info and footer
                if ctx.guild and ctx.guild.icon:
                    embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)

                embed.set_footer(
                    text=f"Page {i // emojis_per_page + 1}/{(emoji_count + emojis_per_page - 1) // emojis_per_page} • Requested by {ctx.author}",
                    icon_url=ctx.author.display_avatar.url,
                )

                # Create a table-like format with headers
                table_header = "\n**Emoji**\u2003\u2002**Reference**\n"
                embed.description = f"Found **{emoji_count}** emojis in the emoji manager's cache.{table_header}"

                for emoji in page_emojis:
                    # Format with consistent spacing (using unicode spaces for alignment)
                    emoji_display = str(emoji)
                    emoji_name = emoji.name
                    emoji_id = emoji.id

                    # Create copyable reference format
                    is_animated = getattr(emoji, "animated", False)
                    emoji_ref = (
                        f"<{'a' if is_animated else ''}:{emoji_name}:{emoji_id}>"
                    )

                    embed.description += (
                        f"{emoji_display}\u2003\u2003\u2003`{emoji_ref}`\n"
                    )

                menu.add_page(embed)

            # Add navigation buttons
            menu_buttons = [
                ViewButton(
                    style=discord.ButtonStyle.secondary,
                    custom_id=ViewButton.ID_GO_TO_FIRST_PAGE,
                    emoji="⏮️",
                ),
                ViewButton(
                    style=discord.ButtonStyle.secondary,
                    custom_id=ViewButton.ID_PREVIOUS_PAGE,
                    emoji="⏪",
                ),
                ViewButton(
                    style=discord.ButtonStyle.secondary,
                    custom_id=ViewButton.ID_NEXT_PAGE,
                    emoji="⏩",
                ),
                ViewButton(
                    style=discord.ButtonStyle.secondary,
                    custom_id=ViewButton.ID_GO_TO_LAST_PAGE,
                    emoji="⏭️",
                ),
            ]

            menu.add_buttons(menu_buttons)

            # Start the menu
            await menu.start()

        except Exception as e:
            logger.error(f"Error in list_emojis command: {e}")
            await ctx.send(f"Error listing emojis: {e}")

    @dev.command(
        name="load_cog",
        aliases=["lc", "load", "l"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def load_cog(self, ctx: commands.Context[Tux], *, cog: str) -> None:
        """
        Load a cog into the bot.

        This command supports automatic path resolution. You can use short names
        like "ping" which will be resolved to "tux.modules.utility.ping", or
        provide the full module path directly.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        cog : str
            The name of the cog to load (short name or full module path).
        """
        resolved_cog = self._resolve_cog_path(cog)
        try:
            await self.bot.load_extension(resolved_cog)
            await ctx.send(f"✅ Cog `{resolved_cog}` loaded successfully.")
            logger.info(f"Cog {resolved_cog} loaded by {ctx.author}")
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f"❌ Cog `{resolved_cog}` is already loaded.")
        except commands.ExtensionNotFound:
            await ctx.send(f"❌ Cog `{cog}` not found. (Resolved to: `{resolved_cog}`)")
        except commands.ExtensionFailed as e:
            await ctx.send(f"❌ Failed to load cog `{resolved_cog}`: {e.original}")
            logger.error(f"Failed to load cog {resolved_cog}: {e.original}")
        except Exception as e:
            await ctx.send(f"❌ Unexpected error loading cog `{resolved_cog}`: {e}")
            logger.error(f"Unexpected error loading cog {resolved_cog}: {e}")

    @dev.command(
        name="unload_cog",
        aliases=["uc", "unload", "u"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def unload_cog(self, ctx: commands.Context[Tux], *, cog: str) -> None:
        """
        Unload a cog from the bot.

        This command supports automatic path resolution. You can use short names
        like "ping" which will be resolved to "tux.modules.utility.ping", or
        provide the full module path directly.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        cog : str
            The name of the cog to unload (short name or full module path).
        """
        resolved_cog = self._resolve_cog_path(cog)
        try:
            await self.bot.unload_extension(resolved_cog)
            await ctx.send(
                f"✅ Cog `{resolved_cog}` unloaded successfully.",
                ephemeral=True,
            )
            logger.info(f"Cog {resolved_cog} unloaded by {ctx.author}")
        except commands.ExtensionNotLoaded:
            await ctx.send(f"❌ Cog `{resolved_cog}` is not loaded.")
        except Exception as e:
            await ctx.send(f"❌ Unexpected error unloading cog `{resolved_cog}`: {e}")
            logger.error(f"Unexpected error unloading cog {resolved_cog}: {e}")

    @dev.command(
        name="reload_cog",
        aliases=["rc", "reload", "r"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def reload_cog(self, ctx: commands.Context[Tux], *, cog: str) -> None:
        """
        Reload a cog in the bot.

        This command supports automatic path resolution. You can use short names
        like "ping" which will be resolved to "tux.modules.utility.ping", or
        provide the full module path directly.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        cog : str
            The name of the cog to reload (short name or full module path).
        """
        resolved_cog = self._resolve_cog_path(cog)
        try:
            await self.bot.reload_extension(resolved_cog)
            await ctx.send(
                f"✅ Cog `{resolved_cog}` reloaded successfully.",
                ephemeral=True,
            )
            logger.info(f"Cog {resolved_cog} reloaded by {ctx.author}")
        except commands.ExtensionNotLoaded:
            await ctx.send(f"❌ Cog `{resolved_cog}` is not loaded.")
        except commands.ExtensionFailed as e:
            await ctx.send(f"❌ Failed to reload cog `{resolved_cog}`: {e.original}")
            logger.error(f"Failed to reload cog {resolved_cog}: {e.original}")
        except Exception as e:
            await ctx.send(f"❌ Unexpected error reloading cog `{resolved_cog}`: {e}")
            logger.error(f"Unexpected error reloading cog {resolved_cog}: {e}")

    @dev.command(
        name="stop",
        aliases=["shutdown"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def stop(self, ctx: commands.Context[Tux]) -> None:
        """
        Stop the bot. If Tux is running with Docker Compose, this will restart the container.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        """
        await ctx.send(
            "Stopping the bot...\n-# Note: if Tux is running with Docker Compose, this will restart the container.",
        )

        await self.bot.shutdown()


async def setup(bot: Tux) -> None:
    """Set up the Dev cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Dev(bot))
