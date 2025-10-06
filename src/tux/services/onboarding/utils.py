"""Utility functions and helpers for the onboarding service."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from loguru import logger

from tux.ui.embeds import EmbedCreator, EmbedType

if TYPE_CHECKING:
    from tux.core.bot import Tux


async def find_welcome_channel(guild: discord.Guild) -> discord.TextChannel | None:
    """Find the best channel to send welcome messages.

    Priority order:
    1. System channel (where Discord sends join messages)
    2. General channel (common names like 'general', 'main', 'chat')
    3. First text channel the bot can send to

    Args:
        guild: The Discord guild to search in

    Returns:
        The best text channel for sending messages, or None if none found
    """
    # Check system channel first
    if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
        return guild.system_channel

    # Check for common general channel names
    general_names = ["general", "main", "chat", "lounge", "welcome"]
    for channel in guild.text_channels:
        if (
            any(name in channel.name.lower() for name in general_names)
            and channel.permissions_for(guild.me).send_messages
        ):
            return channel

    # Find the first channel the bot can send to
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            return channel

    return None


async def send_fallback_welcome_message(guild: discord.Guild, bot: Tux) -> None:
    """Send a fallback welcome message when onboarding channel creation fails.

    Args:
        guild: The Discord guild to send the message to
        bot: The bot instance for database access
    """
    # Try to find the best channel to send the welcome message
    channel = await find_welcome_channel(guild)
    if not channel:
        logger.warning(f"No suitable channel found to send welcome message for guild {guild.id}")
        return

    embed = EmbedCreator.create_embed(
        title="🎉 Welcome to Tux!",
        description=(
            f"Thanks for adding Tux to **{guild.name}**! I'm here to help moderate and manage your server.\n\n"
            "**🚀 Quick Setup (2 minutes):**\n"
            "I've automatically created a permission system for your server. To complete setup:\n\n"
            "1. **Run the setup wizard:** `/setup wizard`\n"
            "2. **Configure essential channels and roles**\n"
            "3. **Assign staff roles to permission ranks**\n\n"
            "**📖 Need Help?**\n"
            "• Use `/setup status` to check your progress\n"
            "• Use `/config` to manage permissions and settings\n"
            "• Use `/help` to see all available commands\n\n"
            "**💡 Pro Tip:** The setup wizard will guide you through everything step-by-step!"
        ),
        embed_type=EmbedType.SUCCESS,
        custom_color=discord.Color.blue(),
    )

    embed.add_field(
        name="📋 What's Been Set Up",
        value=(
            "✅ **Permission Ranks Created**\n"
            "• Member, Trusted, Junior Moderator\n"
            "• Moderator, Senior Moderator\n"
            "• Administrator, Head Administrator\n"
            "• Server Owner\n\n"
            "🔄 **Next Steps:** Configure channels and assign roles"
        ),
        inline=False,
    )

    embed.set_footer(text="Use /setup wizard to get started!")

    try:
        await channel.send(embed=embed)
        logger.info(f"Sent welcome message to guild {guild.id} in channel {channel.id}")
    except (discord.Forbidden, discord.HTTPException) as e:
        logger.warning(f"Failed to send welcome message to guild {guild.id}: {e}")


def get_channel_permissions_overwrites(
    guild: discord.Guild,
) -> dict[discord.Role | discord.Member, discord.PermissionOverwrite]:
    """Get the permission overwrites for creating an onboarding channel.

    Args:
        guild: The Discord guild to create the channel in

    Returns:
        Dictionary of permission overwrites for the channel
    """
    return {
        guild.default_role: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            read_message_history=True,
        ),
        guild.me: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            manage_channels=True,
            manage_messages=True,
        ),
    }
