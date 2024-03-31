import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

# TODO: Add a channel argument to allow setting slowmode for other channels.


class Slowmode(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def send_embed(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        color: discord.Colour,
        error_info: str | None = None,
    ) -> None:
        embed = discord.Embed(
            title=title, description=description, color=color, timestamp=interaction.created_at
        )
        if error_info:
            embed.add_field(name="Error Details", value=f"`{error_info}`", inline=False)
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @app_commands.command(name="slowmode", description="Sets slowmode for the current channel.")
    @app_commands.describe(delay="The slowmode time in seconds, max is 21600, default is 5")
    async def set_slowmode(self, interaction: discord.Interaction, delay: int = 5) -> None:
        if not interaction.channel or interaction.channel.type != discord.ChannelType.text:
            return

        if delay < 0 or delay > 21600:
            return await self.send_embed(
                interaction,
                "Error",
                "The slowmode delay must be between 0 and 21600 seconds.",
                discord.Colour.red(),
            )

        try:
            await interaction.channel.edit(slowmode_delay=delay)
            description = f"Slowmode delay has been {'disabled' if delay == 0 else f'set to {delay} seconds'} for {interaction.channel.mention}."
            await self.send_embed(interaction, "Success!", description, discord.Colour.green())
            logger.info(
                f"{interaction.user} modified slowmode in {interaction.channel.name} to {delay} seconds."
            )
        except discord.errors.Forbidden as e:
            logger.error(f"Failed to change slowmode for {interaction.channel.name}: {e}")
            await self.send_embed(
                interaction,
                "Permission Denied",
                "Failed to change slowmode due to insufficient permissions.",
                discord.Colour.red(),
                error_info=str(e),
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Slowmode(bot))
