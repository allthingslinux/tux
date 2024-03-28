import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Server(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="server", description="Shows information about the server.")
    async def server(self, interaction: discord.Interaction) -> None:
        if not (guild := interaction.guild):
            return

        embed = discord.Embed()

        find_bots = sum(bool(member.bot) for member in guild.members)

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

        logger.info(f"{interaction.user} used the server command in {interaction.channel}.")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Server(bot))
