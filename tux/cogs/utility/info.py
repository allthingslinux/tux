from os import name
import discord
from discord import app_commands
from discord.ext import commands

from tux.utils.constants import Constants as CONST


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    group = app_commands.Group(name="info", description="Information commands.")

    @staticmethod
    def create_embed(
        title: str = "", description: str = "", color: int = CONST.COLORS["INFO"]
    ) -> discord.Embed:
        """Utility method for creating a basic embed structure."""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_author(name="Info", icon_url="https://cdn3.emoji.gg/emojis/3228-info.png")
        return embed

    @group.command(name="server", description="Shows information about the server.")
    async def server(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        embed = self.create_embed("Server", guild.name)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon)
        if guild.banner:
            embed.set_image(url=guild.banner.with_format("png").with_size(1024))

        bots = sum(member.bot for member in guild.members)
        owner = str(guild.owner) if guild.owner else "Unknown"
        embed.add_field(name="Members", value=str(guild.member_count))
        embed.add_field(name="Bots", value=str(bots))
        embed.add_field(name="Boosts", value=str(guild.premium_subscription_count))
        embed.add_field(name="Vanity URL", value=str(guild.vanity_url_code or "None"))
        embed.add_field(name="Owner", value=owner)
        embed.add_field(name="Created", value=guild.created_at.strftime("%d/%m/%Y"))
        embed.add_field(name="ID", value=str(guild.id))

        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )
        embed.timestamp = interaction.created_at

        await interaction.response.send_message(embed=embed)

    @group.command(name="tux", description="Shows information about Tux.")
    async def tux(self, interaction: discord.Interaction) -> None:
        embed = self.create_embed(
            "Tux",
            "Tux is a Discord bot which powers the All Things Linux server written in Python using discord.py.",
        )
        embed.add_field(
            name="GitHub", value="[View the source code](https://github.com/allthingslinux/tux)"
        )

        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )
        embed.timestamp = interaction.created_at

        await interaction.response.send_message(embed=embed)

    @group.command(name="member", description="Shows information about a member.")
    async def member(self, interaction: discord.Interaction, member: discord.Member) -> None:
        embed = self.create_embed("Member", f"{member.mention}")

        embed.set_thumbnail(url=member.display_avatar.url)
        bot_status = "✅" if member.bot else "❌"
        joined = (
            member.joined_at.strftime("%a, %b %e, %Y %l:%M %p") if member.joined_at else "Unknown"
        )
        created = member.created_at.strftime("%a, %b %e, %Y %l:%M %p")
        roles = (
            ", ".join(role.mention for role in member.roles[1:]) if member.roles[1:] else "No roles"
        )

        embed.add_field(name="Bot?", value=bot_status, inline=False)
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="ID", value=str(member.id), inline=False)
        embed.add_field(name="Joined", value=joined, inline=False)
        embed.add_field(name="Registered", value=created, inline=False)
        embed.add_field(name="Roles", value=roles, inline=False)

        fetched_member = await self.bot.fetch_user(member.id)
        embed.set_image(url=fetched_member.banner)

        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )
        embed.timestamp = interaction.created_at

        await interaction.response.send_message(embed=embed)

    @group.command(name="irc", description="Shows information about the IRC server")
    async def irc(self, interaction: discord.Interaction) -> None:
        embed = self.create_embed(
            "IRC Server"
            "We have an IRC Server! ",
        )
        embed.set_author(name="Info", icon_url="https://cdn3.emoji.gg/emojis/3228-info.png")
        embed.add_field(
            name="Information", value="irc.atl.tools, 6697, TLS/SSL, Channel: #general"
        )
        embed.add_field(
          name="NickServ Connection Instructions", value="""
          1. Connect to IRC Server
        2. type /msg NickServ register followed by a password and email address.
      3. Talk!"""
        )
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )
        embed.timestamp = interaction.created_at

        await interaction.response.send_message(embed=embed)



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Info(bot))
