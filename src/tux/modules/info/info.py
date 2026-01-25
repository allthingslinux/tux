"""
Information display commands for Discord objects.

This module provides comprehensive information display commands for various Discord
entities including users, members, channels, guilds, roles, emojis, and stickers.
Each command shows detailed information using Components V2.
"""

from contextlib import suppress

import discord
from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux

from .builders import (
    build_channel_view,
    build_emoji_view,
    build_guild_view,
    build_invite_view,
    build_member_view,
    build_role_view,
    build_thread_view,
    build_user_view,
)
from .helpers import extract_invite_code
from .utils import send_error, send_view


class Info(BaseCog):
    """Information commands for Discord objects."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Info cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.hybrid_group(
        name="info",
        aliases=["i"],
    )
    @commands.guild_only()
    async def info(
        self,
        ctx: commands.Context[Tux],
    ) -> None:
        """Get information about Discord objects.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object associated with the command.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("info")

    @info.command(
        name="server",
        aliases=["guild", "s"],
    )
    @commands.guild_only()
    async def info_server(
        self,
        ctx: commands.Context[Tux],
        guild_input: str | None = None,
    ) -> None:
        """Get information about a server/guild.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        guild_input : str | None, optional
            The guild ID or invite URL to get information about. If None, uses current guild.
        """
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        if guild_input is None:
            guild = ctx.guild
            if guild is None:
                await send_error(ctx, "This command can only be used in a server.")
                return
            view = await build_guild_view(guild)
            await send_view(ctx, view)
            return

        guild = None

        # First, try to parse as guild ID
        if guild_input.isdigit() and 15 <= len(guild_input) <= 20:
            guild = self.bot.get_guild(int(guild_input))
            if guild is not None:
                view = await build_guild_view(guild)
                await send_view(ctx, view)
                return

        # If not a guild ID, try to extract from invite URL
        invite_input_lower = guild_input.lower()
        if (
            "discord.gg/" in invite_input_lower
            or "discord.com/invite/" in invite_input_lower
        ):
            with suppress(commands.BadArgument):
                extracted_code = extract_invite_code(guild_input)
                invite_converter = commands.InviteConverter()
                invite = await invite_converter.convert(ctx, extracted_code)

                if invite.guild:
                    guild = self.bot.get_guild(invite.guild.id)
                    if guild is not None:
                        view = await build_guild_view(guild)
                        await send_view(ctx, view)
                        return
                    error_msg = (
                        f"❌ I'm not in the server from invite `{extracted_code}`. "
                        "I can only show information for servers I'm a member of."
                    )
                    await send_error(ctx, error_msg)
                    return
                error_msg = (
                    f"❌ The invite `{extracted_code}` doesn't point to a server. "
                    "Please provide a valid server invite or guild ID."
                )
                await send_error(ctx, error_msg)
                return

        error_msg = (
            f"❌ I couldn't find a server with ID or invite `{guild_input}`. "
            "Please provide a valid guild ID or invite URL (e.g., discord.gg/linux)."
        )
        await send_error(ctx, error_msg)

    @info.command(
        name="user",
        aliases=["member", "u", "m"],
    )
    @commands.guild_only()
    async def info_user(
        self,
        ctx: commands.Context[Tux],
        entity: str,
    ) -> None:
        """Get information about a user or member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        entity : str
            The user or member to get information about (mention or ID).
        """
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        # Try MemberConverter first (for guild members)
        member_converter = commands.MemberConverter()
        with suppress(commands.BadArgument):
            member = await member_converter.convert(ctx, entity)
            view = await build_member_view(member, self.bot)
            await send_view(ctx, view)
            return

        # Try UserConverter (for users not in guild)
        user_converter = commands.UserConverter()
        with suppress(commands.BadArgument):
            user = await user_converter.convert(ctx, entity)
            view = build_user_view(user)
            await send_view(ctx, view)
            return

        error_msg = f"❌ I couldn't find a user or member matching '{entity}'. Please provide a valid mention or ID."
        await send_error(ctx, error_msg)

    @info.command(
        name="emoji",
        aliases=["e"],
    )
    @commands.guild_only()
    async def info_emoji(
        self,
        ctx: commands.Context[Tux],
        emoji: discord.Emoji,
    ) -> None:
        """Get information about an emoji.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        emoji : discord.Emoji
            The emoji to get information about (mention or ID).
        """
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        view = build_emoji_view(emoji)
        await send_view(ctx, view)

    @info.command(
        name="role",
        aliases=["r"],
    )
    @commands.guild_only()
    async def info_role(
        self,
        ctx: commands.Context[Tux],
        role: discord.Role,
    ) -> None:
        """Get information about a role.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        role : discord.Role
            The role to get information about (mention or ID).
        """
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        view = build_role_view(role)
        await send_view(ctx, view)

    @info.command(
        name="channel",
        aliases=["c"],
    )
    @commands.guild_only()
    async def info_channel(
        self,
        ctx: commands.Context[Tux],
        channel: discord.abc.GuildChannel | discord.Thread,
    ) -> None:
        """Get information about a channel or thread.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        channel : discord.abc.GuildChannel | discord.Thread
            The channel or thread to get information about (mention or ID).
        """
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        if isinstance(channel, discord.Thread):
            view = build_thread_view(channel)
        else:
            view = build_channel_view(channel)
        await send_view(ctx, view)

    @info.command(
        name="invite",
        aliases=["inv"],
    )
    @commands.guild_only()
    async def info_invite(
        self,
        ctx: commands.Context[Tux],
        invite_code: str,
    ) -> None:
        """Get information about an invite.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        invite_code : str
            The invite code or URL to get information about.
        """
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        extracted_code = extract_invite_code(invite_code)
        invite_converter = commands.InviteConverter()
        try:
            invite = await invite_converter.convert(ctx, extracted_code)
            view = build_invite_view(invite)
            await send_view(ctx, view)
        except commands.BadArgument:
            error_msg = f"❌ I couldn't find an invite matching '{extracted_code}'. Please provide a valid invite code or URL."
            await send_error(ctx, error_msg)


async def setup(bot: Tux) -> None:
    """Set up the Info cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Info(bot))
