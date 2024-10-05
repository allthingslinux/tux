# cogs/levels/backfill.py

import asyncio
import csv
import datetime
from pathlib import Path

from discord.ext import commands

from tux.bot import Tux
from tux.cogs.services.levels import LevelsService
from tux.database.controllers.levels import LevelsController

# Define the hard-coded CSV path
CSV_FILE_PATH = "./stats.csv"

# TODO: Remove this cog after the backfill process is complete


class BackfillLevels(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_service = LevelsService(bot)  # Initialize service for level and XP calculations
        self.levels_controller = LevelsController()  # Access to the database operations

    @commands.command(name="backfill_levels")
    @commands.has_permissions(administrator=True)
    async def backfill_levels(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Backfills XP and levels from a predefined CSV file at CSV_FILE_PATH.
        """
        await ctx.send("Starting the backfill process. This may take some time...")

        # Path to the CSV file
        path = Path(CSV_FILE_PATH)
        if not path.exists():
            await ctx.send(f"CSV file not found at `{CSV_FILE_PATH}`.")
            return

        # Read the CSV file
        with path.open() as file:  # noqa: ASYNC230
            reader = csv.DictReader(file)
            rows = list(reader)

        # Fetch the guild where the command was invoked
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command must be used within a server.")
            return

        total_members = len(rows)
        processed = 0
        errors = 0

        # Iterate through each row in the CSV
        for row in rows:
            try:
                member_id = int(row["id"])  # Get member ID
                message_count = int(row["count"])  # Get message count

                member = guild.get_member(member_id)  # Locate the member in the guild
                if member is None:
                    # Log the missing member silently
                    errors += 1
                    continue

                # Calculate XP (95% of message count)
                base_xp = 0.95 * message_count

                # Determine the highest multiplier based on roles
                multiplier = self.levels_service.calculate_xp_increment(member)
                total_xp = base_xp * multiplier  # Calculate total XP

                # Calculate the level based on total XP
                new_level = self.levels_service.calculate_level(total_xp)

                # Update the database with the new XP and level
                await self.levels_controller.update_xp_and_level(
                    member_id=member.id,
                    guild_id=guild.id,
                    xp=total_xp,
                    level=new_level,
                    last_message=datetime.datetime.now(datetime.UTC),
                )

                # Assign roles based on the new level
                await self.levels_service.update_roles(member, guild, new_level)

                processed += 1

                # Provide feedback every 10 members
                if processed % 10 == 0:
                    await ctx.send(f"Processed {processed}/{total_members} members.")

                # Respect rate limits by sleeping briefly
                await asyncio.sleep(0.5)  # Adjust as necessary

            except Exception as e:
                await ctx.send(f"Error processing member ID `{row.get("id")}`: {e}")
                errors += 1
                continue

        await ctx.send(
            f"Backfill process completed. Total members processed: {processed}/{total_members}. Errors: {errors}.",
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(BackfillLevels(bot))
