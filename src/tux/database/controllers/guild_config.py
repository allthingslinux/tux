from __future__ import annotations

from typing import Any

from tux.database.controllers.base import BaseController, with_session
from tux.database.models.guild import GuildConfig


class GuildConfigController(BaseController):
    @with_session
    async def get_guild_config(self, guild_id: int, *, session: Any = None) -> GuildConfig | None:
        return await session.get(GuildConfig, guild_id)

    @with_session
    async def get_guild_prefix(self, guild_id: int, *, session: Any = None) -> str | None:
        cfg = await session.get(GuildConfig, guild_id)
        return None if cfg is None else cfg.prefix

    # Generic field updater
    @with_session
    async def _update_field(self, guild_id: int, field: str, value: int | str | None, *, session: Any = None) -> None:
        cfg = await session.get(GuildConfig, guild_id)
        if cfg is None:
            cfg = await GuildConfig.create(session, guild_id=guild_id)
        setattr(cfg, field, value)
        await session.flush()

    # Log channels
    async def update_private_log_id(self, guild_id: int, channel_id: int) -> None:
        await self._update_field(guild_id, "private_log_id", channel_id)

    async def update_report_log_id(self, guild_id: int, channel_id: int) -> None:
        await self._update_field(guild_id, "report_log_id", channel_id)

    async def update_dev_log_id(self, guild_id: int, channel_id: int) -> None:
        await self._update_field(guild_id, "dev_log_id", channel_id)

    async def update_mod_log_id(self, guild_id: int, channel_id: int) -> None:
        await self._update_field(guild_id, "mod_log_id", channel_id)

    async def update_audit_log_id(self, guild_id: int, channel_id: int) -> None:
        await self._update_field(guild_id, "audit_log_id", channel_id)

    async def update_join_log_id(self, guild_id: int, channel_id: int) -> None:
        await self._update_field(guild_id, "join_log_id", channel_id)

    # Log getters
    @with_session
    async def get_report_log_id(self, guild_id: int, *, session: Any = None) -> int | None:
        cfg = await session.get(GuildConfig, guild_id)
        return None if cfg is None else cfg.report_log_id

    @with_session
    async def get_audit_log_id(self, guild_id: int, *, session: Any = None) -> int | None:
        cfg = await session.get(GuildConfig, guild_id)
        return None if cfg is None else cfg.audit_log_id

    @with_session
    async def get_mod_log_id(self, guild_id: int, *, session: Any = None) -> int | None:
        cfg = await session.get(GuildConfig, guild_id)
        return None if cfg is None else cfg.mod_log_id

    @with_session
    async def get_join_log_id(self, guild_id: int, *, session: Any = None) -> int | None:
        cfg = await session.get(GuildConfig, guild_id)
        return None if cfg is None else cfg.join_log_id

    @with_session
    async def get_private_log_id(self, guild_id: int, *, session: Any = None) -> int | None:
        cfg = await session.get(GuildConfig, guild_id)
        return None if cfg is None else cfg.private_log_id

    @with_session
    async def get_dev_log_id(self, guild_id: int, *, session: Any = None) -> int | None:
        cfg = await session.get(GuildConfig, guild_id)
        return None if cfg is None else cfg.dev_log_id

    # Channels
    async def update_jail_channel_id(self, guild_id: int, channel_id: int) -> None:
        await self._update_field(guild_id, "jail_channel_id", channel_id)

    async def update_starboard_channel_id(self, guild_id: int, channel_id: int) -> None:
        await self._update_field(guild_id, "starboard_channel_id", channel_id)

    async def update_general_channel_id(self, guild_id: int, channel_id: int) -> None:
        await self._update_field(guild_id, "general_channel_id", channel_id)

    @with_session
    async def get_jail_channel_id(self, guild_id: int, *, session: Any = None) -> int | None:
        cfg = await session.get(GuildConfig, guild_id)
        return None if cfg is None else cfg.jail_channel_id

    @with_session
    async def get_starboard_channel_id(self, guild_id: int, *, session: Any = None) -> int | None:
        cfg = await session.get(GuildConfig, guild_id)
        return None if cfg is None else cfg.starboard_channel_id

    @with_session
    async def get_general_channel_id(self, guild_id: int, *, session: Any = None) -> int | None:
        cfg = await session.get(GuildConfig, guild_id)
        return None if cfg is None else cfg.general_channel_id

    # Role getters used in checks
    @with_session
    async def get_jail_role_id(self, guild_id: int, *, session: Any = None) -> int | None:
        cfg = await session.get(GuildConfig, guild_id)
        return None if cfg is None else cfg.jail_role_id

    # Perm-levels
    @with_session
    async def get_perm_level_role(self, guild_id: int, perm_field: str, *, session: Any = None) -> int | None:
        cfg = await session.get(GuildConfig, guild_id)
        return None if cfg is None else getattr(cfg, perm_field)

    @with_session
    async def update_perm_level_role(
        self, guild_id: int, perm_level: str, role_id: int, *, session: Any = None
    ) -> None:
        field = f"perm_level_{perm_level}_role_id"
        await self._update_field(guild_id, field, role_id)

    # Prefix
    async def update_guild_prefix(self, guild_id: int, prefix: str) -> None:
        await self._update_field(guild_id, "prefix", prefix)

    async def delete_guild_prefix(self, guild_id: int) -> None:
        await self._update_field(guild_id, "prefix", None)

    @with_session
    async def get_log_channel(self, guild_id: int, log_type: str, *, session: Any = None) -> int | None:
        cfg = await session.get(GuildConfig, guild_id)
        if cfg is None:
            return None
        mapping = {
            "mod": cfg.mod_log_id,
            "audit": cfg.audit_log_id,
            "join": cfg.join_log_id,
            "private": cfg.private_log_id,
            "report": cfg.report_log_id,
            "dev": cfg.dev_log_id,
        }
        return mapping.get(log_type)

        # Generic field getter for setup workflows

    @with_session
    async def get_guild_config_field_value(self, guild_id: int, field: str, *, session: Any = None) -> Any:
        cfg = await session.get(GuildConfig, guild_id)
        return None if cfg is None else getattr(cfg, field)
