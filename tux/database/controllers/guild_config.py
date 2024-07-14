from typing import Any

from prisma.models import Guild, GuildConfig
from prisma.types import GuildConfigScalarFieldKeys, GuildConfigUpdateInput
from tux.database.client import db


class GuildConfigController:
    def __init__(self):
        self.table = db.guildconfig
        self.guild_table = db.guild

    async def ensure_guild_exists(self, guild_id: int) -> Guild | None:
        guild = await self.guild_table.find_first(where={"guild_id": guild_id})
        if guild is None:
            return await self.guild_table.create(data={"guild_id": guild_id})
        return guild

    async def get_guild_config_by_id(self, guild_id: int) -> GuildConfig | None:
        return await self.table.find_first(where={"guild_id": guild_id})

    async def insert_guild_config(self, guild_id: int) -> GuildConfig:
        await self.ensure_guild_exists(guild_id)
        return await self.table.create(data={"guild_id": guild_id})

    async def delete_guild_config_by_id(self, guild_id: int) -> None:
        await self.table.delete(where={"guild_id": guild_id})

    async def get_log_channel(self, guild_id: int, log_type: str) -> int | None:
        log_channel_ids: dict[str, GuildConfigScalarFieldKeys] = {
            "mod": "guild_mod_log_channel_id",
            "audit": "guild_audit_log_channel_id",
            "join": "guild_join_log_channel_id",
            "private": "guild_private_log_channel_id",
            "report": "guild_report_log_channel_id",
            "dev": "guild_dev_log_channel_id",
        }
        return await self.get_guild_config_field_value(guild_id, log_channel_ids[log_type])

    async def update_guild_mod_log_channel_id(
        self,
        guild_id: int,
        guild_mod_log_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "guild_mod_log_channel_id": guild_mod_log_channel_id,
                },
                "update": {"guild_mod_log_channel_id": guild_mod_log_channel_id},
            },
        )

    async def update_guild_audit_log_channel_id(
        self,
        guild_id: int,
        guild_audit_log_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "guild_audit_log_channel_id": guild_audit_log_channel_id,
                },
                "update": {"guild_audit_log_channel_id": guild_audit_log_channel_id},
            },
        )

    async def update_guild_join_log_channel_id(
        self,
        guild_id: int,
        guild_join_log_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "guild_join_log_channel_id": guild_join_log_channel_id,
                },
                "update": {"guild_join_log_channel_id": guild_join_log_channel_id},
            },
        )

    async def update_guild_private_log_channel_id(
        self,
        guild_id: int,
        guild_private_log_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "guild_private_log_channel_id": guild_private_log_channel_id,
                },
                "update": {"guild_private_log_channel_id": guild_private_log_channel_id},
            },
        )

    async def update_guild_report_log_channel_id(
        self,
        guild_id: int,
        guild_report_log_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "guild_report_log_channel_id": guild_report_log_channel_id,
                },
                "update": {"guild_report_log_channel_id": guild_report_log_channel_id},
            },
        )

    async def update_guild_dev_log_channel_id(
        self,
        guild_id: int,
        guild_dev_log_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "guild_dev_log_channel_id": guild_dev_log_channel_id,
                },
                "update": {"guild_dev_log_channel_id": guild_dev_log_channel_id},
            },
        )

    async def update_guild_jail_channel_id(
        self,
        guild_id: int,
        guild_jail_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, "guild_jail_channel_id": guild_jail_channel_id},
                "update": {"guild_jail_channel_id": guild_jail_channel_id},
            },
        )

    async def update_guild_general_channel_id(
        self,
        guild_id: int,
        guild_general_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "guild_general_channel_id": guild_general_channel_id,
                },
                "update": {"guild_general_channel_id": guild_general_channel_id},
            },
        )

    async def update_guild_starboard_channel_id(
        self,
        guild_id: int,
        guild_starboard_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "guild_starboard_channel_id": guild_starboard_channel_id,
                },
                "update": {"guild_starboard_channel_id": guild_starboard_channel_id},
            },
        )

    async def update_guild_mod_channel_id(
        self,
        guild_id: int,
        guild_mod_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, "guild_mod_channel_id": guild_mod_channel_id},
                "update": {"guild_mod_channel_id": guild_mod_channel_id},
            },
        )

    async def update_guild_bot_channel_id(
        self,
        guild_id: int,
        guild_bot_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, "guild_bot_channel_id": guild_bot_channel_id},
                "update": {"guild_bot_channel_id": guild_bot_channel_id},
            },
        )

    async def update_guild_dev_role_id(
        self,
        guild_id: int,
        guild_dev_role_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, "guild_dev_role_id": guild_dev_role_id},
                "update": {"guild_dev_role_id": guild_dev_role_id},
            },
        )

    async def update_guild_admin_role_id(
        self,
        guild_id: int,
        guild_admin_role_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, "guild_admin_role_id": guild_admin_role_id},
                "update": {"guild_admin_role_id": guild_admin_role_id},
            },
        )

    async def update_guild_senior_role_id(
        self,
        guild_id: int,
        guild_senior_role_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, "guild_senior_role_id": guild_senior_role_id},
                "update": {"guild_senior_role_id": guild_senior_role_id},
            },
        )

    async def update_guild_mod_role_id(
        self,
        guild_id: int,
        guild_mod_role_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, "guild_mod_role_id": guild_mod_role_id},
                "update": {"guild_mod_role_id": guild_mod_role_id},
            },
        )

    async def update_guild_junior_role_id(
        self,
        guild_id: int,
        guild_junior_role_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, "guild_junior_role_id": guild_junior_role_id},
                "update": {"guild_junior_role_id": guild_junior_role_id},
            },
        )

    async def update_guild_base_staff_role_id(
        self,
        guild_id: int,
        guild_base_staff_role_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "guild_base_staff_role_id": guild_base_staff_role_id,
                },
                "update": {"guild_base_staff_role_id": guild_base_staff_role_id},
            },
        )

    async def update_guild_base_member_role_id(
        self,
        guild_id: int,
        guild_base_member_role_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "guild_base_member_role_id": guild_base_member_role_id,
                },
                "update": {"guild_base_member_role_id": guild_base_member_role_id},
            },
        )

    async def update_guild_jail_role_id(
        self,
        guild_id: int,
        guild_jail_role_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, "guild_jail_role_id": guild_jail_role_id},
                "update": {"guild_jail_role_id": guild_jail_role_id},
            },
        )

    async def update_guild_quarantine_role_id(
        self,
        guild_id: int,
        guild_quarantine_role_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "guild_quarantine_role_id": guild_quarantine_role_id,
                },
                "update": {"guild_quarantine_role_id": guild_quarantine_role_id},
            },
        )

    # async def update_guild_disabled_commands(
    #     self, guild_id: int, guild_disabled_commands: list[str]
    # ) -> GuildConfig | None:
    #     return await self.table.update(
    #         where={"guild_id": guild_id},
    #         data={"guild_disabled_commands": guild_disabled_commands},
    #     )

    # async def update_guild_disabled_cogs(
    #     self, guild_id: int, guild_disabled_cogs: list[str]
    # ) -> GuildConfig | None:
    #     return await self.table.update(
    #         where={"guild_id": guild_id},
    #         data={"guild_disabled_cogs": guild_disabled_cogs},
    #     )

    async def update_guild_config(
        self,
        guild_id: int,
        data: GuildConfigUpdateInput,
    ) -> GuildConfig | None:
        return await self.table.update(where={"guild_id": guild_id}, data=data)

    async def get_guild_config_field_value(
        self,
        guild_id: int,
        field: GuildConfigScalarFieldKeys,
    ) -> Any:
        config = await self.table.find_first(where={"guild_id": guild_id})
        return None if config is None else getattr(config, field)

    async def get_mod_log_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_mod_log_channel_id")

    async def get_audit_log_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_audit_log_channel_id")

    async def get_join_log_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_join_log_channel_id")

    async def get_private_log_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_private_log_channel_id")

    async def get_report_log_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_report_log_channel_id")

    async def get_dev_log_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_dev_log_channel_id")

    async def get_jail_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_jail_channel_id")

    async def get_general_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_general_channel_id")

    async def get_starboard_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_starboard_channel_id")

    async def get_mod_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_mod_channel_id")

    async def get_bot_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_bot_channel_id")

    async def get_dev_role(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_dev_role_id")

    async def get_admin_role(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_admin_role_id")

    async def get_senior_role(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_senior_role_id")

    async def get_mod_role(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_mod_role_id")

    async def get_junior_role(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_junior_role_id")

    async def get_base_staff_role(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_base_staff_role_id")

    async def get_base_member_role(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_base_member_role_id")

    async def get_jail_role(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_jail_role_id")

    async def get_quarantine_role(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "guild_quarantine_role_id")

    # async def get_disabled_commands(self, guild_id: int) -> list[str] | None:
    #     return await self.get_guild_config_field_value(guild_id, "guild_disabled_commands")

    # async def get_disabled_cogs(self, guild_id: int) -> list[str] | None:
    #     return await self.get_guild_config_field_value(guild_id, "guild_disabled_cogs")

    async def get_all_guild_configs(self) -> list[GuildConfig]:
        return await self.table.find_many()
