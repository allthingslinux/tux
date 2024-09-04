from datetime import UTC, datetime, timedelta

import discord
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.database.controllers.starboard import StarboardController, StarboardMessageController
from tux.utils import checks
from tux.utils.embeds import EmbedCreator


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
    @checks.has_pl(5)
    async def starboard(self, ctx: commands.Context[Tux]) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help("starboard")

    @starboard.command(
        name="setup",
        aliases=["s"],
        usage="starboard setup <channel> <emoji> <threshold>",
    )
    @commands.has_permissions(manage_guild=True)
    async def setup_starboard(
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
        channel : discord.TextChannel
            The channel to use for the starboard.
        emoji : str
            The emoji to use for the starboard.
        threshold : int
            The number of reactions required to trigger the starboard.
        """

        assert ctx.guild

        if len(emoji) != 1 or not emoji.isprintable():
            await ctx.send(
                embed=EmbedCreator.create_error_embed(
                    title="Invalid Emoji",
                    description="Please use a single default Discord emoji.",
                    ctx=ctx,
                ),
            )
            return

        if threshold < 1:
            await ctx.send(
                embed=EmbedCreator.create_error_embed(
                    title="Invalid Threshold",
                    description="Threshold must be at least 1.",
                    ctx=ctx,
                ),
            )
            return

        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(
                embed=EmbedCreator.create_error_embed(
                    title="Permission Denied",
                    description=f"I don't have permission to send messages in {channel.mention}.",
                    ctx=ctx,
                ),
            )
            return

        try:
            await self.starboard_controller.create_or_update_starboard(ctx.guild.id, channel.id, emoji, threshold)

            embed = EmbedCreator.create_success_embed(
                title="Starboard Setup",
                description="Starboard configured successfully.",
                ctx=ctx,
            )
            embed.add_field(name="Channel", value=channel.mention)
            embed.add_field(name="Emoji", value=emoji)
            embed.add_field(name="Threshold", value=threshold)

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error configuring starboard: {e}")
            await ctx.send(f"An error occurred while configuring the starboard: {e}")

    @starboard.command(
        name="remove",
        aliases=["r"],
        usage="starboard remove",
    )
    @commands.has_permissions(manage_guild=True)
    async def remove_starboard(self, ctx: commands.Context[Tux]) -> None:
        """
        Remove the starboard configuration for this server.
        """

        assert ctx.guild

        try:
            result = await self.starboard_controller.delete_starboard_by_guild_id(ctx.guild.id)

            embed = (
                EmbedCreator.create_success_embed(
                    title="Starboard Removed",
                    description="Starboard configuration removed successfully.",
                    ctx=ctx,
                )
                if result
                else EmbedCreator.create_error_embed(
                    title="No Starboard Found",
                    description="No starboard configuration found for this server.",
                    ctx=ctx,
                )
            )

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error removing starboard configuration: {e}")
            await ctx.send(f"An error occurred while removing the starboard configuration: {e}")

    @commands.Cog.listener("on_raw_reaction_add")
    async def starboard_check(self, payload: discord.RawReactionActionEvent) -> None:
        """
        Check if a message should be added to the starboard

        Parameters
        ----------
        payload : discord.RawReactionActionEvent
            The payload of the reaction event.
        """

        if not payload.guild_id or not payload.member:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
            if message.author.id == payload.user_id:
                return

            starboard = await self.starboard_controller.get_starboard_by_guild_id(payload.guild_id)
            if not starboard or str(payload.emoji) != starboard.starboard_emoji:
                return

            reaction_count = sum(r.count for r in message.reactions if str(r.emoji) == starboard.starboard_emoji)

            if reaction_count >= starboard.starboard_threshold:
                starboard_channel = channel.guild.get_channel(starboard.starboard_channel_id)

                if not isinstance(starboard_channel, discord.TextChannel):
                    logger.error(
                        f"Starboard channel {starboard.starboard_channel_id} not found or is not a text channel",
                    )
                    return

                await self.create_or_update_starboard_message(starboard_channel, message, reaction_count)

        except Exception as e:
            logger.error(f"Error in starboard_check: {e}")

    async def get_existing_starboard_message(
        self,
        starboard_channel: discord.TextChannel,
        original_message: discord.Message,
    ) -> discord.Message | None:
        """
        Get the existing starboard message for a given original message.

        Parameters
        ----------
        starboard_channel : discord.TextChannel
            The starboard channel.
        original_message : discord.Message
            The original message.
        """

        assert original_message.guild

        try:
            starboard_message = await self.starboard_message_controller.get_starboard_message_by_id(
                original_message.id,
                original_message.guild.id,
            )

            return (
                await starboard_channel.fetch_message(starboard_message.starboard_message_id)
                if starboard_message
                else None
            )

        except Exception as e:
            logger.error(f"Error while fetching starboard message: {e}")

        return None

    async def create_or_update_starboard_message(
        self,
        starboard_channel: discord.TextChannel,
        original_message: discord.Message,
        reaction_count: int,
    ) -> None:
        """
        Create or update a starboard message.

        Parameters
        ----------
        starboard_channel : discord.TextChannel
            The starboard channel.
        original_message : discord.Message
            The original message.
        reaction_count : int
            The number of reactions on the original message.
        """

        if not original_message.guild:
            logger.error("Original message has no guild")
            return

        try:
            starboard = await self.starboard_controller.get_starboard_by_guild_id(original_message.guild.id)
            if not starboard:
                return

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
            logger.error(f"Error while creating or updating starboard message: {e}")


async def setup(bot: Tux) -> None:
    await bot.add_cog(Starboard(bot))
