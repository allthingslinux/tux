import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Unban(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @app_commands.command(name="unban", description="Unbans a member from the server.")
    @app_commands.describe(
        username_or_id="The username of the member to unban", reason="Reason for unban"
    )
    async def unban(
        self, interaction: discord.Interaction, username_or_id: str, reason: str | None = None
    ) -> None:
        if interaction.guild is None:
            return

        banned_users = [ban.user async for ban in interaction.guild.bans()]

        try:
            user_id = int(username_or_id)
            user_to_unban = discord.utils.get(banned_users, id=user_id)
        except ValueError:
            user_to_unban = discord.utils.find(lambda u: u.name == username_or_id, banned_users)

        if user_to_unban is None:
            await self.send_error_message(
                interaction, "No banned user matches the provided username/ID"
            )
            return

        logger.info(
            f"{interaction.user} used the unban command in {interaction.channel} to unban user {user_to_unban.display_name}."
        )

        try:
            await interaction.guild.unban(user_to_unban, reason=reason)
            await interaction.response.send_message(
                embed=self.create_success_embed(
                    interaction, user_to_unban, reason or "None provided"
                )
            )
        except discord.HTTPException as e:
            await self.send_error_message(
                interaction, f"Failed to unban {user_to_unban.display_name}. Error info: {e}"
            )

    def create_success_embed(
        self, interaction: discord.Interaction, user_to_unban: discord.User, reason: str | None
    ) -> discord.Embed:
        embed = discord.Embed(
            title=f"Unbanned {user_to_unban.display_name}!",
            color=discord.Color.red(),
            timestamp=interaction.created_at,
        )
        embed.add_field(name="Reason", value=f"`{reason}`", inline=True)
        embed.add_field(name="Member", value=f"<@{user_to_unban.id}>", inline=True)
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar,
        )
        return embed

    async def send_error_message(self, interaction: discord.Interaction, error_msg: str):
        embed = discord.Embed(
            color=discord.Color.red(),
            title="Error",
            description=error_msg,
            timestamp=interaction.created_at,
        )
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Unban(bot))
