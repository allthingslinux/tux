import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Warns(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @app_commands.command(name="warn", description="Warns a member in the server for a reason.")
    @app_commands.describe(member="Which member to warn", reason="Reason for warn")
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str | None = "No reason",
    ) -> None:
        logger.info(f"{interaction.user} just warned user {member} for {reason}")

        response = await self.execute_warn(interaction.user, member, reason)

        await interaction.response.send_message(embed=response)

    async def execute_warn(
        self, moderator: discord.Member, member: discord.Member, reason: str
    ) -> discord.Embed:
        try:
            # await add_infraction(moderator.id, member.id, "warn", reason, datetime.now()) TODO replace this with function that creates a warn
            embed = discord.Embed(
                title=f"Warned {member.display_name}!",
                color=discord.Colour.gold(),
                description=f"Reason: `{reason}`",
            )
            embed.set_footer(
                text=f"Warned by {moderator.display_name}",
                icon_url=moderator.display_avatar.url,
            )
        except Exception as error:
            embed = discord.Embed(
                title=f"Failed to warn {member.display_name}",
                color=discord.Colour.red(),
                description=f"Unknown error. Error Info: `{error}`",
            )
            logger.error(f"Failed to warn {member.display_name}. Error: {error}")

        return embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Warns(bot))
