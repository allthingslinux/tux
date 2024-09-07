import csv
import datetime
import io

import discord

from tux.ui.embeds import EmbedCreator

_flags = {
    "user": "User",
    "display": "Display Name",
    "id": "ID",
    "reason": "Reason",
    "mention": "Mention",
    "created": "Creation Date",
}


async def _define_headers(
    args: list[str],
    valid_flags: list[str],
    default: list[str] | None = None,
) -> list[str]:
    """
    Define the headers for the CSV output file.
    """
    if default is None:
        default = [_flags["user"], _flags["id"]]

    headers: list[str] = []

    if "--all" in args:
        headers = [_flags[flag_key] for flag_key in _flags if flag_key in valid_flags]

    else:
        for flag in args:
            flag_key = flag.removeprefix("--")
            if flag_key in valid_flags:
                headers.append(_flags[flag_key])

    return headers or default


async def _create_encoded_string(
    headers: list[str],
    rows: list[dict[str, str]],
    quoting: int = csv.QUOTE_ALL,
) -> io.BytesIO:
    """
    Create an encoded string from the retrieved data.
    """
    csvfile = io.StringIO()
    writer = csv.DictWriter(csvfile, fieldnames=headers, quoting=quoting)
    writer.writeheader()
    writer.writerows(rows)
    return io.BytesIO(csvfile.getvalue().encode())


async def get_help_embed(
    valid_flags: list[str],
    title: str,
    data_description: str,
) -> discord.Embed:
    """
    Create an embed with help information for exporting data.
    """
    valid_flags.sort()

    return EmbedCreator.create_embed(
        embed_type=EmbedCreator.INFO,
        title=title,
        description=f"Use any combination of the following flags to export a list of {data_description} to a CSV file:\n```--all\n{'\n'.join([f'--{flag}' for flag in valid_flags])}```",
    )


async def get_ban_list_csv(
    interaction: discord.Interaction,
    bans: list[discord.guild.BanEntry],
    valid_flags: list[str],
    args: list[str],
) -> discord.File:
    """
    Export a list of banned users in CSV format.
    """
    headers: list[str] = await _define_headers(
        args,
        valid_flags,
        default=[_flags["user"], _flags["id"], _flags["reason"]],
    )

    rows: list[dict[str, str]] = []
    for ban in bans:
        row: dict[str, str] = {}
        for header in headers:
            if header == _flags["user"]:
                row[header] = ban.user.name
            elif header == _flags["display"]:
                row[header] = ban.user.display_name
            elif header == _flags["id"]:
                row[header] = str(ban.user.id)
            elif header == _flags["reason"]:
                row[header] = str(ban.reason)
            elif header == _flags["mention"]:
                row[header] = ban.user.mention
            elif header == _flags["created"]:
                row[header] = ban.user.created_at.isoformat()

        rows.append(row)

    if interaction.guild is None:
        msg = "Interaction does not have a guild attribute."
        raise ValueError(msg)

    guild_id = interaction.guild.id
    timestamp = datetime.datetime.now(tz=datetime.UTC).strftime("%Y%m%d_%H%M%S")
    csvfile = await _create_encoded_string(headers, rows)

    return discord.File(csvfile, filename=f"{guild_id}_bans_{timestamp}.csv")


async def get_member_list_csv(
    interaction: discord.Interaction,
    members: list[discord.Member],
    valid_flags: list[str],
    args: list[str],
) -> discord.File:
    """
    Export a list of members in CSV format.
    """
    headers: list[str] = await _define_headers(args, valid_flags, [_flags["user"], _flags["id"]])

    rows: list[dict[str, str]] = []
    for member in members:
        row: dict[str, str] = {}
        for header in headers:
            if header == _flags["user"]:
                row[header] = member.name
            elif header == _flags["display"]:
                row[header] = member.display_name
            elif header == _flags["id"]:
                row[header] = str(member.id)
            elif header == _flags["mention"]:
                row[header] = member.mention
            elif header == _flags["created"]:
                row[header] = member.created_at.isoformat()

        rows.append(row)

    if interaction.guild is None:
        msg = "Interaction does not have a guild attribute."
        raise ValueError(msg)

    guild_id = interaction.guild.id
    timestamp = datetime.datetime.now(tz=datetime.UTC).strftime("%Y%m%d_%H%M%S")
    csvfile = await _create_encoded_string(headers, rows)

    return discord.File(csvfile, filename=f"{guild_id}_members_{timestamp}.csv")
