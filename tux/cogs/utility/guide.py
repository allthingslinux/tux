import discord
from discord import app_commands
from discord.ext import commands

# from loguru import logger
from tux.utils.constants import Constants as CONST


class Guide(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def create_embed(
        title: str = "", description: str = "", color: int = CONST.COLORS["INFO"]
    ) -> discord.Embed:
        """Utility method for creating a basic embed structure."""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_author(name="Info", icon_url="https://cdn3.emoji.gg/emojis/3228-info.png")
        return embed

    @app_commands.command(
        name="guide", description="See useful channels and other resources for the server."
    )
    async def guide(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        embed = self.create_embed("Server Guide", "Welcome to " + guild.name + "!")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon)
        if guild.banner:
            embed.set_image(url=guild.banner.with_format("png").with_size(1024))
        embed.add_field(
            name="Categories",
            value="""/SRV/ Get roles, look at starboard and suggest things.
                     /HOME/ Chat with our community.
                     /MNT/SUPPORT/ Get help with a variety of topics!
                     /DEV/VOICE/ Listen to music or just talk.
                     /VAR/LOG/: See logs related to moderation actions and github logs.

                 """,
        )
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )
        embed.timestamp = interaction.created_at
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Guide(bot))
