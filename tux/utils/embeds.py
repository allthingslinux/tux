from datetime import datetime

import discord
from discord.ext import commands

from tux.utils.constants import Constants as CONST


class EmbedCreator:
    @staticmethod
    def get_timestamp(
        ctx: commands.Context[commands.Bot] | None, interaction: discord.Interaction | None
    ) -> datetime:
        if ctx and ctx.message:
            return ctx.message.created_at
        return interaction.created_at if interaction else discord.utils.utcnow()

    @staticmethod
    def get_footer(
        ctx: commands.Context[commands.Bot] | None, interaction: discord.Interaction | None
    ) -> tuple[str, str | None]:
        user: discord.User | discord.Member | None = None

        if ctx:
            user = ctx.author
        elif interaction:
            user = interaction.user

        if isinstance(user, discord.User | discord.Member):
            return (
                f"Requested by {user.display_name}",
                str(user.avatar.url) if user.avatar else None,
            )

        return ("", None)

    # @staticmethod
    # def shell_terminal_format(user: str) -> str:
    #     return f"[{user}@tux ~]$"

    @staticmethod
    def add_field(embed: discord.Embed, name: str, value: str, inline: bool = True) -> None:
        embed.add_field(name=name, value=value, inline=inline)

    @staticmethod
    def set_thumbnail(embed: discord.Embed, url: str) -> None:
        embed.set_thumbnail(url=url)

    @staticmethod
    def base_embed(
        ctx: commands.Context[commands.Bot] | None,
        interaction: discord.Interaction | None,
        state: str,
    ) -> discord.Embed:
        footer = EmbedCreator.get_footer(ctx, interaction)
        timestamp = EmbedCreator.get_timestamp(ctx, interaction)

        # if ctx:
        #     user_name = ctx.author.display_name
        # else:
        #     user_name = interaction.user.display_name if interaction else "Tux"

        embed = discord.Embed()
        embed.color = CONST.EMBED_STATE_COLORS[state]
        embed.set_author(
            name=state.capitalize() if state else "Info",
            icon_url=CONST.EMBED_STATE_ICONS[state]
            if state
            else CONST.EMBED_STATE_ICONS["DEFAULT"],
        )
        embed.set_footer(text=footer[0], icon_url=footer[1])
        embed.timestamp = timestamp

        return embed

    @classmethod
    def create_embed(
        cls,
        ctx: commands.Context[commands.Bot] | None,
        interaction: discord.Interaction | None,
        state: str,
        title: str,
        description: str,
    ) -> discord.Embed:
        embed = cls.base_embed(ctx, interaction, state)
        embed.title = title
        embed.description = description

        return embed

    @classmethod
    def create_default_embed(
        cls,
        title: str,
        description: str,
        ctx: commands.Context[commands.Bot] | None = None,
        interaction: discord.Interaction | None = None,
    ) -> discord.Embed:
        return cls.create_embed(ctx, interaction, "DEFAULT", title, description)

    @classmethod
    def create_info_embed(
        cls,
        title: str,
        description: str,
        ctx: commands.Context[commands.Bot] | None = None,
        interaction: discord.Interaction | None = None,
    ) -> discord.Embed:
        return cls.create_embed(ctx, interaction, "INFO", title, description)

    @classmethod
    def create_error_embed(
        cls,
        title: str,
        description: str,
        ctx: commands.Context[commands.Bot] | None = None,
        interaction: discord.Interaction | None = None,
    ) -> discord.Embed:
        return cls.create_embed(ctx, interaction, "ERROR", title, description)

    @classmethod
    def create_warning_embed(
        cls,
        title: str,
        description: str,
        ctx: commands.Context[commands.Bot] | None = None,
        interaction: discord.Interaction | None = None,
    ) -> discord.Embed:
        return cls.create_embed(ctx, interaction, "WARNING", title, description)

    @classmethod
    def create_success_embed(
        cls,
        title: str,
        description: str,
        ctx: commands.Context[commands.Bot] | None = None,
        interaction: discord.Interaction | None = None,
    ) -> discord.Embed:
        return cls.create_embed(ctx, interaction, "SUCCESS", title, description)
