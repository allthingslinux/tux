import discord
from discord import app_commands
from discord.ext import commands

from tux.utils.embeds import EmbedCreator
from tux.utils.exports import get_ban_list_csv, get_help_embed, get_member_list_csv


class Export(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    export = app_commands.Group(name="export", description="export server data with Tux.")

    @export.command(name="banned", description="Export a list of all banned users.")
    @commands.bot_has_permissions(ban_members=True)
    async def export_banned(
        self,
        interaction: discord.Interaction,
        flags: str | None = None,
    ) -> None:
        """
        Export a list of banned users in csv format.
        """
        bans = [entry async for entry in interaction.guild.bans(limit=10000)]
        valid_flags = ["user", "display", "id", "reason", "mention", "created"]

        if not bans:
            embed = EmbedCreator.create_success_embed(
                title=f"{interaction.guild} Banned Users",
                description="There are no banned users in this server.",
            )
            return await interaction.response.send_message(embed=embed)

        if flags and "--help" not in flags:
            file = await get_ban_list_csv(
                interaction, bans, valid_flags, *flags.split(sep=" ") if flags else []
            )
            return await interaction.response.send_message(file=file)

        title = f"Total Bans in {interaction.guild}: {len(bans)}"
        data_description = "banned users"
        embed = await get_help_embed(interaction, valid_flags, title, data_description)
        return await interaction.response.send_message(embed=embed)

    @export.command(name="members", description="Export a list of all members in the server.")
    async def export_members(
        self,
        interaction: discord.Interaction,
        flags: str | None = None,
    ) -> None:
        """
        Export a list of members in csv format.
        """
        members = list(interaction.guild.members)
        valid_flags = ["user", "display", "id", "mention", "created"]

        if flags and "--help" not in flags:
            file = await get_member_list_csv(
                interaction, members, valid_flags, *flags.split(sep=" ") if flags else []
            )
            return await interaction.response.send_message(file=file)

        title = f"Total Members in {interaction.guild}: {len(members)}"
        data_description = "members"
        embed = await get_help_embed(interaction, valid_flags, title, data_description)
        return await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Export(bot))
