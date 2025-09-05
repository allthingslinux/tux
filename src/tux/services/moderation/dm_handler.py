"""
DM (Direct Message) handling for moderation actions.

Handles sending DMs to users before and after moderation actions.
"""

from typing import Any

import discord
from discord.ext import commands
from loguru import logger

from tux.core.types import Tux


class DMHandler:
    """
    Handles DM (Direct Message) operations for moderation actions.

    This mixin provides functionality to:
    - Send DMs to users before/after moderation actions
    - Handle DM failures gracefully
    - Track DM delivery status
    """

    async def send_dm(
        self,
        ctx: commands.Context[Tux],
        silent: bool,
        user: discord.Member | discord.User,
        reason: str,
        action: str,
    ) -> bool:
        """
        Send a DM to the target user.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        silent : bool
            Whether the command is silent.
        user : Union[discord.Member, discord.User]
            The target of the moderation action.
        reason : str
            The reason for the moderation action.
        action : str
            The action being performed.

        Returns
        -------
        bool
            Whether the DM was successfully sent.
        """

        if not silent:
            try:
                await user.send(f"You have been {action} from {ctx.guild} for the following reason:\n> {reason}")
            except (discord.Forbidden, discord.HTTPException) as e:
                logger.warning(f"Failed to send DM to {user}: {e}")
                return False
            else:
                return True
        else:
            return False

    def _handle_dm_result(self, user: discord.Member | discord.User, dm_result: Any) -> bool:
        """
        Handle the result of sending a DM.

        Parameters
        ----------
        user : Union[discord.Member, discord.User]
            The user the DM was sent to.
        dm_result : Any
            The result of the DM sending operation.

        Returns
        -------
        bool
            Whether the DM was successfully sent.
        """

        if isinstance(dm_result, Exception):
            logger.warning(f"Failed to send DM to {user}: {dm_result}")
            return False

        return dm_result if isinstance(dm_result, bool) else False
