import discord
from discord.ext import commands

from tux.database.controllers import DatabaseController


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = DatabaseController().guild_config

    @commands.hybrid_group(name="config", description="Guild configuration commands.", alias="cfg")
    async def config(self, ctx: commands.Context[commands.Bot]) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help("config")

    @commands.has_permissions(administrator=True)
    @config.command(name="set_dev_role", description="Set the dev role for the guild.")
    async def set_dev_role(self, ctx: commands.Context[commands.Bot], role: discord.Role) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_dev_role_id(ctx.guild.id, role.id)
        await ctx.reply(f"Dev role set to {role.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_admin_role", description="Set the admin role for the guild.")
    async def set_admin_role(self, ctx: commands.Context[commands.Bot], role: discord.Role) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_admin_role_id(ctx.guild.id, role.id)
        await ctx.reply(f"Admin role set to {role.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_senior_role", description="Set the senior role for the guild.")
    async def set_senior_role(
        self,
        ctx: commands.Context[commands.Bot],
        role: discord.Role,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_senior_role_id(ctx.guild.id, role.id)
        await ctx.reply(f"Senior role set to {role.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_staff_role", description="Set the base staff role for the guild.")
    async def set_staff_role(self, ctx: commands.Context[commands.Bot], role: discord.Role) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_base_staff_role_id(ctx.guild.id, role.id)
        await ctx.reply(f"Staff role set to {role.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_member_role", description="Set the base member role for the guild.")
    async def set_member_role(
        self,
        ctx: commands.Context[commands.Bot],
        role: discord.Role,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_base_member_role_id(ctx.guild.id, role.id)
        await ctx.reply(f"Member role set to {role.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_junior_role", description="Set the junior role for the guild.")
    async def set_junior_role(
        self,
        ctx: commands.Context[commands.Bot],
        role: discord.Role,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_junior_role_id(ctx.guild.id, role.id)
        await ctx.reply(f"Junior role set to {role.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_jail_role", description="Set the jail role for the guild.")
    async def set_jail_role(self, ctx: commands.Context[commands.Bot], role: discord.Role) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_jail_role_id(ctx.guild.id, role.id)
        await ctx.reply(f"Jail role set to {role.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(
        name="set_quarantine_role",
        description="Set the quarantine role for the guild.",
    )
    async def set_quarantine_role(
        self,
        ctx: commands.Context[commands.Bot],
        role: discord.Role,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_quarantine_role_id(ctx.guild.id, role.id)
        await ctx.reply(f"Quarantine role set to {role.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_mod_role", description="Set the moderator role for the guild.")
    async def set_mod_role(self, ctx: commands.Context[commands.Bot], role: discord.Role) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_mod_role_id(ctx.guild.id, role.id)
        await ctx.reply(f"Moderator role set to {role.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_mod_log", description="Set the mod log channel for the guild.")
    async def set_mod_log(
        self,
        ctx: commands.Context[commands.Bot],
        channel: discord.TextChannel,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_mod_log_channel_id(ctx.guild.id, channel.id)
        await ctx.reply(f"Mod log channel set to {channel.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_audit_log", description="Set the audit log channel for the guild.")
    async def set_audit_log(
        self,
        ctx: commands.Context[commands.Bot],
        channel: discord.TextChannel,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_audit_log_channel_id(ctx.guild.id, channel.id)
        await ctx.reply(f"Audit log channel set to {channel.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_join_log", description="Set the join log channel for the guild.")
    async def set_join_log(
        self,
        ctx: commands.Context[commands.Bot],
        channel: discord.TextChannel,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_join_log_channel_id(ctx.guild.id, channel.id)
        await ctx.reply(f"Join log channel set to {channel.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(
        name="set_private_log",
        description="Set the private log channel for the guild.",
    )
    async def set_private_log(
        self,
        ctx: commands.Context[commands.Bot],
        channel: discord.TextChannel,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_private_log_channel_id(ctx.guild.id, channel.id)
        await ctx.reply(f"Private log channel set to {channel.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_report_log", description="Set the report log channel for the guild.")
    async def set_report_log(
        self,
        ctx: commands.Context[commands.Bot],
        channel: discord.TextChannel,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_report_log_channel_id(ctx.guild.id, channel.id)
        await ctx.reply(f"Report log channel set to {channel.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_dev_log", description="Set the dev log channel for the guild.")
    async def set_dev_log(
        self,
        ctx: commands.Context[commands.Bot],
        channel: discord.TextChannel,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_dev_log_channel_id(ctx.guild.id, channel.id)
        await ctx.reply(f"Dev log channel set to {channel.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_jail_channel", description="Set the jail channel for the guild.")
    async def set_jail_channel(
        self,
        ctx: commands.Context[commands.Bot],
        channel: discord.TextChannel,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_jail_channel_id(ctx.guild.id, channel.id)
        await ctx.reply(f"Jail channel set to {channel.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(
        name="set_starboard_channel",
        description="Set the starboard channel for the guild.",
    )
    async def set_starboard_channel(
        self,
        ctx: commands.Context[commands.Bot],
        channel: discord.TextChannel,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_starboard_channel_id(ctx.guild.id, channel.id)
        await ctx.reply(f"Starboard channel set to {channel.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_mod_channel", description="Set the mod channel for the guild.")
    async def set_mod_channel(
        self,
        ctx: commands.Context[commands.Bot],
        channel: discord.TextChannel,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_mod_channel_id(ctx.guild.id, channel.id)
        await ctx.reply(f"Mod channel set to {channel.mention}.", ephemeral=True)

    @commands.has_permissions(administrator=True)
    @config.command(name="set_bot_channel", description="Set the bot channel for the guild.")
    async def set_bot_channel(
        self,
        ctx: commands.Context[commands.Bot],
        channel: discord.TextChannel,
    ) -> None:
        if ctx.guild is None:
            return
        await self.db.update_guild_bot_channel_id(ctx.guild.id, channel.id)
        await ctx.reply(f"Bot channel set to {channel.mention}.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Config(bot))
