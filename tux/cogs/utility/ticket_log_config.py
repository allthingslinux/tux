from pathlib import Path

import discord
from discord.ext import commands

from tux.bot import Tux

CONFIG_PATH = (Path(__file__).parent / "../../assets/embeds/ticket_log_channel.txt").resolve()


class TicketLogConfig(commands.Cog):
    """Cog to configure the ticket log channel."""

    def __init__(self, bot: Tux):
        self.bot = bot
        self._load_config()

    def _load_config(self):
        self.config = {}
        if CONFIG_PATH.exists():
            with CONFIG_PATH.open() as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or ":" not in line:
                        continue
                    gid, cid = line.split(":", 1)
                    self.config[gid] = int(cid)

    def _save_config(self):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_PATH.open("w") as f:
            f.writelines(f"{gid}:{cid}\n" for gid, cid in self.config.items())

    @discord.app_commands.command(
        name="set_ticket_log_channel",
        description="Set the channel where ticket logs will be sent.",
    )
    @discord.app_commands.describe(channel="Channel to send ticket logs to")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def set_ticket_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the channel where ticket logs will be sent (slash command)."""
        self.config[str(interaction.guild.id)] = channel.id
        self._save_config()
        await interaction.response.send_message(f"Ticket log channel set to {channel.mention}", ephemeral=True)

    def get_log_channel_id(self, guild_id: int):
        return self.config.get(str(guild_id))


async def setup(bot: Tux):
    await bot.add_cog(TicketLogConfig(bot))
