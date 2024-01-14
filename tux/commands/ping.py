import discord
from discord.ext import commands

from tux.command_cog import CommandCog
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Ping(CommandCog):
    @commands.hybrid_command(name="ping")
    async def ping(self, ctx: commands.Context):
        """
        Checks the bot's latency.
        """

        message = await ctx.send("Pinging...")

        # Discord Python calculates the latency and records it in the bot instance
        # It's done every minute so this won't hurt performance
        discord_ping = round(self.bot.latency * 1000)

        # The time it takes for the message to be sent

        await message.edit(content=f"Pong! 🏓\nDiscord API latency: {discord_ping}ms")

        logger.info(f"{ctx.author} used {ctx.command} in {ctx.channel}.")

        if isinstance(ctx.channel, (discord.TextChannel | discord.VoiceChannel)):
            logger.audit(
                self.bot,
                title="Ping",
                description=f"{ctx.author.mention} used `{ctx.command}` in {ctx.channel.mention}.",
                color=0x00FF00,
            )
        else:
            logger.error(
                f"Failed to send message: Channel '{ctx.channel}' is not a text channel."
            )

        if isinstance(ctx.channel, (discord.TextChannel | discord.VoiceChannel)):
            fields = [
                ("User ID", str(ctx.author.id), False),
                ("Channel ID", str(ctx.channel.id), False),
            ]

            logger.audit(
                self.bot,
                title="Ping command used",
                description=f"{ctx.author.mention} used `{ctx.command}` in {ctx.channel.mention}.",
                color=0x00FF00,
                fields=fields,
                thumbnail_url="https://picsum.photos/200/300",
                image_url="https://fastly.picsum.photos/id/174/200/300.jpg?hmac=QaIDLHcDtfSD0nDbTHmEYRm7_bAbvyCafyheoeR2ZB4",
                author_name=str(ctx.author),
                author_url="https://picsum.photos/200/300",
                author_icon_url="https://picsum.photos/200/300",
                footer_text="This is a footer.",
                footer_icon_url="https://picsum.photos/200/300",
            )
        else:
            logger.error(
                f"Failed to send message: Channel '{ctx.channel}' is not a text channel."
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))
