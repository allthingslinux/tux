import asyncio
from collections.abc import Coroutine, Sequence
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseController

# TODO: Move to a constants file or set a global check/error handler for all commands to avoid repetition.

GUILD_ONLY_MESSAGE = "This command can only be used in a guild."


class Db(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_controller = DatabaseController()

    group = app_commands.Group(name="seed", description="Database commands.")

    @app_commands.checks.has_role("Root")
    @group.command(name="members", description="Seeds the database with all members.")
    async def seed_members(self, interaction: discord.Interaction) -> None:
        """
        Seeds the database with all members in the guild.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation.
        """

        await interaction.response.defer()

        if interaction.guild is None:
            await interaction.followup.send(GUILD_ONLY_MESSAGE)
            return

        members: Sequence[discord.Member] = interaction.guild.members

        batch_size = 10

        for i in range(0, len(members), batch_size):
            batch = members[i : i + batch_size]

            tasks = [
                self.db_controller.users.sync_user(
                    user_id=member.id,
                    name=member.name,
                    display_name=member.display_name,
                    mention=str(member.mention),
                    bot=member.bot,
                    created_at=member.created_at,
                    joined_at=member.joined_at,
                )
                for member in batch
            ]

            await asyncio.gather(*tasks)
            await asyncio.sleep(1)

        await interaction.followup.send("Seeded all members.")
        logger.info(f"{interaction.user} seeded all members.")

    @app_commands.checks.has_role("Root")
    @group.command(name="roles", description="Seeds the database with all roles.")
    async def seed_roles(self, interaction: discord.Interaction) -> None:
        """
        Seeds the database with all roles in the guild.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation.
        """

        await interaction.response.defer()

        if interaction.guild is None:
            await interaction.followup.send(GUILD_ONLY_MESSAGE)
            return

        roles: Sequence[discord.Role] = interaction.guild.roles

        batch_size = 10

        for i in range(0, len(roles), batch_size):
            batch = roles[i : i + batch_size]

            tasks = [
                self.db_controller.roles.sync_role(
                    role_id=role.id,
                    role_name=role.name,
                    mention=role.mention,
                    hoist=role.hoist,
                    managed=role.managed,
                    mentionable=role.mentionable,
                    color=role.color.value,
                    created_at=role.created_at,
                )
                for role in batch
            ]

            await asyncio.gather(*tasks)
            await asyncio.sleep(1)

        await interaction.followup.send("Seeded all roles.")
        logger.info(f"{interaction.user} seeded all roles.")

    @app_commands.checks.has_role("Root")
    @group.command(name="user_roles", description="Seeds the database with all user roles.")
    async def seed_user_roles(self, interaction: discord.Interaction) -> None:
        """
        Seeds the database with all user roles in the guild.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation.
        """

        await interaction.response.defer()

        if interaction.guild is None:
            await interaction.followup.send(GUILD_ONLY_MESSAGE)
            return

        members: Sequence[discord.Member] = interaction.guild.members
        batch_size = 10

        for i in range(0, len(members), batch_size):
            batch = members[i : i + batch_size]

            tasks: list[Coroutine[Any, Any, None]] = []

            for member in batch:
                role_ids: list[int] = [role.id for role in member.roles]

                tasks.append(
                    self.db_controller.user_roles.sync_user_roles(
                        user_id=member.id, role_ids=role_ids
                    )
                )

            await asyncio.gather(*tasks)
            await asyncio.sleep(1)

        await interaction.followup.send("Seeded all user roles.")
        logger.info(f"{interaction.user} seeded all user roles.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Db(bot))
