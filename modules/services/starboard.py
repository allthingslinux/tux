import contextlib
from datetime import UTC, datetime, timedelta

import discord
from bot import Tux
from database.controllers import DatabaseController
from discord.ext import commands
from loguru import logger
from ui.embeds import EmbedCreator, EmbedType
from utils import checks
from utils.converters import get_channel_safe
from utils.functions import generate_usage


class Starboard(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()
        self.starboard.usage = generate_usage(self.starboard)
        self.setup_starboard.usage = generate_usage(self.setup_starboard)
        self.remove_starboard.usage = generate_usage(self.remove_starboard)

    @commands.Cog.listener("on_raw_reaction_add")
    async def starboard_on_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await self.handle_starboard_reaction(payload)

    @commands.Cog.listener("on_raw_reaction_remove")
    async def starboard_on_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        await self.handle_starboard_reaction(payload)

    @commands.Cog.listener("on_raw_reaction_clear")
    async def starboard_on_reaction_clear(self, payload: discord.RawReactionClearEvent) -> None:
        await self.handle_reaction_clear(payload)

    @commands.Cog.listener("on_raw_reaction_clear_emoji")
    async def starboard_on_reaction_clear_emoji(self, payload: discord.RawReactionClearEmojiEvent) -> None:
        await self.handle_reaction_clear(payload, payload.emoji)

    @commands.hybrid_group(
        name="starboard",
    )
    @commands.guild_only()
    @checks.has_pl(5)
    async def starboard(self, ctx: commands.Context[Tux]) -> None:
        """
        Configure the starboard for this server.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("starboard")

    @starboard.command(
        name="setup",
        aliases=["s"],
    )
    @checks.has_pl(5)
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
                embed=EmbedCreator.create_embed(
                    bot=self.bot,
                    embed_type=EmbedCreator.ERROR,
                    user_name=ctx.author.name,
                    user_display_avatar=ctx.author.display_avatar.url,
                    title="Invalid Emoji",
                    description="Please use a single default Discord emoji.",
                ),
            )
            return

        if threshold < 1:
            await ctx.send(
                embed=EmbedCreator.create_embed(
                    bot=self.bot,
                    embed_type=EmbedCreator.ERROR,
                    user_name=ctx.author.name,
                    user_display_avatar=ctx.author.display_avatar.url,
                    title="Invalid Threshold",
                    description="Threshold must be at least 1.",
                ),
            )
            return

        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(
                embed=EmbedCreator.create_embed(
                    bot=self.bot,
                    embed_type=EmbedCreator.ERROR,
                    user_name=ctx.author.name,
                    user_display_avatar=ctx.author.display_avatar.url,
                    title="Permission Denied",
                    description=f"I don't have permission to send messages in {channel.mention}.",
                ),
            )
            return

        try:
            await self.db.starboard.create_or_update_starboard(ctx.guild.id, channel.id, emoji, threshold)

            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.INFO,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="Starboard Setup",
                description="Starboard configured successfully.",
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
    )
    @checks.has_pl(5)
    async def remove_starboard(self, ctx: commands.Context[Tux]) -> None:
        """
        Remove the starboard configuration for this server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        """

        assert ctx.guild

        try:
            result = await self.db.starboard.delete_starboard_by_guild_id(ctx.guild.id)

            embed = (
                EmbedCreator.create_embed(
                    bot=self.bot,
                    embed_type=EmbedCreator.INFO,
                    user_name=ctx.author.name,
                    user_display_avatar=ctx.author.display_avatar.url,
                    title="Starboard Removed",
                    description="Starboard configuration removed successfully.",
                )
                if result
                else EmbedCreator.create_embed(
                    bot=self.bot,
                    embed_type=EmbedCreator.ERROR,
                    user_name=ctx.author.name,
                    user_display_avatar=ctx.author.display_avatar.url,
                    title="No Starboard Found",
                    description="No starboard configuration found for this server.",
                )
            )

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error removing starboard configuration: {e}")
            await ctx.send(f"An error occurred while removing the starboard configuration: {e}")

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
        original_message : discord.Message`
            The original message.

        Returns
        -------
        discord.Message | None
            The existing starboard message or None if it does not exist.
        """

        assert original_message.guild

        try:
            starboard_message = await self.db.starboard_message.get_starboard_message_by_id(
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
            starboard = await self.db.starboard.get_starboard_by_guild_id(original_message.guild.id)
            if not starboard:
                return

            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.INFO,
                description=original_message.content,
                custom_color=discord.Color.gold(),
                message_timestamp=original_message.created_at,
                custom_author_text=original_message.author.display_name,
                custom_author_icon_url=original_message.author.avatar.url if original_message.author.avatar else None,
                custom_footer_text=f"{reaction_count} {starboard.starboard_emoji}",
                image_url=original_message.attachments[0].url if original_message.attachments else None,
            )
            embed.add_field(name="Source", value=f"[Jump to message]({original_message.jump_url})")

            starboard_message = await self.get_existing_starboard_message(starboard_channel, original_message)

            if starboard_message:
                if starboard_message.embeds:
                    existing_embed = starboard_message.embeds[0]
                    if existing_embed.footer != embed.footer:
                        await starboard_message.edit(embed=embed)
                    else:
                        return
            else:
                starboard_message = await starboard_channel.send(embed=embed)

            await self.db.starboard_message.create_or_update_starboard_message(
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

    async def handle_starboard_reaction(self, payload: discord.RawReactionActionEvent) -> None:
        """Handle starboard reaction add or remove"""
        if not payload.guild_id:
            return

        starboard = await self.db.starboard.get_starboard_by_guild_id(payload.guild_id)
        if not starboard or str(payload.emoji) != starboard.starboard_emoji:
            return

        channel = await get_channel_safe(self.bot, payload.channel_id)
        if channel is None:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
            reaction = discord.utils.get(message.reactions, emoji=starboard.starboard_emoji)
            reaction_count = reaction.count if reaction else 0

            if reaction:
                async for user in reaction.users():
                    if user.id == message.author.id:
                        reaction_count -= 1
                        with contextlib.suppress(Exception):
                            await message.remove_reaction(starboard.starboard_emoji, message.author)

            starboard_channel = channel.guild.get_channel(starboard.starboard_channel_id)
            if not isinstance(starboard_channel, discord.TextChannel):
                return

            if reaction_count >= starboard.starboard_threshold:
                await self.create_or_update_starboard_message(starboard_channel, message, reaction_count)

            else:
                existing_starboard_message = await self.get_existing_starboard_message(starboard_channel, message)
                if existing_starboard_message:
                    await existing_starboard_message.delete()

        except Exception as e:
            logger.error(f"Unexpected error in handle_starboard_reaction: {e}")

    async def handle_reaction_clear(
        self,
        payload: discord.RawReactionClearEvent | discord.RawReactionClearEmojiEvent,
        emoji: discord.PartialEmoji | None = None,
    ) -> None:
        """
        Handle reaction clear for all emojis or a specific emoji

        Parameters
        ----------
        payload : discord.RawReactionClearEvent | discord.RawReactionClearEmojiEvent
            The payload of the reaction clear event.
        emoji : discord.PartialEmoji | None
            The emoji to handle the reaction clear for.
        """
        if not payload.guild_id:
            return

        try:
            channel = self.bot.get_channel(payload.channel_id)
            if not isinstance(channel, discord.TextChannel):
                return

            message = await channel.fetch_message(payload.message_id)
            starboard = await self.db.starboard.get_starboard_by_guild_id(payload.guild_id)

            if not starboard or (emoji and str(emoji) != starboard.starboard_emoji):
                return

            starboard_channel = channel.guild.get_channel(starboard.starboard_channel_id)
            if not isinstance(starboard_channel, discord.TextChannel):
                return

            starboard_message = await self.get_existing_starboard_message(starboard_channel, message)
            if starboard_message:
                await starboard_message.delete()

        except Exception as e:
            logger.error(f"Error in handle_reaction_clear: {e}")


async def setup(bot: Tux) -> None:
    await bot.add_cog(Starboard(bot))
