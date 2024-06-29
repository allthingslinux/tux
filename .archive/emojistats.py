import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseController
from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class EmojiStats(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_controller = DatabaseController().emojistats

    @app_commands.command(name="emojistats", description="List the top 10 most used emojis.")
    async def list_emoji_stats(self, interaction: discord.Interaction) -> None:
        """
        List the top 10 most used emojis.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object.
        """

        await interaction.response.defer()

        emoji_stats = await self.db_controller.get_all_emoji_stats()

        if not emoji_stats:
            await interaction.followup.send("No emoji stats found.")
            return

        emoji_stats = sorted(emoji_stats, key=lambda x: x.count, reverse=True)[:10]

        embed = EmbedCreator.create_info_embed(
            title="Emoji Stats",
            description="\n".join(
                [
                    f"{str(index + 1).zfill(2)}. {self.bot.get_emoji(emoji.emoji_id) or 'Unknown'} | count: {emoji.count}"
                    for index, emoji in enumerate(emoji_stats)
                ]
            ),
        )

        await interaction.followup.send(embed=embed)

    # TODO: make it not error out if the emoji isnt from the guild
    @commands.command(
        name="emojiinfo", description="Get information about an emoji. (put emoji as parameter)"
    )
    async def emoji_info(self, ctx: commands.Context[commands.Bot], emoji: discord.Emoji) -> None:
        """
        Get information about an emoji.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object.
        emoji : discord.Emoji
            The emoji to get information about.
        """

        # create custom embed
        embed = discord.Embed(
            title=f"Emoji Info for {emoji.name}",
            color=CONST.EMBED_STATE_COLORS["DEBUG"],
        )

        embed.add_field(name="Name", value=emoji.name, inline=True)
        embed.add_field(name="ID", value=emoji.id, inline=True)
        embed.add_field(name="URL", value=emoji.url, inline=False)
        # set the emoji image as the thumbnail
        embed.set_thumbnail(url=emoji.url)

        # get the emojis usage stats if it exists
        emoji_stats = await self.db_controller.get_emoji_stats(emoji.id)
        if emoji_stats:
            embed.add_field(name="Usage Count", value=emoji_stats.count, inline=True)
            # find how the emoji ranks in the guild
            emoji_stats = await self.db_controller.get_all_emoji_stats()
            emoji_stats = sorted(emoji_stats, key=lambda x: x.count, reverse=True)
            rank = next(
                (
                    index + 1
                    for index, emoji_stat in enumerate(emoji_stats)
                    if emoji_stat.emoji_id == emoji.id
                ),
                None,
            )
            embed.add_field(name="Rank", value=rank, inline=True)

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        When a message is sent in a guild.

        Parameters
        ----------
        message : discord.Message
            The message that was sent.
        """

        if message.author.bot or not message.guild:
            return

        # Get the emojis from the guild and check if any of them are in the message content
        if any(str(emoji) in message.content for emoji in message.guild.emojis):
            for emoji in message.guild.emojis:
                if str(emoji) in message.content:
                    await self.db_controller.increment_emoji_count_or_create(emoji.id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """
        When a reaction is added to a message.

        Parameters
        ----------
        payload : discord.RawReactionActionEvent
            The payload of the event.
        """

        if not self.bot.user:
            logger.error("Bot user not found. This should never happen.")
            return

        if payload.user_id == self.bot.user.id:
            return

        if not payload.guild_id:
            return

        if not payload.emoji.id:
            return

        # Check if the emoji is from the guild
        emoji = self.bot.get_emoji(payload.emoji.id)
        if not emoji or emoji.guild_id != payload.guild_id:
            return

        await self.db_controller.increment_emoji_count_or_create(emoji.id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EmojiStats(bot))
