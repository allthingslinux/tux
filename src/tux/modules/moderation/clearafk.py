"""
AFK status clearing commands.

This module provides commands to manually clear AFK status from users
and reset their nicknames back to their original state.
"""

import contextlib

import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.core.checks import requires_command_permission


class ClearAFK(BaseCog):
    """Discord cog for clearing AFK status from users."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the ClearAFK cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)
        self.clear_afk.usage = "clearafk <member>"

    @commands.hybrid_command(
        name="clearafk",
        aliases=["unafk"],
        description="Clear a member's AFK status and reset their nickname.",
    )
    @commands.guild_only()
    @requires_command_permission(
        allow_self_use_for_param="member",
    )  # Anyone can clear their own AFK; clearing others requires permission rank
    async def clear_afk(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
    ) -> discord.Message:
        """
        Clear a member's AFK status and reset their nickname.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member whose AFK status is to be cleared.

        Returns
        -------
        discord.Message
            The confirmation message sent. Raises on send failure.
        """
        assert ctx.guild

        if not await self.db.afk.is_afk(member.id, guild_id=ctx.guild.id):
            if ctx.interaction:
                msg = await ctx.interaction.followup.send(
                    f"{member.mention} is not currently AFK.",
                    ephemeral=True,
                )
                assert msg is not None  # followup.send always returns Message
                return msg
            return await ctx.send(f"{member.mention} is not currently AFK.")

        # Fetch the AFK entry to retrieve the original nickname
        entry = await self.db.afk.get_afk_member(member.id, guild_id=ctx.guild.id)

        if not entry:
            # Entry was removed between check and fetch (race condition)
            if ctx.interaction:
                msg = await ctx.interaction.followup.send(
                    f"{member.mention} is no longer AFK.",
                    ephemeral=True,
                )
                assert msg is not None
                return msg
            return await ctx.send(f"{member.mention} is no longer AFK.")

        # Restore nickname and untimeout before removing from database
        # This ensures if operations fail, AFK entry still exists
        nickname_restored = False
        if entry.nickname:
            with contextlib.suppress(discord.Forbidden):
                await member.edit(nick=entry.nickname)  # Reset nickname to original
                nickname_restored = True

        if entry.enforced:  # untimeout the user if the afk status is a self-timeout
            try:
                # Check if member is actually timed out before attempting untimeout
                if member.timed_out_until is not None:
                    await member.timeout(None, reason="removing self-timeout")
            except (discord.Forbidden, discord.HTTPException) as e:
                logger.warning(
                    f"Failed to untimeout member {member.id}: {e}",
                )

        # Only remove from database after operations succeed (or are attempted)
        # Re-check entry exists to avoid race condition
        current_entry = await self.db.afk.get_afk_member(
            member.id,
            guild_id=ctx.guild.id,
        )
        if current_entry is not None:
            await self.db.afk.remove_afk(member.id, ctx.guild.id)
        elif not nickname_restored and entry.nickname:
            # Entry was removed but nickname wasn't restored, try to restore it
            with contextlib.suppress(discord.Forbidden):
                await member.edit(nick=entry.nickname)

        if ctx.interaction:
            msg = await ctx.interaction.followup.send(
                f"AFK status for {member.mention} has been cleared.",
                ephemeral=True,
            )
            assert msg is not None  # followup.send always returns Message
            return msg
        return await ctx.send(
            f"AFK status for {member.mention} has been cleared.",
        )


async def setup(bot: Tux) -> None:
    """Set up the ClearAFK cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(ClearAFK(bot))
