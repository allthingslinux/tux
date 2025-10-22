"""Callback handlers for the onboarding wizard."""

from .channel import (
    handle_audit_log_channel_select,
    handle_dev_log_channel_select,
    handle_jail_channel_select,
    handle_join_log_channel_select,
    handle_mod_log_channel_select,
    handle_private_log_channel_select,
    handle_report_log_channel_select,
)
from .role import (
    handle_jail_role_select,
    handle_permission_rank_role_select,
)

__all__ = [
    "handle_audit_log_channel_select",
    "handle_dev_log_channel_select",
    "handle_jail_channel_select",
    "handle_jail_role_select",
    "handle_join_log_channel_select",
    "handle_mod_log_channel_select",
    "handle_permission_rank_role_select",
    "handle_private_log_channel_select",
    "handle_report_log_channel_select",
]
