"""Utility functions for sending responses in info commands."""

import discord
from discord.ext import commands

from tux.core.bot import Tux


async def send_view(
    ctx: commands.Context[Tux],
    view: discord.ui.LayoutView,
    ephemeral: bool = True,
) -> None:
    """Send a LayoutView response, handling both interaction and prefix commands.

    Parameters
    ----------
    ctx : commands.Context[Tux]
        The command context.
    view : discord.ui.LayoutView
        The view to send.
    ephemeral : bool, optional
        Whether the response should be ephemeral (slash commands only), by default True.
    """
    if ctx.interaction:
        if ctx.interaction.response.is_done():
            await ctx.interaction.followup.send(view=view, ephemeral=ephemeral)
        else:
            await ctx.interaction.response.send_message(view=view, ephemeral=ephemeral)
    else:
        await ctx.send(view=view)


async def send_error(
    ctx: commands.Context[Tux],
    error_msg: str,
    ephemeral: bool = True,
) -> None:
    """Send an error message response.

    Parameters
    ----------
    ctx : commands.Context[Tux]
        The command context.
    error_msg : str
        The error message to send.
    ephemeral : bool, optional
        Whether the response should be ephemeral (slash commands only), by default True.
    """
    if ctx.interaction:
        if ctx.interaction.response.is_done():
            await ctx.interaction.followup.send(content=error_msg, ephemeral=ephemeral)
        else:
            await ctx.interaction.response.send_message(
                content=error_msg,
                ephemeral=ephemeral,
            )
    else:
        await ctx.send(content=error_msg)
