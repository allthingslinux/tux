from datetime import UTC, datetime, timedelta

import discord
import emojis
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.database.controllers.starboard import StarboardController, StarboardMessageController
from tux.utils import checks


class Starboard(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.starboard_controller = StarboardController()
        self.starboard_message_controller = StarboardMessageController()

    @commands.hybrid_group(
        name="starboard",
        usage="starboard <subcommand>",
        description="Configure the starboard for this server",
    )
    @commands.guild_only()
    @checks.has_pl(5)  # admin & up
    async def starboard(self, ctx: commands.Context[Tux]) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help("starboard")

    @starboard.command(
        name="setup",
        aliases=["s"],
        usage="starboard setup <channel> <emoji> <threshold>",
        description="Configure the starboard for this server",
    )
    @commands.has_permissions(manage_guild=True)
    async def configure_starboard(
        self,
        ctx: commands.Context[Tux],
        channel: discord.TextChannel,
        emoji: str,
        threshold: int,
    ) -> None:
        """
        Configure the starboard for this server.

        Parameters
        ----------
        channel: discord.TextChannel
            The channel to configure the starboard for
        emoji: str
            The emoji to use for the starboard
        threshold: int
            The threshold for the starboard
        """
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return

        try:
            if not emojis.count(emoji, unique=True) or emojis.count(emoji, unique=True) > 1:  # type: ignore
                await ctx.send("Invalid emoji. Please use a single default Discord emoji.")
                return

            if threshold < 1:
                await ctx.send("Threshold must be at least 1.")
                return

            if not channel.permissions_for(ctx.guild.me).send_messages:
                await ctx.send(f"I don't have permission to send messages in {channel.mention}.")
                return

            await self.starboard_controller.create_or_update_starboard(ctx.guild.id, channel.id, emoji, threshold)
            await ctx.send(
                f"Starboard configured successfully. Channel: {channel.mention}, Emoji: {emoji}, Threshold: {threshold}",
            )
        except Exception as e:
            logger.error(f"Error configuring starboard: {e!s}")
            await ctx.send(f"An error occurred while configuring the starboard: {e!s}")

    @starboard.command(
        name="remove",
        aliases=["r"],
        usage="starboard remove",
        description="Remove the starboard configuration for this server",
    )
    @commands.has_permissions(manage_guild=True)
    async def remove_starboard(self, ctx: commands.Context[Tux]) -> None:
        """
        Remove the starboard configuration for this server.

        Parameters
        ----------
        ctx: commands.Context[Tux]
            The context of the command
        """
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return

        try:
            result = await self.starboard_controller.delete_starboard_by_guild_id(ctx.guild.id)
            if result:
                await ctx.send("Starboard configuration removed successfully.")
            else:
                await ctx.send("No starboard configuration found for this server.")
        except Exception as e:
            logger.error(f"Error removing starboard configuration: {e!s}")
            await ctx.send(f"An error occurred while removing the starboard configuration: {e!s}")

    @commands.Cog.listener("on_raw_reaction_add")
    async def starboard_check(self, payload: discord.RawReactionActionEvent) -> None:
        user_id = payload.user_id
        reaction = payload.emoji
        channel = self.bot.get_channel(payload.channel_id)

        assert isinstance(channel, discord.TextChannel)
        message = await channel.fetch_message(payload.message_id)

        if not message.guild or not user_id:
            return

        try:
            starboard = await self.starboard_controller.get_starboard_by_guild_id(message.guild.id)
            if not starboard:
                return

            if str(reaction) != starboard.starboard_emoji:
                logger.debug(
                    f"Reaction emoji {reaction} does not match starboard emoji {starboard.starboard_emoji}",
                )
                return

            # The message author cannot star their own message
            if message.author.id == user_id:
                logger.debug(f"User {user_id} tried to star their own message")
                return

            reaction_count = sum(r.count for r in message.reactions if str(r.emoji) == starboard.starboard_emoji)

            if reaction_count >= starboard.starboard_threshold:
                starboard_channel = message.guild.get_channel(starboard.starboard_channel_id)
                logger.info(f"Starboard channel: {starboard_channel}")

                if not isinstance(starboard_channel, discord.TextChannel):
                    logger.error(
                        f"Starboard channel {starboard.starboard_channel_id} not found or is not a text channel",
                    )
                    return

                await self.create_or_update_starboard_message(starboard_channel, message, reaction_count)
        except Exception as e:
            logger.error(f"Error in starboard_check: {e!s}")

    async def get_existing_starboard_message(
        self,
        starboard_channel: discord.TextChannel,
        original_message: discord.Message,
    ) -> discord.Message | None:
        assert original_message.guild
        try:
            starboard_message = await self.starboard_message_controller.get_starboard_message_by_id(
                original_message.id,
                original_message.guild.id,
            )
            logger.info(f"Starboard message: {starboard_message}")
            if starboard_message:
                return await starboard_channel.fetch_message(starboard_message.starboard_message_id)
        except Exception as e:
            logger.error(f"Error while fetching starboard message: {e!s}")

        return None

    async def create_or_update_starboard_message(
        self,
        starboard_channel: discord.TextChannel,
        original_message: discord.Message,
        reaction_count: int,
    ) -> None:
        if not original_message.guild:
            logger.error("Original message has no guild")
            return

        try:
            starboard = await self.starboard_controller.get_starboard_by_guild_id(original_message.guild.id)
            assert starboard

            embed = discord.Embed(
                description=original_message.content,
                color=discord.Color.gold(),
                timestamp=original_message.created_at,
            )
            embed.set_author(
                name=original_message.author.display_name,
                icon_url=original_message.author.avatar.url if original_message.author.avatar else None,
            )
            embed.add_field(name="Source", value=f"[Jump to message]({original_message.jump_url})")
            embed.set_footer(text=f"{reaction_count} {starboard.starboard_emoji}")

            if original_message.attachments:
                embed.set_image(url=original_message.attachments[0].url)

            starboard_message = await self.get_existing_starboard_message(starboard_channel, original_message)

            if starboard_message:
                await starboard_message.edit(embed=embed)
            else:
                starboard_message = await starboard_channel.send(embed=embed)

            # Create or update the starboard message entry in the database
            await self.starboard_message_controller.create_or_update_starboard_message(
                message_id=original_message.id,
                message_content=original_message.content,
                message_expires_at=datetime.now(UTC) + timedelta(days=30),
                message_channel_id=original_message.channel.id,
                message_user_id=original_message.author.id,
                message_guild_id=original_message.guild.id,
                star_count=reaction_count,
                starboard_message_id=starboard_message.id,
            )

        except Exception as e:
            logger.error(f"Error while creating or updating starboard message: {e!s}")


async def setup(bot: Tux) -> None:
    await bot.add_cog(Starboard(bot))
