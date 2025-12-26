"""
Guild configuration management controller.

This controller manages Discord guild configuration settings, including bot
preferences, moderation settings, and feature toggles for each guild.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tux.database.controllers.base import BaseController
from tux.database.models import GuildConfig

if TYPE_CHECKING:
    from tux.database.service import DatabaseService


class GuildConfigController(BaseController[GuildConfig]):
    """Clean GuildConfig controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None) -> None:
        """Initialize the guild config controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        """
        super().__init__(GuildConfig, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_config_by_guild_id(self, guild_id: int) -> GuildConfig | None:
        """
        Get guild configuration by guild ID.

        Returns
        -------
        GuildConfig | None
            The guild configuration if found, None otherwise.
        """
        return await self.get_by_id(guild_id)

    async def get_or_create_config(self, guild_id: int, **defaults: Any) -> GuildConfig:
        """
        Get guild configuration, or create it with defaults if it doesn't exist.

        Returns
        -------
        GuildConfig
            The guild configuration (existing or newly created).
        """
        # Note: Guild existence should be ensured at a higher level (service/application)
        # This method assumes the guild exists to avoid circular dependencies
        config, _ = await self.get_or_create(defaults=defaults, id=guild_id)
        return config

    async def update_config(self, guild_id: int, **updates: Any) -> GuildConfig | None:
        """
        Update guild configuration.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_by_id(guild_id, **updates)

    async def delete_config(self, guild_id: int) -> bool:
        """
        Delete guild configuration.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        return await self.delete_by_id(guild_id)

    async def get_all_configs(self) -> list[GuildConfig]:
        """
        Get all guild configurations.

        Returns
        -------
        list[GuildConfig]
            List of all guild configurations.
        """
        return await self.find_all()

    async def get_config_count(self) -> int:
        """
        Get the total number of guild configurations.

        Returns
        -------
        int
            The total count of guild configurations.
        """
        return await self.count()

    async def find_configs_by_field(
        self,
        field_name: str,
        field_value: Any,
    ) -> list[GuildConfig]:
        """
        Find configurations by a specific field value.

        Returns
        -------
        list[GuildConfig]
            List of configurations with matching field value.
        """
        return await self.find_all(
            filters=getattr(GuildConfig, field_name) == field_value,
        )

    async def update_config_field(
        self,
        guild_id: int,
        field_name: str,
        field_value: Any,
    ) -> GuildConfig | None:
        """
        Update a specific field in guild configuration.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_by_id(guild_id, **{field_name: field_value})

    # Onboarding-specific methods
    async def update_onboarding_stage(
        self,
        guild_id: int,
        stage: str,
    ) -> GuildConfig | None:
        """
        Update the onboarding stage for a guild.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_by_id(guild_id, onboarding_stage=stage)

    async def mark_onboarding_completed(self, guild_id: int) -> GuildConfig | None:
        """
        Mark onboarding as completed for a guild.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_by_id(
            guild_id,
            onboarding_completed=True,
            onboarding_stage="completed",
        )

    async def reset_onboarding(self, guild_id: int) -> GuildConfig | None:
        """
        Reset onboarding status for a guild.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_by_id(
            guild_id,
            onboarding_completed=False,
            onboarding_stage="not_started",
        )

    async def get_onboarding_status(self, guild_id: int) -> tuple[bool, str | None]:
        """
        Get onboarding status for a guild.

        Returns
        -------
        tuple[bool, str | None]
            Tuple of (completed, stage) for the guild's onboarding status.
        """
        config = await self.get_config_by_guild_id(guild_id)
        if config:
            return config.onboarding_completed, config.onboarding_stage
        return False, None

    async def update_channel_field(
        self,
        guild_id: int,
        channel_field: str,
        channel_id: int,
    ) -> GuildConfig | None:
        """
        Update a channel field in guild configuration.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_config_field(guild_id, channel_field, channel_id)

    async def get_configs_by_prefix(self, prefix: str) -> list[GuildConfig]:
        """
        Get configurations where guild ID starts with a prefix.

        Returns
        -------
        list[GuildConfig]
            List of configurations with matching guild ID prefix.
        """
        # This would need a custom SQL query, but for now we'll use find_all
        # and filter in Python. In production, you might want to use with_session
        # for more complex queries.
        all_configs = await self.find_all()
        return [config for config in all_configs if str(config.id).startswith(prefix)]

    # Additional methods that module files expect
    async def update_perm_level_role(
        self,
        guild_id: int,
        role_id: int | str,
        perm_level: int | str,
    ) -> GuildConfig | None:
        """
        Update permission level role for a guild.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
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
        """
        Get any field from guild configuration.

        Returns
        -------
        Any
            The field value, or None if configuration or field not found.
        """
        config = await self.get_config_by_guild_id(guild_id)
        return getattr(config, field_name, None) if config else None

    async def get_jail_role_id(self, guild_id: int) -> int | None:
        """
        Get jail role ID for a guild.

        Returns
        -------
        int | None
            The jail role ID, or None if not configured.
        """
        return await self.get_config_field(guild_id, "jail_role_id")

    # TODO: Remove/rename after investigation of use
    async def get_perm_level_role(self, guild_id: int, perm_level: str) -> int | None:
        """
        Get role ID for a specific permission level.

        Returns
        -------
        int | None
            The role ID for the permission level, or None if not configured.
        """
        return await self.get_config_field(guild_id, f"perm_level_{perm_level}_role_id")

    async def get_jail_channel_id(self, guild_id: int) -> int | None:
        """
        Get jail channel ID for a guild.

        Returns
        -------
        int | None
            The jail channel ID, or None if not configured.
        """
        return await self.get_config_field(guild_id, "jail_channel_id")

    # Channel update methods for UI compatibility
    async def update_private_log_id(
        self,
        guild_id: int,
        channel_id: int,
    ) -> GuildConfig | None:
        """
        Update private log channel ID.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_channel_field(guild_id, "private_log_id", channel_id)

    async def update_report_log_id(
        self,
        guild_id: int,
        channel_id: int,
    ) -> GuildConfig | None:
        """
        Update report log channel ID.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_channel_field(guild_id, "report_log_id", channel_id)

    async def update_dev_log_id(
        self,
        guild_id: int,
        channel_id: int,
    ) -> GuildConfig | None:
        """
        Update dev log channel ID.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_channel_field(guild_id, "dev_log_id", channel_id)

    async def update_mod_log_id(
        self,
        guild_id: int,
        channel_id: int,
    ) -> GuildConfig | None:
        """
        Update mod log channel ID.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_channel_field(guild_id, "mod_log_id", channel_id)

    async def update_audit_log_id(
        self,
        guild_id: int,
        channel_id: int,
    ) -> GuildConfig | None:
        """
        Update audit log channel ID.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_channel_field(guild_id, "audit_log_id", channel_id)

    async def update_join_log_id(
        self,
        guild_id: int,
        channel_id: int,
    ) -> GuildConfig | None:
        """
        Update join log channel ID.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_channel_field(guild_id, "join_log_id", channel_id)

    async def update_jail_channel_id(
        self,
        guild_id: int,
        channel_id: int,
    ) -> GuildConfig | None:
        """
        Update jail channel ID.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_channel_field(guild_id, "jail_channel_id", channel_id)

    async def update_starboard_channel_id(
        self,
        guild_id: int,
        channel_id: int,
    ) -> GuildConfig | None:
        """
        Update starboard channel ID.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_channel_field(
            guild_id,
            "starboard_channel_id",
            channel_id,
        )

    async def update_general_channel_id(
        self,
        guild_id: int,
        channel_id: int,
    ) -> GuildConfig | None:
        """
        Update general channel ID.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_channel_field(
            guild_id,
            "general_channel_id",
            channel_id,
        )

    async def get_starboard_channel_id(self, guild_id: int) -> int | None:
        """
        Get starboard channel ID for a guild.

        Returns
        -------
        int | None
            The starboard channel ID, or None if not configured.
        """
        return await self.get_config_field(guild_id, "starboard_channel_id")

    async def get_general_channel_id(self, guild_id: int) -> int | None:
        """
        Get general channel ID for a guild.

        Returns
        -------
        int | None
            The general channel ID, or None if not configured.
        """
        return await self.get_config_field(guild_id, "general_channel_id")

    async def get_join_log_id(self, guild_id: int) -> int | None:
        """
        Get join log channel ID for a guild.

        Returns
        -------
        int | None
            The join log channel ID, or None if not configured.
        """
        return await self.get_config_field(guild_id, "join_log_id")

    async def get_audit_log_id(self, guild_id: int) -> int | None:
        """
        Get audit log channel ID for a guild.

        Returns
        -------
        int | None
            The audit log channel ID, or None if not configured.
        """
        return await self.get_config_field(guild_id, "audit_log_id")

    async def get_mod_log_id(self, guild_id: int) -> int | None:
        """
        Get mod log channel ID for a guild.

        Returns
        -------
        int | None
            The mod log channel ID, or None if not configured.
        """
        return await self.get_config_field(guild_id, "mod_log_id")

    async def get_private_log_id(self, guild_id: int) -> int | None:
        """
        Get private log channel ID for a guild.

        Returns
        -------
        int | None
            The private log channel ID, or None if not configured.
        """
        return await self.get_config_field(guild_id, "private_log_id")

    async def get_report_log_id(self, guild_id: int) -> int | None:
        """
        Get report log channel ID for a guild.

        Returns
        -------
        int | None
            The report log channel ID, or None if not configured.
        """
        return await self.get_config_field(guild_id, "report_log_id")

    async def get_dev_log_id(self, guild_id: int) -> int | None:
        """
        Get dev log channel ID for a guild.

        Returns
        -------
        int | None
            The dev log channel ID, or None if not configured.
        """
        return await self.get_config_field(guild_id, "dev_log_id")

    async def update_guild_prefix(
        self,
        guild_id: int,
        prefix: str,
    ) -> GuildConfig | None:
        """
        Update guild prefix.

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_config(guild_id, prefix=prefix)

    async def delete_guild_prefix(self, guild_id: int) -> GuildConfig | None:
        """
        Delete guild prefix (set to default).

        Returns
        -------
        GuildConfig | None
            The updated configuration, or None if not found.
        """
        return await self.update_config(guild_id, prefix=None)

    async def get_log_channel(
        self,
        guild_id: int,
        log_type: str | None = None,
    ) -> int | None:
        """
        Get log channel ID for a guild based on log type.

        Returns
        -------
        int | None
            The log channel ID for the specified type, or None if not found.
        """
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
