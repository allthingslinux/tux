"""Onboarding decorators for feature gating and access control."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

from tux.ui.embeds import EmbedCreator, EmbedType

if TYPE_CHECKING:
    from tux.core.bot import Tux
    from tux.services.onboarding.service import GuildOnboardingService
else:
    from tux.services.onboarding.service import GuildOnboardingService


def requires_onboarding_completion():
    """Decorator to require onboarding completion before using a command.

    This decorator checks if a guild has completed the onboarding process
    before allowing access to certain features. If onboarding is not complete,
    it sends a helpful message guiding users to complete setup first.

    Usage:
        @requires_onboarding_completion()
        async def some_command(self, ctx):
            # This command requires onboarding completion
            pass
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(self: Any, ctx: commands.Context[Tux], *args: Any, **kwargs: Any) -> Any:
            if not ctx.guild:
                return await func(self, ctx, *args, **kwargs)

            onboarding_service = GuildOnboardingService(ctx.bot)
            completed = await onboarding_service.is_onboarding_completed(ctx.guild.id)

            if not completed:
                embed = EmbedCreator.create_embed(
                    title="🎯 Setup Required",
                    description=(
                        "Before using this feature, please complete the initial setup to ensure everything works properly.\n\n"
                        "**Quick Setup:** Use `/setup wizard` to get started!"
                    ),
                    embed_type=EmbedType.WARNING,
                    custom_color=discord.Color.orange(),
                )

                embed.add_field(
                    name="💡 Why?",
                    value="Some features require proper configuration to work safely and effectively.",
                    inline=False,
                )

                embed.set_footer(text="Run /setup wizard to complete setup")

                await ctx.send(embed=embed, ephemeral=True)
                return None

            return await func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator
