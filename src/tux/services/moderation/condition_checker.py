"""
Condition checking for moderation actions.

Handles permission checks, role hierarchy validation, and other preconditions for moderation actions.
"""

import discord
from discord.ext import commands

from tux.core.types import Tux


class ConditionChecker:
    """
    Checks conditions and permissions for moderation actions.

    This mixin provides functionality to:
    - Validate moderator permissions
    - Check role hierarchies
    - Prevent self-moderation
    - Validate guild ownership rules
    """

    async def check_bot_permissions(
        self,
        ctx: commands.Context[Tux],
        action: str,
    ) -> tuple[bool, str | None]:
        """
        Check if the bot has the required permissions to perform the action.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        action : str
            The action being performed.

        Returns
        -------
        tuple[bool, str | None]
            (has_permissions, error_message)
        """
        assert ctx.guild
        assert ctx.bot and ctx.bot.user

        bot_member = ctx.guild.get_member(ctx.bot.user.id)
        if not bot_member:
            return False, "Bot is not a member of this server."

        # Define permission requirements for each action
        action_permissions = {
            "ban": ["ban_members"],
            "kick": ["kick_members"],
            "timeout": ["moderate_members"],
            "mute": ["moderate_members"],
            "unmute": ["moderate_members"],
            "warn": [],  # No special permissions needed
            "note": [],  # No special permissions needed
        }

        required_perms = action_permissions.get(action.lower(), [])
        if not required_perms:
            return True, None  # Action doesn't require special permissions

        # Check each required permission
        missing_perms = [
            perm.replace("_", " ").title()
            for perm in required_perms
            if not getattr(bot_member.guild_permissions, perm, False)
        ]

        if missing_perms:
            perm_list = ", ".join(missing_perms)
            return False, f"Bot is missing required permissions: {perm_list}"

        return True, None

    async def check_conditions(
        self,
        ctx: commands.Context[Tux],
        user: discord.Member | discord.User,
        moderator: discord.Member | discord.User,
        action: str,
    ) -> bool:
        """
        Check if the conditions for the moderation action are met.

        This includes bot permission validation, user validation, and hierarchy checks.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        user : Union[discord.Member, discord.User]
            The target of the moderation action.
        moderator : Union[discord.Member, discord.User]
            The moderator of the moderation action.
        action : str
            The action being performed.

        Returns
        -------
        bool
            Whether the conditions are met.
        """

        assert ctx.guild

        # 🔍 PHASE 1: Bot Permission Validation
        bot_has_perms, bot_error = await self.check_bot_permissions(ctx, action)
        if not bot_has_perms:
            await self.send_error_response(ctx, bot_error)  # type: ignore
            return False

        # 🔍 PHASE 2: User Validation
        fail_reason = None

        # Self-moderation check
        if user.id == moderator.id:
            fail_reason = f"You cannot {action} yourself."
        # Guild owner check
        elif user.id == ctx.guild.owner_id:
            fail_reason = f"You cannot {action} the server owner."
        # Role hierarchy check - only applies when both are Members
        elif (
            isinstance(user, discord.Member)
            and isinstance(moderator, discord.Member)
            and user.top_role >= moderator.top_role
        ):
            fail_reason = f"You cannot {action} a user with a higher or equal role."
        # Bot hierarchy check
        elif isinstance(user, discord.Member):
            assert ctx.bot and ctx.bot.user
            bot_member = ctx.guild.get_member(ctx.bot.user.id)
            if bot_member and user.top_role >= bot_member.top_role:
                fail_reason = f"Cannot {action} user with higher or equal role than bot."

        # If we have a failure reason, send the embed and return False
        if fail_reason:
            await self.send_error_response(ctx, fail_reason)  # type: ignore
            return False

        # All checks passed
        return True
