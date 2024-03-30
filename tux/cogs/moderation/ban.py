import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Ban(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ban", description="Bans a user from the server.")
    @app_commands.describe(member="Which member to ban", reason="Reason to ban member")
    async def ban(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ) -> None:
        logger.info(
            f"{interaction.user} used the ban command in {interaction.channel} to ban user {member.display_name}."
        )

        try:
            await member.ban(reason=reason)
            embed: discord.Embed = discord.Embed(
                title=f"Banned {member.display_name}!",
                color=discord.Colour.red(),
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

        # You don't have permission
        except discord.errors.Forbidden as e:
            embed_error = discord.Embed(
                colour=discord.Colour.red(),
                title=f"Failed to ban {member.display_name}",
                description=f"tldr: You don't have permission\n`Error info: {e}`",
                timestamp=interaction.created_at,
            )
            embed_error.set_footer(
                text=f"Requested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar,
            )
            await interaction.response.send_message(embed=embed_error)
            return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ban(bot))
