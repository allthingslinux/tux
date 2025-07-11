import discord
from bot import Tux
from discord.ext import commands
from loguru import logger
from reactionmenu import ViewButton, ViewMenu
from utils import checks
from utils.functions import generate_usage


class Dev(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.sync_tree.usage = generate_usage(self.sync_tree)
        self.clear_tree.usage = generate_usage(self.clear_tree)
        self.load_cog.usage = generate_usage(self.load_cog)
        self.unload_cog.usage = generate_usage(self.unload_cog)
        self.reload_cog.usage = generate_usage(self.reload_cog)
        self.stop.usage = generate_usage(self.stop)
        self.sync_emojis.usage = generate_usage(self.sync_emojis)
        self.resync_emoji.usage = generate_usage(self.resync_emoji)
        self.delete_all_emojis.usage = generate_usage(self.delete_all_emojis)

    @commands.hybrid_group(
        name="dev",
        aliases=["d"],
    )
    @commands.guild_only()
    @checks.has_pl(8)
    async def dev(self, ctx: commands.Context[Tux]) -> None:
        """
        Dev related commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        Raises
        ------
        commands.MissingPermissions
            If the user does not have the required permissions
        commands.CommandInvokeError
            If the subcommand is not found.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send_help("dev")

    @dev.command(
        name="sync_tree",
        aliases=["st", "sync", "s"],
    )
    @commands.guild_only()
    @checks.has_pl(8)
    async def sync_tree(self, ctx: commands.Context[Tux], guild: discord.Guild) -> None:
        """
        Syncs the app command tree.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        guild : discord.Guild
            The guild to sync application commands to.

        Raises
        ------
        commands.MissingRequiredArgument
            If a guild is not specified.
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
    @checks.has_pl(8)
    async def clear_tree(self, ctx: commands.Context[Tux]) -> None:
        """
        Clears the app command tree.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.

        Raises
        ------
        commands.MissingPermissions
            If the user does not have the required permissions.
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
        aliases=["em"],
    )
    @commands.guild_only()
    @checks.has_pl(8)
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
    @checks.has_pl(8)
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
                    color=discord.Color.green() if created_count > 0 else discord.Color.blue(),
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
    @checks.has_pl(8)
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
    @checks.has_pl(8)
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
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

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
    @checks.has_pl(8)
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
            if len(self.bot.emoji_manager.cache) == 0:
                await ctx.send("Emoji manager cache is empty. It might not be initialized yet.")
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
                    emoji_ref = f"<{'a' if is_animated else ''}:{emoji_name}:{emoji_id}>"

                    embed.description += f"{emoji_display}\u2003\u2003\u2003`{emoji_ref}`\n"

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
    @checks.has_pl(8)
    async def load_cog(self, ctx: commands.Context[Tux], *, cog: str) -> None:
        """
        Loads a cog into the bot.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        cog : str
            The name of the cog to load.
        """
        await self.bot.load_extension(cog)
        await ctx.send(f"Cog {cog} loaded.")
        logger.info(f"Cog {cog} loaded.")

    @dev.command(
        name="unload_cog",
        aliases=["uc", "unload", "u"],
    )
    @commands.guild_only()
    @checks.has_pl(8)
    async def unload_cog(self, ctx: commands.Context[Tux], *, cog: str) -> None:
        """
        Unloads a cog from the bot.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        cog : str
            The name of the cog to unload.
        """
        await self.bot.unload_extension(cog)
        logger.info(f"Cog {cog} unloaded.")
        await ctx.send(f"Cog {cog} unloaded.", ephemeral=True, delete_after=30)

    @dev.command(
        name="reload_cog",
        aliases=["rc", "reload", "r"],
    )
    @commands.guild_only()
    @checks.has_pl(8)
    async def reload_cog(self, ctx: commands.Context[Tux], *, cog: str) -> None:
        """
        Reloads a cog in the bot.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        cog : str
            The name of the cog to reload.
        """
        await self.bot.unload_extension(cog)
        await self.bot.load_extension(cog)
        await ctx.send(f"Cog {cog} reloaded.", ephemeral=True, delete_after=30)
        logger.info(f"Cog {cog} reloaded.")

    @dev.command(
        name="stop",
    )
    @commands.guild_only()
    @checks.has_pl(8)
    async def stop(self, ctx: commands.Context[Tux]) -> None:
        """
        Stops the bot. If Tux is running with Docker Compose, this will restart the container.

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
    await bot.add_cog(Dev(bot))
