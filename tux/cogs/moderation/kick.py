import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Kick(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="kick", description="Kicks a user from the server.")
    @app_commands.describe(member="Which member to kick", reason="Reason to kick member")
    async def kick(
        self, interaction: discord.Interaction, member: discord.Member, reason: str
    ) -> None:
        logger.info(
            f"{interaction.user} used the kick command in {interaction.channel} to kick user {member.display_name}."
        )
        try:
            await member.kick()
        except discord.errors.Forbidden as e:
            embed_error = discord.Embed(
                colour=discord.Colour.red(),
                title=f"Failed to kick {member.display_name}",
                description=f"`Error info: {e}`",
                timestamp=interaction.created_at,
            )
            embed_error.set_footer(
                text=f"Requested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar,
            )
            await interaction.response.send_message(embed=embed_error)
            return

        embed: discord.Embed = discord.Embed(
            title=f"Kicked {member.display_name}!",
            color=discord.Colour.gold(),
            timestamp=interaction.created_at,
            type="rich",
        )

        embed.add_field(
            name="Reason",
            value="`none provided`" if not reason else f"`{reason}`",
            inline=True,
        )
        embed.add_field(
            name="User",
            value=f"<@{member.id}>",
            inline=True,
        )

        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar,
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Kick(bot))
