import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseController
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
