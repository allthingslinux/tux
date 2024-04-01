import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Warn(commands.Cog):
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

        moderator: discord.Member | discord.User = interaction.user

        if interaction.guild:
            moderator = await interaction.guild.fetch_member(interaction.user.id)

        response = await self.execute_warn(
            interaction, moderator, member, reason or "None provided"
        )

        await interaction.response.send_message(embed=response)

    async def execute_warn(
        self,
        interaction: discord.Interaction,
        moderator: discord.Member | discord.User,
        member: discord.Member,
        reason: str,
    ) -> discord.Embed:
        try:
            # TODO Replace this with function that creates a warn
            # await add_infraction(moderator.id, member.id, "warn", reason, datetime.now())
            embed = discord.Embed(
                title=f"Warned {member.display_name}!",
                color=discord.Colour.gold(),
                description=f"Reason: `{reason}`",
                timestamp=interaction.created_at,
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
                timestamp=interaction.created_at,
            )
            logger.error(f"Failed to warn {member.display_name}. Error: {error}")

        return embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Warn(bot))
