"""
Revision ID: cb9d912934d3
Revises:
Create Date: 2025-08-19 00:51:42.713645
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "cb9d912934d3"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create the PostgreSQL ENUM type up front
    case_type_enum = postgresql.ENUM(
        "BAN",
        "UNBAN",
        "HACKBAN",
        "TEMPBAN",
        "KICK",
        "TIMEOUT",
        "UNTIMEOUT",
        "WARN",
        "JAIL",
        "UNJAIL",
        "SNIPPETBAN",
        "SNIPPETUNBAN",
        "POLLBAN",
        "POLLUNBAN",
        name="case_type_enum",
        create_type=True,
    )
    case_type_enum.create(op.get_bind(), checkfirst=True)

    # guild
    op.create_table(
        "guild",
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("guild_joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("case_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index("idx_guild_id", "guild", ["guild_id"])

    # guild_config
    op.create_table(
        "guild_config",
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("guild.guild_id"), primary_key=True),
        sa.Column("prefix", sa.String(length=10), nullable=True),
        sa.Column("mod_log_id", sa.BigInteger(), nullable=True),
        sa.Column("audit_log_id", sa.BigInteger(), nullable=True),
        sa.Column("join_log_id", sa.BigInteger(), nullable=True),
        sa.Column("private_log_id", sa.BigInteger(), nullable=True),
        sa.Column("report_log_id", sa.BigInteger(), nullable=True),
        sa.Column("dev_log_id", sa.BigInteger(), nullable=True),
        sa.Column("jail_channel_id", sa.BigInteger(), nullable=True),
        sa.Column("general_channel_id", sa.BigInteger(), nullable=True),
        sa.Column("starboard_channel_id", sa.BigInteger(), nullable=True),
        sa.Column("base_staff_role_id", sa.BigInteger(), nullable=True),
        sa.Column("base_member_role_id", sa.BigInteger(), nullable=True),
        sa.Column("jail_role_id", sa.BigInteger(), nullable=True),
        sa.Column("quarantine_role_id", sa.BigInteger(), nullable=True),
        sa.Column("perm_level_0_role_id", sa.BigInteger(), nullable=True),
        sa.Column("perm_level_1_role_id", sa.BigInteger(), nullable=True),
        sa.Column("perm_level_2_role_id", sa.BigInteger(), nullable=True),
        sa.Column("perm_level_3_role_id", sa.BigInteger(), nullable=True),
        sa.Column("perm_level_4_role_id", sa.BigInteger(), nullable=True),
        sa.Column("perm_level_5_role_id", sa.BigInteger(), nullable=True),
        sa.Column("perm_level_6_role_id", sa.BigInteger(), nullable=True),
        sa.Column("perm_level_7_role_id", sa.BigInteger(), nullable=True),
    )

    # snippet
    op.create_table(
        "snippet",
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snippet_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("snippet_name", sa.String(length=100), nullable=False),
        sa.Column("snippet_content", sa.String(length=4000), nullable=True),
        sa.Column("snippet_user_id", sa.BigInteger(), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("guild.guild_id"), nullable=False),
        sa.Column("uses", sa.Integer(), server_default="0", nullable=False),
        sa.Column("locked", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("alias", sa.String(length=100), nullable=True),
    )
    op.create_index("idx_snippet_name_guild", "snippet", ["snippet_name", "guild_id"], unique=True)

    # reminder
    op.create_table(
        "reminder",
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("reminder_content", sa.String(length=2000), nullable=False),
        sa.Column("reminder_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reminder_channel_id", sa.BigInteger(), nullable=False),
        sa.Column("reminder_user_id", sa.BigInteger(), nullable=False),
        sa.Column("reminder_sent", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("guild.guild_id"), nullable=False),
    )

    # afk
    op.create_table(
        "afk",
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("member_id", sa.BigInteger(), primary_key=True),
        sa.Column("nickname", sa.String(length=100), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("since", sa.DateTime(timezone=True), nullable=False),
        sa.Column("until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("guild.guild_id"), nullable=False),
        sa.Column("enforced", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("perm_afk", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index("idx_afk_member_guild", "afk", ["member_id", "guild_id"], unique=True)

    # levels
    op.create_table(
        "levels",
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("member_id", sa.BigInteger(), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("guild.guild_id"), primary_key=True),
        sa.Column("xp", sa.Float(), server_default="0", nullable=False),
        sa.Column("level", sa.Integer(), server_default="0", nullable=False),
        sa.Column("blacklisted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("last_message", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_levels_guild_xp", "levels", ["guild_id", "xp"])

    # custom_case_type
    op.create_table(
        "custom_case_type",
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("guild.guild_id"), nullable=False),
        sa.Column("type_name", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("severity_level", sa.Integer(), server_default="1", nullable=False),
        sa.Column("requires_duration", sa.Boolean(), server_default="false", nullable=False),
    )

    # case
    op.create_table(
        "case",
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("case_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("case_status", sa.Boolean(), nullable=True),
        sa.Column("case_type", postgresql.ENUM(name="case_type_enum", create_type=False), nullable=True),  # pyright: ignore[reportUnknownArgumentType]
        sa.Column("custom_case_type_id", sa.Integer(), sa.ForeignKey("custom_case_type.id"), nullable=True),
        sa.Column("case_reason", sa.String(length=2000), nullable=False),
        sa.Column("case_moderator_id", sa.BigInteger(), nullable=False),
        sa.Column("case_user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "case_user_roles",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("case_number", sa.Integer(), nullable=True),
        sa.Column("case_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("case_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("guild.guild_id"), nullable=False),
        sa.UniqueConstraint("guild_id", "case_number", name="uq_case_guild_case_number"),
    )
    op.create_index("idx_case_guild_user", "case", ["guild_id", "case_user_id"])
    op.create_index("idx_case_guild_moderator", "case", ["guild_id", "case_moderator_id"])

    # note
    op.create_table(
        "note",
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("note_content", sa.String(length=2000), nullable=False),
        sa.Column("note_moderator_id", sa.BigInteger(), nullable=False),
        sa.Column("note_user_id", sa.BigInteger(), nullable=False),
        sa.Column("note_number", sa.Integer(), nullable=True),
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("guild.guild_id"), nullable=False),
    )

    # guild_permission
    op.create_table(
        "guild_permission",
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), sa.ForeignKey("guild.guild_id"), nullable=False),
        sa.Column("permission_type", sa.String(length=50), nullable=False),
        sa.Column("access_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=False),
        sa.Column("target_name", sa.String(length=100), nullable=True),
        sa.Column("command_name", sa.String(length=100), nullable=True),
        sa.Column("module_name", sa.String(length=100), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_index("idx_guild_perm_guild_type", "guild_permission", ["guild_id", "permission_type"])
    op.create_index("idx_guild_perm_target", "guild_permission", ["target_id", "permission_type"])

    # starboard
    op.create_table(
        "starboard",
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("starboard_channel_id", sa.BigInteger(), nullable=False),
        sa.Column("starboard_emoji", sa.String(length=64), nullable=False),
        sa.Column("starboard_threshold", sa.Integer(), server_default="1", nullable=False),
    )

    # starboard_message
    op.create_table(
        "starboard_message",
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message_id", sa.BigInteger(), primary_key=True),
        sa.Column("message_content", sa.String(length=4000), nullable=False),
        sa.Column("message_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("message_channel_id", sa.BigInteger(), nullable=False),
        sa.Column("message_user_id", sa.BigInteger(), nullable=False),
        sa.Column("message_guild_id", sa.BigInteger(), nullable=False),
        sa.Column("star_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("starboard_message_id", sa.BigInteger(), nullable=False),
    )
    op.create_index("ux_starboard_message", "starboard_message", ["message_id", "message_guild_id"], unique=True)


def downgrade() -> None:
    # drop indexes if they exist
    op.execute("DROP INDEX IF EXISTS ux_starboard_message")
    op.execute("DROP INDEX IF EXISTS idx_guild_perm_target")
    op.execute("DROP INDEX IF EXISTS idx_guild_perm_guild_type")
    op.execute("DROP INDEX IF EXISTS idx_case_guild_moderator")
    op.execute("DROP INDEX IF EXISTS idx_case_guild_user")
    op.execute("DROP INDEX IF EXISTS idx_levels_guild_xp")
    op.execute("DROP INDEX IF EXISTS idx_afk_member_guild")
    op.execute("DROP INDEX IF EXISTS idx_snippet_name_guild")
    op.execute("DROP INDEX IF EXISTS idx_guild_id")

    # drop tables if they exist (reverse dep order)
    op.execute("DROP TABLE IF EXISTS starboard_message")
    op.execute("DROP TABLE IF EXISTS starboard")
    op.execute("DROP TABLE IF EXISTS guild_permission")
    op.execute("DROP TABLE IF EXISTS note")
    op.execute('DROP TABLE IF EXISTS "case"')
    op.execute("DROP TABLE IF EXISTS custom_case_type")
    op.execute("DROP TABLE IF EXISTS levels")
    op.execute("DROP TABLE IF EXISTS afk")
    op.execute("DROP TABLE IF EXISTS reminder")
    op.execute("DROP TABLE IF EXISTS snippet")
    op.execute("DROP TABLE IF EXISTS guild_config")
    op.execute("DROP TABLE IF EXISTS guild")

    # drop enum type
    sa.Enum(name="case_type_enum").drop(op.get_bind(), checkfirst=True)
