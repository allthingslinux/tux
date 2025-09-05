"""
Case response handling for moderation actions.

Handles the creation and sending of case response embeds after moderation actions.
"""

import asyncio

import discord
from discord.ext import commands

from tux.core.types import Tux
from tux.database.models import CaseType as DBCaseType
from tux.shared.constants import CONST


class CaseResponseHandler:
    """
    Handles case response creation and sending for moderation actions.

    This mixin provides functionality to:
    - Create case response embeds
    - Format case titles and descriptions
    - Send responses to moderators and log channels
    """

    async def handle_case_response(
        self,
        ctx: commands.Context[Tux],
        case_type: DBCaseType,
        case_number: int | None,
        reason: str,
        user: discord.Member | discord.User,
        dm_sent: bool,
        duration: str | None = None,
    ) -> discord.Message | None:
        """
        Handle the response for a case and return the audit log message.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        case_type : CaseType
            The type of case.
        case_number : Optional[int]
            The case number.
        reason : str
            The reason for the case.
        user : Union[discord.Member, discord.User]
            The target of the case.
        dm_sent : bool
            Whether the DM was sent.
        duration : Optional[str]
            The duration of the case.

        Returns
        -------
        discord.Message | None
            The audit log message that was sent, or None if sending failed.
        """

        moderator = ctx.author

        fields = [
            ("Moderator", f"-# **{moderator}**\n-# `{moderator.id}`", True),
            ("Target", f"-# **{user}**\n-# `{user.id}`", True),
            ("Reason", f"-# > {reason}", False),
        ]

        title = self._format_case_title(case_type, case_number, duration)

        embed = self.create_embed(  # type: ignore
            ctx,
            title=title,
            fields=fields,
            color=CONST.EMBED_COLORS["CASE"],
            icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
        )

        embed.description = "-# DM sent" if dm_sent else "-# DM not sent"

        # Send audit log message and capture it
        audit_log_message: discord.Message | None
        audit_log_message, _ = await asyncio.gather(  # type: ignore
            self.send_embed(ctx, embed, log_type="mod"),  # type: ignore
            ctx.send(embed=embed, ephemeral=True),  # type: ignore
        )

        return audit_log_message  # type: ignore

    def _format_case_title(self, case_type: DBCaseType, case_number: int | None, duration: str | None) -> str:
        """
        Format a case title.

        Parameters
        ----------
        case_type : CaseType
            The type of case.
        case_number : Optional[int]
            The case number.
        duration : Optional[str]
            The duration of the case.

        Returns
        -------
        str
            The formatted case title.
        """
        case_num = case_number if case_number is not None else 0
        if duration:
            return f"Case #{case_num} ({duration} {case_type.value})"
        return f"Case #{case_num} ({case_type.value})"
