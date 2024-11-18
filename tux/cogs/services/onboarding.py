# This service is to handle onboarding of a server on the bot's first join.
# In order to use all features from Tux, the server needs to have certain configurations set up.
# Without setting up these configurations, said features will be locked.
# This service will write to the database based on the server's onboarding progress until it's completed.
# The onboarding progress will be checked on every command invocation.
# Ideally this should be managed with cache to avoid unnecessary database calls.
# This service will also handle the onboarding command.

import discord
from discord.ext import commands

from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.mentionable_tree import MentionableTree


class Onboarding(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.guild_db = DatabaseController().guild
        self.guild_config_db = DatabaseController().guild_config

    @commands.command(name="onboarding")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def onboarding(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Start the onboarding process for the server.
        """
        guild = ctx.guild

        assert guild

        # Create a onboarding channel and set the channel as private for the inviter and owners only.

        overwrites: dict[discord.Role | discord.Member, discord.PermissionOverwrite] = {
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        if guild.owner:
            overwrites[guild.owner] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        onboarding_channel = await guild.create_text_channel("tux-onboarding", overwrites=overwrites)

        # Send a welcome embed and add a reaction to it for moving to the next step.

        embed = discord.Embed(
            title="Server Onboarding",
            description="Hello! I'm Tux, an all-in-one Discord bot. Let's get started with setting up your server.",
            color=discord.Color.blurple(),
        )

        # Step 1: Set up the prefix

        # Get the /config prefix set app command mention from the mentionable tree

        assert self.bot.tree is not None and isinstance(self.bot.tree, MentionableTree)
        cmd = await self.bot.tree.find_mention_for("config prefix set", guild=guild)
        prefix_set_mention = cmd or "config prefix set"

        embed.add_field(
            name="Step 1: Set up the prefix",
            value=f"The default prefix is `$`. You can change it by using the slash command below.\n {prefix_set_mention}",
            inline=False,
        )

        await onboarding_channel.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Onboarding(bot))
