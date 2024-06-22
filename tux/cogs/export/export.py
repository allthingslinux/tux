import discord
from discord import app_commands
from discord.ext import commands

from tux.utils.embeds import EmbedCreator
from tux.utils.exports import get_ban_list_csv


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

        if not bans:
            embed = EmbedCreator.create_success_embed(
                title=f"{interaction.guild} Banned Users",
                description="There are no banned users in this server.",
            )
            return await interaction.response.send_message(embed=embed)

        if flags and "--help" not in flags:
            file = await get_ban_list_csv(interaction, bans, *flags.split(sep=" ") if flags else [])
            return await interaction.response.send_message(file=file)

        embed = EmbedCreator.create_success_embed(
            title=f"Total Bans in {interaction.guild}: {len(bans)}",
            description="Use any combination of the following flags "
            "to export a list of banned users to a CSV file:\n"
            "```"
            "--user (User Name)\n"
            "--display (Display Name)\n"
            "--id (User ID)\n"
            "--reason (Ban Reason)\n"
            "--mention (User Mention)\n"
            "--created (Account Creation Date)\n"
            "--all (Export all available fields)\n"
            "--help (Show this message)"
            "```",
        )
        return await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Export(bot))
