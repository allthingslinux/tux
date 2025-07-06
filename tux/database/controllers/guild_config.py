from typing import Any

from loguru import logger

from tux.database.controllers.base import BaseController
from tux.database.schemas import GuildConfig


class GuildConfigController(BaseController[GuildConfig]):
    """Controller for managing GuildConfig records."""

    def __init__(self) -> None:
        super().__init__(GuildConfig)

    # --- Generic Field Reader ---

    async def get_field(self, guild_id: int, field: str) -> Any:
        """
        Fetch a single scalar field from GuildConfig.
        Returns None if the record or field does not exist.
        """
        cfg = await self.find_unique(where={"guild_id": guild_id})
        if cfg is None:
            logger.warning(f"No GuildConfig found for guild_id={guild_id}")
            return None
        value = self.safe_get_attr(cfg, field, None)
        logger.debug(f"GuildConfig[{guild_id}].{field} = {value!r}")
        return value

    # --- Read Methods ---

    async def get_guild_config(self, guild_id: int) -> GuildConfig | None:
        return await self.find_unique(where={"guild_id": guild_id})

    async def get_guild_prefix(self, guild_id: int) -> str | None:
        return await self.get_field(guild_id, "prefix")

    async def get_log_channel(self, guild_id: int, log_type: str) -> int | None:
        log_fields: dict[str, str] = {
            "mod": "mod_log_id",
            "audit": "audit_log_id",
            "join": "join_log_id",
            "private": "private_log_id",
            "report": "report_log_id",
            "dev": "dev_log_id",
        }
        field = log_fields.get(log_type)
        if field is None:
            logger.error(f"Unknown log_type '{log_type}'")
            return None
        return await self.get_field(guild_id, field)

    async def get_perm_level_role(self, guild_id: int, level: int) -> int | None:
        """
        Get the role id for a specific permission level.
        """
        field = f"perm_level_{level}_role_id"
        try:
            return await self.get_field(guild_id, field)
        except Exception as e:
            logger.error(f"Error getting perm level role {level} for guild {guild_id}: {e}")
            return None

    async def get_perm_level_roles(self, guild_id: int, lower_bound: int) -> list[int] | None:
        """
        Get the role ids for all permission levels from lower_bound up to 7.
        """
        try:
            role_ids: list[int] = []
            for lvl in range(lower_bound, 8):
                field = f"perm_level_{lvl}_role_id"
                rid = await self.get_field(guild_id, field)
                if rid is not None:
                    role_ids.append(rid)
            logger.debug(f"Retrieved perm roles >={lower_bound} for guild {guild_id}: {role_ids}")
        except Exception as e:
            logger.error(f"Error getting perm level roles for guild {guild_id}: {e}")
            return None
        else:
            return role_ids

    async def get_mod_log_id(self, guild_id: int) -> int | None:
        return await self.get_field(guild_id, "mod_log_id")

    async def get_audit_log_id(self, guild_id: int) -> int | None:
        return await self.get_field(guild_id, "audit_log_id")

    async def get_join_log_id(self, guild_id: int) -> int | None:
        return await self.get_field(guild_id, "join_log_id")

    async def get_private_log_id(self, guild_id: int) -> int | None:
        return await self.get_field(guild_id, "private_log_id")

    async def get_report_log_id(self, guild_id: int) -> int | None:
        return await self.get_field(guild_id, "report_log_id")

    async def get_dev_log_id(self, guild_id: int) -> int | None:
        return await self.get_field(guild_id, "dev_log_id")

    async def get_jail_channel_id(self, guild_id: int) -> int | None:
        return await self.get_field(guild_id, "jail_channel_id")

    async def get_general_channel_id(self, guild_id: int) -> int | None:
        return await self.get_field(guild_id, "general_channel_id")

    async def get_starboard_channel_id(self, guild_id: int) -> int | None:
        return await self.get_field(guild_id, "starboard_channel_id")

    async def get_base_staff_role_id(self, guild_id: int) -> int | None:
        return await self.get_field(guild_id, "base_staff_role_id")

    async def get_base_member_role_id(self, guild_id: int) -> int | None:
        return await self.get_field(guild_id, "base_member_role_id")

    async def get_jail_role_id(self, guild_id: int) -> int | None:
        return await self.get_field(guild_id, "jail_role_id")

    async def get_quarantine_role_id(self, guild_id: int) -> int | None:
        return await self.get_field(guild_id, "quarantine_role_id")

    # --- Generic Field Upserter ---

    async def _upsert_field(self, guild_id: int, field: str, value: Any) -> GuildConfig:
        """
        Upsert a single scalar field on GuildConfig, ensuring the
        GuildConfig row (and its guild relation) exists.
        """
        return await self.upsert(
            where={"guild_id": guild_id},
            create={
                field: value,
                "guild": self.connect_or_create_relation("guild_id", guild_id),
            },
            update={field: value},
        )

    # --- Write Methods ---

    async def update_guild_prefix(self, guild_id: int, prefix: str) -> GuildConfig:
        return await self._upsert_field(guild_id, "prefix", prefix)

    async def update_mod_log_id(self, guild_id: int, channel_id: int) -> GuildConfig:
        return await self._upsert_field(guild_id, "mod_log_id", channel_id)

    async def update_audit_log_id(self, guild_id: int, channel_id: int) -> GuildConfig:
        return await self._upsert_field(guild_id, "audit_log_id", channel_id)

    async def update_join_log_id(self, guild_id: int, channel_id: int) -> GuildConfig:
        return await self._upsert_field(guild_id, "join_log_id", channel_id)

    async def update_private_log_id(self, guild_id: int, channel_id: int) -> GuildConfig:
        return await self._upsert_field(guild_id, "private_log_id", channel_id)

    async def update_report_log_id(self, guild_id: int, channel_id: int) -> GuildConfig:
        return await self._upsert_field(guild_id, "report_log_id", channel_id)

    async def update_dev_log_id(self, guild_id: int, channel_id: int) -> GuildConfig:
        return await self._upsert_field(guild_id, "dev_log_id", channel_id)

    async def update_jail_channel_id(self, guild_id: int, cid: int) -> GuildConfig:
        return await self._upsert_field(guild_id, "jail_channel_id", cid)

    async def update_general_channel_id(self, guild_id: int, cid: int) -> GuildConfig:
        return await self._upsert_field(guild_id, "general_channel_id", cid)

    async def update_starboard_channel_id(self, guild_id: int, cid: int) -> GuildConfig:
        return await self._upsert_field(guild_id, "starboard_channel_id", cid)

    async def update_base_staff_role_id(self, guild_id: int, rid: int) -> GuildConfig:
        return await self._upsert_field(guild_id, "base_staff_role_id", rid)

    async def update_base_member_role_id(self, guild_id: int, rid: int) -> GuildConfig:
        return await self._upsert_field(guild_id, "base_member_role_id", rid)

    async def update_jail_role_id(self, guild_id: int, rid: int) -> GuildConfig:
        return await self._upsert_field(guild_id, "jail_role_id", rid)

    async def update_quarantine_role_id(self, guild_id: int, rid: int) -> GuildConfig:
        return await self._upsert_field(guild_id, "quarantine_role_id", rid)

    async def update_perm_level_role(self, guild_id: int, level: int, role_id: int) -> GuildConfig:
        field = f"perm_level_{level}_role_id"
        return await self._upsert_field(guild_id, field, role_id)

    async def update_guild_config(self, guild_id: int, data: dict[str, Any]) -> GuildConfig | None:
        return await self.update(where={"guild_id": guild_id}, data=data)

    # --- Delete Methods ---

    async def delete_guild_config(self, guild_id: int) -> GuildConfig | None:
        return await self.delete(where={"guild_id": guild_id})

    async def delete_guild_prefix(self, guild_id: int) -> GuildConfig | None:
        return await self.update(where={"guild_id": guild_id}, data={"prefix": None})
