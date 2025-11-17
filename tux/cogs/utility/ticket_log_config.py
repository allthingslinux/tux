import discord
from discord.ext import commands

from tux.bot import Tux
from tux.database.controllers import DatabaseController


class TicketLogConfig(commands.Cog):
    """Cog to configure the ticket log channel."""

    def __init__(self, bot: Tux):
        self.bot = bot
        self.db = DatabaseController()

    @discord.app_commands.command(
        name="set_ticket_log_channel",
        description="Set the channel where ticket logs will be sent.",
    )
    @discord.app_commands.describe(channel="Channel to send ticket logs to")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def set_ticket_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the channel where ticket logs will be sent (slash command)."""
        await self.db.guild_config.update_ticket_log_id(interaction.guild.id, channel.id)
        await interaction.response.send_message(f"Ticket log channel set to {channel.mention}", ephemeral=True)

    async def get_log_channel_id(self, guild_id: int):
        """Get the ticket log channel ID for a guild."""
        return await self.db.guild_config.get_ticket_log_id(guild_id)


async def setup(bot: Tux):
    await bot.add_cog(TicketLogConfig(bot))
