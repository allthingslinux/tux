from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from tux.database.controllers import DatabaseController


class ConfigSelectMenu(discord.ui.RoleSelect[Any]):
    def __init__(self) -> None:
        self.db = DatabaseController().guild_config
        super().__init__(
            placeholder="Select a setting to configure.",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return

        if self.values[0] == "mod_log":
            await self.db.update_mod_log_id(interaction.guild.id, self.values[1].id)
            await interaction.response.send_message(f"Mod log channel set to {self.values[1].mention}.", ephemeral=True)


class ConfigSelectView(discord.ui.View):
    def __init__(self, *, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.add_item(ConfigSelectMenu())


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = DatabaseController().guild_config

    @app_commands.command(name="config_set_roles", description="Configure the guild roles.")
    async def config_set_roles(
        self,
        interaction: discord.Interaction,
    ) -> None:
        view = ConfigSelectView()
        await interaction.response.send_message("Select a setting to configure.", view=view, ephemeral=True)

    # @commands.hybrid_group(name="config", description="Guild configuration commands.", alias="cfg")
    # async def config(self, ctx: commands.Context[commands.Bot]) -> None:
    #     if ctx.invoked_subcommand is None:
    #         await ctx.send_help("config")

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_dev_role", description="Set the dev role for the guild.")
    # async def set_dev_role(self, ctx: commands.Context[commands.Bot], role: discord.Role) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_dev_role_id(ctx.guild.id, role.id)
    #     await ctx.reply(f"Dev role set to {role.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_admin_role", description="Set the admin role for the guild.")
    # async def set_admin_role(self, ctx: commands.Context[commands.Bot], role: discord.Role) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_admin_role_id(ctx.guild.id, role.id)
    #     await ctx.reply(f"Admin role set to {role.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_senior_role", description="Set the senior role for the guild.")
    # async def set_senior_role(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     role: discord.Role,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_senior_role_id(ctx.guild.id, role.id)
    #     await ctx.reply(f"Senior role set to {role.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_staff_role", description="Set the base staff role for the guild.")
    # async def set_staff_role(self, ctx: commands.Context[commands.Bot], role: discord.Role) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_base_staff_role_id(ctx.guild.id, role.id)
    #     await ctx.reply(f"Staff role set to {role.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_member_role", description="Set the base member role for the guild.")
    # async def set_member_role(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     role: discord.Role,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_base_member_role_id(ctx.guild.id, role.id)
    #     await ctx.reply(f"Member role set to {role.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_junior_role", description="Set the junior role for the guild.")
    # async def set_junior_role(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     role: discord.Role,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_junior_role_id(ctx.guild.id, role.id)
    #     await ctx.reply(f"Junior role set to {role.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_jail_role", description="Set the jail role for the guild.")
    # async def set_jail_role(self, ctx: commands.Context[commands.Bot], role: discord.Role) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_jail_role_id(ctx.guild.id, role.id)
    #     await ctx.reply(f"Jail role set to {role.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(
    #     name="set_quarantine_role",
    #     description="Set the quarantine role for the guild.",
    # )
    # async def set_quarantine_role(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     role: discord.Role,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_quarantine_role_id(ctx.guild.id, role.id)
    #     await ctx.reply(f"Quarantine role set to {role.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_mod_role", description="Set the moderator role for the guild.")
    # async def set_mod_role(self, ctx: commands.Context[commands.Bot], role: discord.Role) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_mod_role_id(ctx.guild.id, role.id)
    #     await ctx.reply(f"Moderator role set to {role.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_mod_log", description="Set the mod log channel for the guild.")
    # async def set_mod_log(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     channel: discord.TextChannel,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_mod_log_channel_id(ctx.guild.id, channel.id)
    #     await ctx.reply(f"Mod log channel set to {channel.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_audit_log", description="Set the audit log channel for the guild.")
    # async def set_audit_log(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     channel: discord.TextChannel,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_audit_log_channel_id(ctx.guild.id, channel.id)
    #     await ctx.reply(f"Audit log channel set to {channel.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_join_log", description="Set the join log channel for the guild.")
    # async def set_join_log(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     channel: discord.TextChannel,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_join_log_channel_id(ctx.guild.id, channel.id)
    #     await ctx.reply(f"Join log channel set to {channel.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(
    #     name="set_private_log",
    #     description="Set the private log channel for the guild.",
    # )
    # async def set_private_log(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     channel: discord.TextChannel,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_private_log_channel_id(ctx.guild.id, channel.id)
    #     await ctx.reply(f"Private log channel set to {channel.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_report_log", description="Set the report log channel for the guild.")
    # async def set_report_log(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     channel: discord.TextChannel,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_report_log_channel_id(ctx.guild.id, channel.id)
    #     await ctx.reply(f"Report log channel set to {channel.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_dev_log", description="Set the dev log channel for the guild.")
    # async def set_dev_log(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     channel: discord.TextChannel,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_dev_log_channel_id(ctx.guild.id, channel.id)
    #     await ctx.reply(f"Dev log channel set to {channel.mention}.", ephemeral=True)

    # @commands.command(name="set_jail_channel", description="Set the jail channel for the guild.")
    # async def set_jail_channel(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     channel: discord.TextChannel,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_jail_channel_id(ctx.guild.id, channel.id)
    #     await ctx.reply(f"Jail channel set to {channel.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(
    #     name="set_starboard_channel",
    #     description="Set the starboard channel for the guild.",
    # )
    # async def set_starboard_channel(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     channel: discord.TextChannel,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_starboard_channel_id(ctx.guild.id, channel.id)
    #     await ctx.reply(f"Starboard channel set to {channel.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_mod_channel", description="Set the mod channel for the guild.")
    # async def set_mod_channel(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     channel: discord.TextChannel,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_mod_channel_id(ctx.guild.id, channel.id)
    #     await ctx.reply(f"Mod channel set to {channel.mention}.", ephemeral=True)

    # @commands.has_perms(administrator=True)
    # @config.command(name="set_bot_channel", description="Set the bot channel for the guild.")
    # async def set_bot_channel(
    #     self,
    #     ctx: commands.Context[commands.Bot],
    #     channel: discord.TextChannel,
    # ) -> None:
    #     if ctx.guild is None:
    #         return
    #     await self.db.update_guild_bot_channel_id(ctx.guild.id, channel.id)
    #     await ctx.reply(f"Bot channel set to {channel.mention}.", ephemeral=True)

    # We will use a single command to set all the roles and channels by using a select menu.

    # @app_commands.command(name="config_set_channels", description="Configure the guild channels.")
    # @app_commands.describe(setting="Which setting to configure")
    # @app_commands.choices(
    #     setting=[
    #         app_commands.Choice(name="Mod Log", value="mod_log"),
    #         app_commands.Choice(name="Audit Log", value="audit_log"),
    #         app_commands.Choice(name="Join Log", value="join_log"),
    #         app_commands.Choice(name="Private Log", value="private_log"),
    #         app_commands.Choice(name="Report Log", value="report_log"),
    #         app_commands.Choice(name="Dev Log", value="dev_log"),
    #         app_commands.Choice(name="Jail Channel", value="jail_channel"),
    #         app_commands.Choice(name="Starboard Channel", value="starboard_channel"),
    #         app_commands.Choice(name="General Channel", value="general_channel"),
    #     ],
    # )
    # async def config_set_channels(
    #     self,
    #     interaction: discord.Interaction,
    #     setting: discord.app_commands.Choice[str],
    #     channel: discord.TextChannel,
    # ) -> None:
    #     if interaction.guild is None:
    #         return

    #     if setting == "mod_log":
    #         await self.db.update_mod_log_id(interaction.guild.id, channel.id)
    #         await interaction.response.send_message(f"Mod log channel set to {channel.mention}.", ephemeral=True)
    #     elif setting == "audit_log":
    #         await self.db.update_audit_log_id(interaction.guild.id, channel.id)
    #         await interaction.response.send_message(f"Audit log channel set to {channel.mention}.", ephemeral=True)
    #     elif setting == "join_log":
    #         await self.db.update_join_log_id(interaction.guild.id, channel.id)
    #         await interaction.response.send_message(f"Join log channel set to {channel.mention}.", ephemeral=True)
    #     elif setting == "private_log":
    #         await self.db.update_private_log_id(interaction.guild.id, channel.id)
    #         await interaction.response.send_message(f"Private log channel set to {channel.mention}.", ephemeral=True)
    #     elif setting == "report_log":
    #         await self.db.update_report_log_id(interaction.guild.id, channel.id)
    #         await interaction.response.send_message(f"Report log channel set to {channel.mention}.", ephemeral=True)
    #     elif setting == "dev_log":
    #         await self.db.update_dev_log_id(interaction.guild.id, channel.id)
    #         await interaction.response.send_message(f"Dev log channel set to {channel.mention}.", ephemeral=True)
    #     elif setting == "jail_channel":
    #         await self.db.update_jail_channel_id(interaction.guild.id, channel.id)
    #         await interaction.response.send_message(f"Jail channel set to {channel.mention}.", ephemeral=True)
    #     elif setting == "starboard_channel":
    #         await self.db.update_starboard_channel_id(interaction.guild.id, channel.id)
    #         await interaction.response.send_message(f"Starboard channel set to {channel.mention}.", ephemeral=True)
    #     elif setting == "general_channel":
    #         await self.db.update_general_channel_id(interaction.guild.id, channel.id)
    #         await interaction.response.send_message(f"General channel set to {channel.mention}.", ephemeral=True)

    # @app_commands.command(name="config_set_roles", description="Configure the guild roles.")
    # @app_commands.describe(setting="Which setting to configure")
    # @app_commands.choices(
    #     setting=[
    #         app_commands.Choice(name="Base Member Role", value="base_member_role"),
    #         app_commands.Choice(name="Base Staff Role", value="base_staff_role"),
    #         app_commands.Choice(name="Jail Role", value="jail_role"),
    #         app_commands.Choice(name="Quarantine Role", value="quarantine_role"),
    #         app_commands.Choice(name="Perm Level 0 Roles", value="perm_level_0_roles"),
    #         app_commands.Choice(name="Perm Level 1 Roles", value="perm_level_1_roles"),
    #         app_commands.Choice(name="Perm Level 2 Roles", value="perm_level_2_roles"),
    #         app_commands.Choice(name="Perm Level 3 Roles", value="perm_level_3_roles"),
    #         app_commands.Choice(name="Perm Level 4 Roles", value="perm_level_4_roles"),
    #         app_commands.Choice(name="Perm Level 5 Roles", value="perm_level_5_roles"),
    #         app_commands.Choice(name="Perm Level 6 Roles", value="perm_level_6_roles"),
    #         app_commands.Choice(name="Perm Level 7 Roles", value="perm_level_7_roles"),
    #         app_commands.Choice(name="Perm Level 8 Roles", value="perm_level_8_roles"),
    #         app_commands.Choice(name="Perm Level 9 Roles", value="perm_level_9_roles"),
    #     ],
    # )
    # async def config_set_roles(
    #     self,
    #     interaction: discord.Interaction,
    #     setting: discord.app_commands.Choice[str],
    #     role: discord.Role,
    # ) -> None:
    #     if interaction.guild is None:
    #         return

    #     if setting == "base_member_role":
    #         await self.db.update_base_member_role_id(interaction.guild.id, role.id)
    #         await interaction.response.send_message(f"Base member role set to {role.mention}.", ephemeral=True)
    #     elif setting == "base_staff_role":
    #         await self.db.update_base_staff_role_id(interaction.guild.id, role.id)
    #         await interaction.response.send_message(f"Base staff role set to {role.mention}.", ephemeral=True)
    #     elif setting == "jail_role":
    #         await self.db.update_jail_role_id(interaction.guild.id, role.id)
    #         await interaction.response.send_message(f"Jail role set to {role.mention}.", ephemeral=True)
    #     elif setting == "quarantine_role":
    #         await self.db.update_quarantine_role_id(interaction.guild.id, role.id)
    #         await interaction.response.send_message(f"Quarantine role set to {role.mention}.", ephemeral=True)
    #     elif setting == "perm_level_0_roles":
    #         await self.db.update_guild_config(
    #             interaction.guild.id,
    #             data={
    #                 "perm_level_0_roles": {
    #                     "push": [role.id],
    #                 }
    #             },
    #         )
    #         await interaction.response.send_message(f"Perm level 0 roles set to {role.mention}.", ephemeral=True)
    #     elif setting == "perm_level_1_roles":
    #         await self.db.update_guild_config(
    #             interaction.guild.id,
    #             data={
    #                 "perm_level_1_roles": {
    #                     "push": [role.id],
    #                 }
    #             },
    #         )
    #         await interaction.response.send_message(f"Perm level 1 roles set to {role.mention}.", ephemeral=True)
    #     elif setting == "perm_level_2_roles":
    #         await self.db.update_guild_config(
    #             interaction.guild.id,
    #             data={
    #                 "perm_level_2_roles": {
    #                     "push": [role.id],
    #                 }
    #             },
    #         )
    #         await interaction.response.send_message(f"Perm level 2 roles set to {role.mention}.", ephemeral=True)
    #     elif setting == "perm_level_3_roles":
    #         await self.db.update_guild_config(
    #             interaction.guild.id,
    #             data={
    #                 "perm_level_3_roles": {
    #                     "push": [role.id],
    #                 }
    #             },
    #         )
    #         await interaction.response.send_message(f"Perm level 3 roles set to {role.mention}.", ephemeral=True)
    #     elif setting == "perm_level_4_roles":
    #         await self.db.update_guild_config(
    #             interaction.guild.id,
    #             data={
    #                 "perm_level_4_roles": {
    #                     "push": [role.id],
    #                 }
    #             },
    #         )
    #         await interaction.response.send_message(f"Perm level 4 roles set to {role.mention}.", ephemeral=True)
    #     elif setting == "perm_level_5_roles":
    #         await self.db.update_guild_config(
    #             interaction.guild.id,
    #             data={
    #                 "perm_level_5_roles": {
    #                     "push": [role.id],
    #                 }
    #             },
    #         )
    #         await interaction.response.send_message(f"Perm level 5 roles set to {role.mention}.", ephemeral=True)
    #     elif setting == "perm_level_6_roles":
    #         await self.db.update_guild_config(
    #             interaction.guild.id,
    #             data={
    #                 "perm_level_6_roles": {
    #                     "push": [role.id],
    #                 }
    #             },
    #         )
    #         await interaction.response.send_message(f"Perm level 6 roles set to {role.mention}.", ephemeral=True)
    #     elif setting == "perm_level_7_roles":
    #         await self.db.update_guild_config(
    #             interaction.guild.id,
    #             data={
    #                 "perm_level_7_roles": {
    #                     "push": [role.id],
    #                 }
    #             },
    #         )
    #         await interaction.response.send_message(f"Perm level 7 roles set to {role.mention}.", ephemeral=True)
    #     elif setting == "perm_level_8_roles":
    #         await self.db.update_guild_config(
    #             interaction.guild.id,
    #             data={
    #                 "perm_level_8_roles": {
    #                     "push": [role.id],
    #                 }
    #             },
    #         )
    #         await interaction.response.send_message(f"Perm level 8 roles set to {role.mention}.", ephemeral=True)
    #     elif setting == "perm_level_9_roles":
    #         await self.db.update_guild_config(
    #             interaction.guild.id,
    #             data={
    #                 "perm_level_9_roles": {
    #                     "push": [role.id],
    #                 }
    #             },
    #         )
    #         await interaction.response.send_message(f"Perm level 9 roles set to {role.mention}.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Config(bot))
