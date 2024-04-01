import datetime

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class TimeOut(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="timeout", description="Timeout a user")
    @app_commands.describe(
        member="Which member to timeout",
        days="Days of timeout",
        hours="Hours of timeout",
        minutes="Minutes of timeout",
        seconds="Seconds of timeout",
        reason="Reason to timeout member",
    )
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        reason: str | None = None,
    ) -> None:
        logger.info(
            f"{interaction.user} used the timeout command to timeout {member}",
        )
        duration = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        try:
            await member.timeout(duration, reason=reason)
            embed = discord.Embed(
                color=discord.Color.red(),
                title=f"User {member.display_name} timed out",
                description=f"Reason: {reason if reason else '`None provided`'}",
                timestamp=interaction.created_at,
            )
            embed.add_field(
                name="User",
                value=f"<@{member.id}>",
                inline=True,
            )
            embed.add_field(
                name="Duration",
                value=duration,
                inline=True,
            )
            embed.set_footer(
                text=f"Requested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar,
            )
            await interaction.response.send_message(embed=embed)
        except discord.errors.Forbidden as e:
            logger.error("")
            embed_error = discord.Embed(
                colour=discord.Colour.red(),
                title=f"Failed to timeout {member.display_name}",
                description=f"`Error info: {e}`",
                timestamp=interaction.created_at,
            )
            embed_error.set_footer(
                text=f"Requested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar,
            )
            await interaction.response.send_message(embed=embed_error)
            return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TimeOut(bot))
