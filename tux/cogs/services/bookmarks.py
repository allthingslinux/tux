import discord
from discord.ext import commands
from loguru import logger


class Bookmarks(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User) -> None:
        if str(reaction.emoji) == "🔖":
            message_link = f"https://discord.com/channels/{reaction.message.guild.id}/{reaction.message.channel.id}/{reaction.message.id}"
            message_contents = reaction.message.content
            message_attachments = reaction.message.attachments
            author_username = reaction.message.author.name
            try:
                if message_attachments:
                    attachments_info = "\n".join([attachment.url for attachment in message_attachments])
                    await user.send(
                        f"Bookmarked: {message_link}\nAuthor: {author_username}\nContent: {message_contents}\nAttachments: {attachments_info}",
                    )
                else:
                    await user.send(
                        f"Bookmarked: {message_link}\nAuthor: {author_username}\nContent: {message_contents}",
                    )
            except (discord.Forbidden, discord.HTTPException):
                logger.error(f"An error occurred while bookmarking {message_link} for {user}")
                return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bookmarks(bot))
