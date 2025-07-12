from typing import Any

from database.client import db
from loguru import logger

from prisma.actions import GuildActions, GuildConfigActions
from prisma.models import Guild, GuildConfig
from prisma.types import (
    GuildConfigScalarFieldKeys,
    GuildConfigUpdateInput,
)


class GuildConfigController:
    def __init__(self):
        """Initialize the controller with database tables."""
        self.table: GuildConfigActions[GuildConfig] = db.client.guildconfig
        self.guild_table: GuildActions[Guild] = db.client.guild

    async def ensure_guild_exists(self, guild_id: int) -> Any:
        """Ensure the guild exists in the database."""
        guild: Any = await self.guild_table.find_first(where={"guild_id": guild_id})
        if guild is None:
            return await self.guild_table.create(data={"guild_id": guild_id})
        return guild

    async def insert_guild_config(self, guild_id: int) -> Any:
        """Insert a new guild config into the database."""
        await self.ensure_guild_exists(guild_id)
        return await self.table.create(data={"guild_id": guild_id})

    async def get_guild_config(self, guild_id: int) -> Any:
        """Get a guild config from the database."""
        return await self.table.find_first(where={"guild_id": guild_id})

    async def get_guild_prefix(self, guild_id: int) -> str | None:
        """Get a guild prefix from the database."""
        config: Any = await self.table.find_first(where={"guild_id": guild_id})
        return None if config is None else config.prefix

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

    async def get_perm_level_role(self, guild_id: int, level: str) -> int | None:
        """
        Get the role id for a specific permission level.
        """
        try:
            role_id = await self.get_guild_config_field_value(guild_id, level)  # type: ignore
            logger.debug(f"Retrieved role_id {role_id} for guild {guild_id} and level {level}")
        except Exception as e:
            logger.error(f"Error getting perm level role: {e}")
            return None
        return role_id

    async def get_perm_level_roles(self, guild_id: int, lower_bound: int) -> list[int] | None:
        """
        Get the role ids for all permission levels from the lower_bound up to but not including 8.
        """
        perm_level_roles: dict[int, str] = {
            0: "perm_level_0_role_id",
            1: "perm_level_1_role_id",
            2: "perm_level_2_role_id",
            3: "perm_level_3_role_id",
            4: "perm_level_4_role_id",
            5: "perm_level_5_role_id",
            6: "perm_level_6_role_id",
            7: "perm_level_7_role_id",
        }

        try:
            role_ids: list[int] = []

            for level in range(lower_bound, 8):
                if role_field := perm_level_roles.get(level):
                    role_id = await self.get_guild_config_field_value(guild_id, role_field)  # type: ignore

                    if role_id:
                        role_ids.append(role_id)

            logger.debug(f"Retrieved role_ids {role_ids} for guild {guild_id} with lower bound {lower_bound}")

        except Exception as e:
            logger.error(f"Error getting perm level roles: {e}")
            return None

        return role_ids

    async def get_guild_config_field_value(
        self,
        guild_id: int,
        field: GuildConfigScalarFieldKeys,
    ) -> Any:
        config: Any = await self.table.find_first(where={"guild_id": guild_id})

        if config is None:
            logger.warning(f"No guild config found for guild_id: {guild_id}")
            return None

        value = getattr(config, field, None)

        logger.debug(f"Retrieved field value for {field}: {value}")

        return value

    async def get_mod_log_id(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "mod_log_id")

    async def get_audit_log_id(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "audit_log_id")

    async def get_join_log_id(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "join_log_id")

    async def get_private_log_id(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "private_log_id")

    async def get_report_log_id(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "report_log_id")

    async def get_dev_log_id(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "dev_log_id")

    async def get_jail_channel_id(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "jail_channel_id")

    async def get_general_channel_id(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "general_channel_id")

    async def get_starboard_channel_id(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "starboard_channel_id")

    async def get_base_staff_role_id(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "base_staff_role_id")

    async def get_base_member_role_id(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "base_member_role_id")

    async def get_jail_role_id(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "jail_role_id")

    async def get_quarantine_role_id(self, guild_id: int) -> int | None:
        return await self.get_guild_config_field_value(guild_id, "quarantine_role_id")

    async def update_guild_prefix(
        self,
        guild_id: int,
        prefix: str,
    ) -> Any:
        await self.ensure_guild_exists(guild_id)

        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, "prefix": prefix},
                "update": {"prefix": prefix},
            },
        )

    async def update_perm_level_role(
        self,
        guild_id: int,
        level: str,
        role_id: int,
    ) -> Any:
        await self.ensure_guild_exists(guild_id)

        perm_level_roles: dict[str, str] = {
            "0": "perm_level_0_role_id",
            "1": "perm_level_1_role_id",
            "2": "perm_level_2_role_id",
            "3": "perm_level_3_role_id",
            "4": "perm_level_4_role_id",
            "5": "perm_level_5_role_id",
            "6": "perm_level_6_role_id",
            "7": "perm_level_7_role_id",
        }

        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id, perm_level_roles[level]: role_id},  # type: ignore
                "update": {perm_level_roles[level]: role_id},
            },
        )

    async def update_mod_log_id(
        self,
        guild_id: int,
        mod_log_id: int,
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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

    async def update_guild_config(
        self,
        guild_id: int,
        data: GuildConfigUpdateInput,
    ) -> Any:
        await self.ensure_guild_exists(guild_id)

        return await self.table.update(where={"guild_id": guild_id}, data=data)

    async def delete_guild_config(self, guild_id: int) -> None:
        await self.table.delete(where={"guild_id": guild_id})

    async def delete_guild_prefix(self, guild_id: int) -> None:
        await self.table.update(where={"guild_id": guild_id}, data={"prefix": None})
