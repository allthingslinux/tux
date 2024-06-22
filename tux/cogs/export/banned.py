import csv
import io

import discord
from discord import app_commands
from discord.ext import commands

from tux.utils.embeds import EmbedCreator


class ExportBanned(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    export = app_commands.Group(name="export", description="export server data with Tux.")

    @export.command(name="banned", description="Export a list of all banned users.")
    async def export_banned(
        self,
        interaction: discord.Interaction,
        flags: str | None = None,
    ) -> None:
        """
        Export a list of banned users in csv format.
        """
        banned_users = [entry async for entry in interaction.guild.bans(limit=2000)]

        if not banned_users:
            embed = EmbedCreator.create_success_embed(
                title=f"{interaction.guild} Banned Users",
                description="There are no banned users in this server.",
            )
            return await interaction.response.send_message(embed=embed)

        # get the csv file based on the flags and banned users list and send
        file = await self.export_ban_list_csv(banned_users, *flags.split(sep=" ") if flags else [])
        return await interaction.response.send_message(file=file)

    @staticmethod
    async def export_ban_list_csv(bans: list[discord.guild.BanEntry], *args: str) -> discord.File:
        valid_flags = {
            "user": "User",
            "display": "Display Name",
            "id": "ID",
            "reason": "Reason",
            "mention": "Mention",
            "created": "Creation Date",
        }

        if args:
            headers = []
            for flag in args:
                flag_key = flag.removeprefix("--")
                if flag_key in valid_flags:
                    headers.append(valid_flags[flag_key])
        else:
            headers = [valid_flags["user"], valid_flags["id"], valid_flags["reason"]]

        rows = []
        for ban in bans:
            row = {}
            for header in headers:
                if header == valid_flags["user"]:
                    row[header] = ban.user.name
                elif header == valid_flags["display"]:
                    row[header] = ban.user.display_name
                elif header == valid_flags["id"]:
                    row[header] = ban.user.id
                elif header == valid_flags["reason"]:
                    row[header] = ban.reason
                elif header == valid_flags["mention"]:
                    row[header] = ban.user.mention
                elif header == valid_flags["created"]:
                    row[header] = ban.user.created_at.isoformat()

            rows.append(row)

        csvfile = io.StringIO()

        writer = csv.DictWriter(csvfile, fieldnames=headers, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

        return discord.File(io.BytesIO(csvfile.getvalue().encode()), filename="bans.csv")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ExportBanned(bot))
