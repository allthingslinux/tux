"""Utility transformers and converters for Discord slash + prefix commands."""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

__all__ = ["MemberOrUser"]

class MemberOrUser(app_commands.Transformer, commands.Converter):
    """Parameter type that resolves to *Member* if possible, else *User*.

    Works for both prefix (`commands.Converter`) and slash
    (`app_commands.Transformer`) invocations so a single annotation can be
    used in `@commands.hybrid_command` definitions.
    """

    # --- app_commands.Transformer protocol ---------------------------------
    # Slash option type must be declared as a class attribute; older d.py exposes it on the *discord* module.
    type: discord.AppCommandOptionType = discord.AppCommandOptionType.user  # noqa: D401

    async def transform(
        self,
        interaction: discord.Interaction,
        value: discord.User,  # Discord supplies a User from the USER option
    ) -> discord.User | discord.Member:  # pragma: no cover
        if interaction.guild:
            # Try cached member first
            member = interaction.guild.get_member(value.id)
            if member is None:
                try:
                    member = await interaction.guild.fetch_member(value.id)
                except discord.HTTPException:
                    member = None
            return member or value
        return value

    # --- commands.Converter protocol --------------------------------------
    async def convert(
        self,
        ctx: commands.Context,
        argument: str | discord.Object | discord.User | discord.Member,
    ) -> discord.User | discord.Member:  # pragma: no cover
        # Let the built-in User converter do the heavy lifting
        try:
            user: discord.User | discord.Member = await commands.UserConverter().convert(ctx, str(argument))
        except commands.BadArgument as exc:
            raise exc

        if isinstance(ctx.guild, discord.Guild):
            member = ctx.guild.get_member(user.id)
            if member is None:
                try:
                    member = await ctx.guild.fetch_member(user.id)
                except discord.HTTPException:
                    member = None
            return member or user
        return user