import contextlib

import discord
from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.core.checks import require_junior_mod


class ClearAFK(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.clear_afk.usage = "clearafk <member>"

    @commands.hybrid_command(
        name="clearafk",
        aliases=["cafk", "removeafk"],
        description="Clear a member's AFK status and reset their nickname.",
    )
    @commands.guild_only()
    @require_junior_mod()  # Ensure the user has the required permission level
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
        """

        assert ctx.guild

        if not await self.db.afk.is_afk(member.id, guild_id=ctx.guild.id):
            return await ctx.send(f"{member.mention} is not currently AFK.", ephemeral=True)

        # Fetch the AFK entry to retrieve the original nickname
        entry = await self.db.afk.get_afk_member(member.id, guild_id=ctx.guild.id)

        await self.db.afk.remove_afk(member.id, ctx.guild.id)

        if entry:
            if entry.nickname:
                with contextlib.suppress(discord.Forbidden):
                    await member.edit(nick=entry.nickname)  # Reset nickname to original
            if entry.enforced:  # untimeout the user if  the afk status is a self-timeout
                await member.timeout(None, reason="removing self-timeout")

        return await ctx.send(f"AFK status for {member.mention} has been cleared.", ephemeral=True)


async def setup(bot: Tux) -> None:
    await bot.add_cog(ClearAFK(bot))
