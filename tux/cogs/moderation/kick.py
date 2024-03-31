import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Kick(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @app_commands.command(name="kick", description="Kicks a member from the server.")
    @app_commands.describe(member="Which member to kick", reason="Reason for kick")
    async def kick(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ) -> None:
        logger.info(f"{interaction.user} kicked {member.display_name} in {interaction.channel}")

        response = await self.execute_kick(interaction, member, reason)

        await interaction.response.send_message(embed=response)

    async def execute_kick(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ) -> discord.Embed:
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title=f"Kicked {member.display_name}!",
                color=discord.Colour.gold(),
                description=f"Reason: `{reason or 'None provided'}`",
            )
            embed.set_footer(
                text=f"Kicked by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url,
            )

            logger.info(f"Successfully kicked {member.display_name}.")

        except discord.errors.Forbidden as error:
            embed = discord.Embed(
                title=f"Failed to kick {member.display_name}",
                color=discord.Colour.red(),
                description=f"Insufficient permissions. Error Info: `{error}`",
            )
            logger.error(f"Failed to kick {member.display_name}. Error: {error}")

        return embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Kick(bot))
