from __future__ import annotations

from typing import Any

from tux.database.controllers.base import BaseController
from tux.database.models import GuildConfig
from tux.database.service import DatabaseService


class GuildConfigController(BaseController[GuildConfig]):
    """Clean GuildConfig controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None):
        super().__init__(GuildConfig, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_config_by_guild_id(self, guild_id: int) -> GuildConfig | None:
        """Get guild configuration by guild ID."""
        return await self.get_by_id(guild_id)

    async def get_or_create_config(self, guild_id: int, **defaults: Any) -> GuildConfig:
        """Get guild configuration, or create it with defaults if it doesn't exist."""
        # Note: Guild existence should be ensured at a higher level (service/application)
        # This method assumes the guild exists to avoid circular dependencies
        config, _ = await self.get_or_create(defaults=defaults, guild_id=guild_id)
        return config

    async def update_config(self, guild_id: int, **updates: Any) -> GuildConfig | None:
        """Update guild configuration."""
        return await self.update_by_id(guild_id, **updates)

    async def delete_config(self, guild_id: int) -> bool:
        """Delete guild configuration."""
        return await self.delete_by_id(guild_id)

    async def get_all_configs(self) -> list[GuildConfig]:
        """Get all guild configurations."""
        return await self.find_all()

    async def get_config_count(self) -> int:
        """Get the total number of guild configurations."""
        return await self.count()

    async def find_configs_by_field(self, field_name: str, field_value: Any) -> list[GuildConfig]:
        """Find configurations by a specific field value."""
        return await self.find_all(filters=getattr(GuildConfig, field_name) == field_value)

    async def update_config_field(self, guild_id: int, field_name: str, field_value: Any) -> GuildConfig | None:
        """Update a specific field in guild configuration."""
        return await self.update_by_id(guild_id, **{field_name: field_value})

    async def update_channel_field(self, guild_id: int, channel_field: str, channel_id: int) -> GuildConfig | None:
        """Update a channel field in guild configuration."""
        return await self.update_config_field(guild_id, channel_field, channel_id)

    async def get_configs_by_prefix(self, prefix: str) -> list[GuildConfig]:
        """Get configurations where guild ID starts with a prefix."""
        # This would need a custom SQL query, but for now we'll use find_all
        # and filter in Python. In production, you might want to use with_session
        # for more complex queries.
        all_configs = await self.find_all()
        return [config for config in all_configs if str(config.guild_id).startswith(prefix)]

    # Additional methods that module files expect
    async def update_perm_level_role(
        self,
        guild_id: int,
        role_id: int | str,
        perm_level: int | str,
    ) -> GuildConfig | None:
        """Update permission level role for a guild."""
        # Handle both int and str inputs for flexibility
        if isinstance(role_id, str):
            # Convert string role_id to int if possible, or handle special cases
            if role_id == "jail":
                return await self.update_config(guild_id, jail_role_id=None)
            # For other string role_ids, you might want to handle differently
            return None

        # Handle both int and str perm_level
        if isinstance(perm_level, str):
            # Convert string perm_level to appropriate field name
            field_name = f"perm_level_{perm_level}_role_id"
            return await self.update_config(guild_id, **{field_name: role_id})

        # Handle int perm_level
        field_name = f"perm_level_{perm_level}_role_id"
        return await self.update_config(guild_id, **{field_name: role_id})

    async def get_config_field(self, guild_id: int, field_name: str) -> Any:
        """Get any field from guild configuration."""
        config = await self.get_config_by_guild_id(guild_id)
        return getattr(config, field_name, None) if config else None

    async def get_jail_role_id(self, guild_id: int) -> int | None:
        """Get jail role ID for a guild."""
        return await self.get_config_field(guild_id, "jail_role_id")

    async def get_perm_level_role(self, guild_id: int, perm_level: str) -> int | None:
        """Get role ID for a specific permission level."""
        return await self.get_config_field(guild_id, f"perm_level_{perm_level}_role_id")

    async def get_jail_channel_id(self, guild_id: int) -> int | None:
        """Get jail channel ID for a guild."""
        return await self.get_config_field(guild_id, "jail_channel_id")

    # Channel update methods for UI compatibility
    async def update_private_log_id(self, guild_id: int, channel_id: int) -> GuildConfig | None:
        """Update private log channel ID."""
        return await self.update_channel_field(guild_id, "private_log_id", channel_id)

    async def update_report_log_id(self, guild_id: int, channel_id: int) -> GuildConfig | None:
        """Update report log channel ID."""
        return await self.update_channel_field(guild_id, "report_log_id", channel_id)

    async def update_dev_log_id(self, guild_id: int, channel_id: int) -> GuildConfig | None:
        """Update dev log channel ID."""
        return await self.update_channel_field(guild_id, "dev_log_id", channel_id)

    async def update_mod_log_id(self, guild_id: int, channel_id: int) -> GuildConfig | None:
        """Update mod log channel ID."""
        return await self.update_channel_field(guild_id, "mod_log_id", channel_id)

    async def update_audit_log_id(self, guild_id: int, channel_id: int) -> GuildConfig | None:
        """Update audit log channel ID."""
        return await self.update_channel_field(guild_id, "audit_log_id", channel_id)

    async def update_join_log_id(self, guild_id: int, channel_id: int) -> GuildConfig | None:
        """Update join log channel ID."""
        return await self.update_channel_field(guild_id, "join_log_id", channel_id)

    async def update_jail_channel_id(self, guild_id: int, channel_id: int) -> GuildConfig | None:
        """Update jail channel ID."""
        return await self.update_channel_field(guild_id, "jail_channel_id", channel_id)

    async def update_starboard_channel_id(self, guild_id: int, channel_id: int) -> GuildConfig | None:
        """Update starboard channel ID."""
        return await self.update_channel_field(guild_id, "starboard_channel_id", channel_id)

    async def update_general_channel_id(self, guild_id: int, channel_id: int) -> GuildConfig | None:
        """Update general channel ID."""
        return await self.update_channel_field(guild_id, "general_channel_id", channel_id)

    async def get_starboard_channel_id(self, guild_id: int) -> int | None:
        """Get starboard channel ID for a guild."""
        return await self.get_config_field(guild_id, "starboard_channel_id")

    async def get_general_channel_id(self, guild_id: int) -> int | None:
        """Get general channel ID for a guild."""
        return await self.get_config_field(guild_id, "general_channel_id")

    async def get_join_log_id(self, guild_id: int) -> int | None:
        """Get join log channel ID for a guild."""
        return await self.get_config_field(guild_id, "join_log_id")

    async def get_audit_log_id(self, guild_id: int) -> int | None:
        """Get audit log channel ID for a guild."""
        return await self.get_config_field(guild_id, "audit_log_id")

    async def get_mod_log_id(self, guild_id: int) -> int | None:
        """Get mod log channel ID for a guild."""
        return await self.get_config_field(guild_id, "mod_log_id")

    async def get_private_log_id(self, guild_id: int) -> int | None:
        """Get private log channel ID for a guild."""
        return await self.get_config_field(guild_id, "private_log_id")

    async def get_report_log_id(self, guild_id: int) -> int | None:
        """Get report log channel ID for a guild."""
        return await self.get_config_field(guild_id, "report_log_id")

    async def get_dev_log_id(self, guild_id: int) -> int | None:
        """Get dev log channel ID for a guild."""
        return await self.get_config_field(guild_id, "dev_log_id")

    async def update_guild_prefix(self, guild_id: int, prefix: str) -> GuildConfig | None:
        """Update guild prefix."""
        return await self.update_config(guild_id, prefix=prefix)

    async def delete_guild_prefix(self, guild_id: int) -> GuildConfig | None:
        """Delete guild prefix (set to default)."""
        return await self.update_config(guild_id, prefix=None)

    async def get_log_channel(self, guild_id: int, log_type: str | None = None) -> int | None:
        """Get log channel ID for a guild based on log type."""
        config = await self.get_config_by_guild_id(guild_id)
        if not config:
            return None

        # Map log types to config fields
        log_type_mapping = {
            "mod": "mod_log_id",
            "audit": "audit_log_id",
            "join": "join_log_id",
            "private": "private_log_id",
            "report": "report_log_id",
            "dev": "dev_log_id",
        }

        if log_type and log_type in log_type_mapping:
            field_name = log_type_mapping[log_type]
            return getattr(config, field_name, None)

        # Default to mod_log_id
        return getattr(config, "mod_log_id", None)
