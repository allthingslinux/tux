import discord
from discord import app_commands

from tux.command_cog import CommandCog
from tux.main import TuxBot
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Server(CommandCog):
    @app_commands.command(
        name="server", description="Shows information about the server."
    )
    async def server(self, interaction: discord.Interaction) -> None:
        """
        Shows information about the server.
        """
        guild = interaction.guild

        if guild:
            find_bots = sum(1 for member in guild.members if member.bot)

            embed = discord.Embed()

            if guild.icon:
                embed.set_thumbnail(url=guild.icon)
            if guild.banner:
                embed.set_image(url=guild.banner.with_format("png").with_size(1024))

            embed.title = guild.name
            embed.add_field(name="Members", value=guild.member_count)
            embed.add_field(name="Bots", value=find_bots)
            embed.add_field(name="Boosts", value=guild.premium_subscription_count)
            embed.add_field(name="Vanity URL", value=guild.vanity_url_code)
            embed.add_field(name="Owner", value=guild.owner)
            embed.add_field(name="Created", value=guild.created_at.strftime("%d/%m/%Y"))

            embed.set_footer(text=f"Server ID: {guild.id}")

            await interaction.response.send_message(embed=embed)


async def setup(bot: TuxBot) -> None:
    await bot.add_cog(Server(bot))
