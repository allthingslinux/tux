import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Ban(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod")
    @app_commands.command(name="ban", description="Bans a member from the server.")
    @app_commands.describe(member="Which member to ban", reason="Reason for ban")
    async def ban(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ) -> None:
        logger.info(f"{interaction.user} banned {member.display_name} in {interaction.channel}")

        response = await self.execute_ban(interaction, member, reason)

        await interaction.response.send_message(embed=response)

    async def execute_ban(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ) -> discord.Embed:
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title=f"Banned {member.display_name}!",
                color=discord.Colour.red(),
                description=f"Reason: `{reason or 'None provided'}`",
            )
            embed.set_footer(
                text=f"Banned by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url,
            )

            logger.info(f"Successfully banned {member.display_name}.")

        except discord.errors.Forbidden as error:
            embed = discord.Embed(
                title=f"Failed to ban {member.display_name}",
                color=discord.Colour.red(),
                description=f"Insufficient permissions. Error Info: `{error}`",
            )
            logger.error(f"Failed to ban {member.display_name}. Error: {error}")

        return embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ban(bot))
