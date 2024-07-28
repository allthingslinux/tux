from typing import Any

from prisma.models import Guild, GuildConfig
from prisma.types import (
    GuildConfigScalarFieldKeys,
    GuildConfigUpdateInput,
)
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

    async def get_guild_config(self, guild_id: int) -> GuildConfig | None:
        return await self.table.find_first(where={"guild_id": guild_id})

    async def insert_guild_config(self, guild_id: int) -> GuildConfig:
        await self.ensure_guild_exists(guild_id)
        return await self.table.create(data={"guild_id": guild_id})

    async def delete_guild_config(self, guild_id: int) -> None:
        await self.table.delete(where={"guild_id": guild_id})

    async def get_log_channel(self, guild_id: int, log_type: str) -> int | None:
        log_channel_ids: dict[str, GuildConfigScalarFieldKeys] = {
            "mod": "mod_log_id",
            "audit": "audit_log_id",
            "join": "join_log_id",
            "private": "private_log_id",
            "report": "report_log_id",
            "dev": "dev_log_id",
        }
        return await self.get_guild_config_field_value(guild_id, log_channel_ids[log_type])

    async def update_mod_log_id(
        self,
        guild_id: int,
        mod_log_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "mod_log_id": mod_log_id,
                },
                "update": {"mod_log_id": mod_log_id},
            },
        )

    async def update_audit_log_id(
        self,
        guild_id: int,
        audit_log_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "audit_log_id": audit_log_id,
                },
                "update": {"audit_log_id": audit_log_id},
            },
        )

    async def update_join_log_id(
        self,
        guild_id: int,
        join_log_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "join_log_id": join_log_id,
                },
                "update": {"join_log_id": join_log_id},
            },
        )

    async def update_private_log_id(
        self,
        guild_id: int,
        private_log_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "private_log_id": private_log_id,
                },
                "update": {"private_log_id": private_log_id},
            },
        )

    async def update_report_log_id(
        self,
        guild_id: int,
        report_log_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "report_log_id": report_log_id,
                },
                "update": {"report_log_id": report_log_id},
            },
        )

    async def update_dev_log_id(
        self,
        guild_id: int,
        dev_log_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "dev_log_id": dev_log_id,
                },
                "update": {"dev_log_id": dev_log_id},
            },
        )

    async def update_jail_channel_id(
        self,
        guild_id: int,
        jail_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, "jail_channel_id": jail_channel_id},
                "update": {"jail_channel_id": jail_channel_id},
            },
        )

    async def update_general_channel_id(
        self,
        guild_id: int,
        general_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "general_channel_id": general_channel_id,
                },
                "update": {"general_channel_id": general_channel_id},
            },
        )

    async def update_starboard_channel_id(
        self,
        guild_id: int,
        starboard_channel_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "starboard_channel_id": starboard_channel_id,
                },
                "update": {"starboard_channel_id": starboard_channel_id},
            },
        )

    async def update_base_staff_role_id(
        self,
        guild_id: int,
        base_staff_role_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "base_staff_role_id": base_staff_role_id,
                },
                "update": {"base_staff_role_id": base_staff_role_id},
            },
        )

    async def update_base_member_role_id(
        self,
        guild_id: int,
        base_member_role_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "base_member_role_id": base_member_role_id,
                },
                "update": {"base_member_role_id": base_member_role_id},
            },
        )

    async def update_jail_role_id(
        self,
        guild_id: int,
        jail_role_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, "jail_role_id": jail_role_id},
                "update": {"jail_role_id": jail_role_id},
            },
        )

    async def update_quarantine_role_id(
        self,
        guild_id: int,
        quarantine_role_id: int,
    ) -> GuildConfig | None:
        await self.ensure_guild_exists(guild_id)
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {
                    "guild_id": guild_id,
                    "quarantine_role_id": quarantine_role_id,
                },
                "update": {"quarantine_role_id": quarantine_role_id},
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
        await self.ensure_guild_exists(guild_id)

        return await self.table.update(where={"guild_id": guild_id}, data=data)

    async def get_guild_config_field_value(
        self,
        guild_id: int,
        field: GuildConfigScalarFieldKeys,
    ) -> Any:
        config = await self.table.find_first(where={"guild_id": guild_id})
        return None if config is None else getattr(config, field)

    async def get_mod_log_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "mod_log_id")

    async def get_audit_log_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "audit_log_id")

    async def get_join_log_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "join_log_id")

    async def get_private_log_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "private_log_id")

    async def get_report_log_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "report_log_id")

    async def get_dev_log_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "dev_log_id")

    async def get_jail_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "jail_channel_id")

    async def get_general_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "general_channel_id")

    async def get_starboard_channel(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "starboard_channel_id")

    async def get_base_staff_role(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "base_staff_role_id")

    async def get_base_member_role(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "base_member_role_id")

    async def get_jail_role(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "jail_role_id")

    async def get_quarantine_role(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "quarantine_role_id")

    # async def get_disabled_commands(self, guild_id: int) -> list[str] | None:
    #     return await self.get_guild_config_field_value(guild_id, "guild_disabled_commands")

    # async def get_disabled_cogs(self, guild_id: int) -> list[str] | None:
    #     return await self.get_guild_config_field_value(guild_id, "guild_disabled_cogs")

    async def update_perm_level_roles(
        self,
        guild_id: int,
        level: str,
        role: int,
    ) -> GuildConfig | None:
        perm_level_roles = {
            "0": "perm_level_0_roles",
            "1": "perm_level_1_roles",
            "2": "perm_level_2_roles",
            "3": "perm_level_3_roles",
            "4": "perm_level_4_roles",
            "5": "perm_level_5_roles",
            "6": "perm_level_6_roles",
            "7": "perm_level_7_roles",
            "8": "perm_level_8_roles",
            "9": "perm_level_9_roles",
        }

        return await self.table.update(
            where={"guild_id": guild_id},
            data={
                perm_level_roles[level]: {
                    "set": [role],  # type: ignore
                },
            },
        )
