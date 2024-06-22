import csv
import datetime
import io

import discord

_flags = {
    "user": "User",
    "display": "Display Name",
    "id": "ID",
    "reason": "Reason",
    "mention": "Mention",
    "created": "Creation Date",
}


async def _define_headers(args: tuple, valid_flags: list, default: list | None = None) -> list[str]:
    """
    Define the headers for the CSV output file.
    """
    if default is None:
        default = [_flags["user"], _flags["id"]]

    headers = []

    if "--all" in args:
        headers = [_flags[flag_key] for flag_key in _flags if flag_key in valid_flags]

    else:
        for flag in args:
            flag_key = flag.removeprefix("--")
            if flag_key in valid_flags:
                headers.append(_flags[flag_key])

    return headers or default


async def _create_encoded_string(headers, rows, quoting=csv.QUOTE_MINIMAL) -> io.BytesIO:
    """
    Create an encoded string from the retrieved data.
    """
    csvfile = io.StringIO()
    writer = csv.DictWriter(csvfile, fieldnames=headers, quoting=quoting)
    writer.writeheader()
    writer.writerows(rows)
    return io.BytesIO(csvfile.getvalue().encode())


async def get_ban_list_csv(
    interaction: discord.Interaction, bans: list[discord.guild.BanEntry], *args: str
) -> discord.File:
    """
    Export a list of banned users in CSV format.
    """
    valid_flags = ["user", "display", "id", "reason", "mention", "created", "all"]
    headers: list = await _define_headers(
        args, valid_flags, default=[_flags["user"], _flags["id"], _flags["reason"]]
    )

    rows = []
    for ban in bans:
        row = {}
        for header in headers:
            if header == _flags["user"]:
                row[header] = ban.user.name
            elif header == _flags["display"]:
                row[header] = ban.user.display_name
            elif header == _flags["id"]:
                row[header] = ban.user.id
            elif header == _flags["reason"]:
                row[header] = ban.reason
            elif header == _flags["mention"]:
                row[header] = ban.user.mention
            elif header == _flags["created"]:
                row[header] = ban.user.created_at.isoformat()

        rows.append(row)

    guild_id = interaction.guild.id
    timestamp = datetime.datetime.now(tz=datetime.UTC).strftime("%Y%m%d_%H%M%S")
    csvfile = await _create_encoded_string(headers, rows)

    return discord.File(csvfile, filename=f"{guild_id}_bans_{timestamp}.csv")


async def get_member_list_csv(
    interaction: discord.Interaction, members: list[discord.Member], *args: str
) -> discord.File:
    """
    Export a list of members in CSV format.
    """
    valid_flags = ["user", "display", "id", "mention", "created", "all"]
    headers: list = await _define_headers(args, valid_flags, [_flags["user"], _flags["id"]])

    rows = []
    for member in members:
        row = {}
        for header in headers:
            if header == _flags["user"]:
                row[header] = member.name
            elif header == _flags["display"]:
                row[header] = member.display_name
            elif header == _flags["id"]:
                row[header] = member.id
            elif header == _flags["mention"]:
                row[header] = member.mention
            elif header == _flags["created"]:
                row[header] = member.created_at.isoformat()

        rows.append(row)

    guild_id = interaction.guild.id
    timestamp = datetime.datetime.now(tz=datetime.UTC).strftime("%Y%m%d_%H%M%S")
    csvfile = await _create_encoded_string(headers, rows)

    return discord.File(csvfile, filename=f"{guild_id}_members_{timestamp}.csv")
