import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

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
        embed = self.create_embed("Server Guide", f"Welcome to {guild.name}!")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon)
        if guild.banner:
            embed.set_image(url=guild.banner.with_format("png").with_size(1024))
        embed.add_field(
            name="Quick Links",
            value="""
            **Meta:**
            <#1172252854371749958>
            <#1172343581495795752>
            <#1172259762893754480>
            <#1193304492226129971>
            **Support:**
            <#1172312602181902357>
            <#1172312653797007461>
            <#1172312674298761216>
            **Resources:**
            <#1221117147091304548>
            <#1221115462549504060>
            <#1174251004586381323>
            <#1174742125036961863>
            <#1220004498789896253>
                 """,
        )
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )
        embed.timestamp = interaction.created_at
        logger.info(f"{interaction.user} used the guide command in {interaction.channel}.")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Guide(bot))
