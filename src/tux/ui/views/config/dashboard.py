"""
Unified configuration dashboard using the new UI framework.

Provides a clean, modular interface for configuration management
built on top of the extensible UI core system.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

import discord
from loguru import logger

from tux.core.permission_system import DEFAULT_RANKS, get_permission_system
from tux.database.models.models import PermissionAssignment
from tux.shared.constants import (
    CONFIG_COLOR_BLURPLE,
    CONFIG_COLOR_GREEN,
    CONFIG_COLOR_RED,
    CONFIG_COLOR_YELLOW,
    CONFIG_COMMANDS_PER_PAGE,
    CONFIG_DASHBOARD_TIMEOUT,
    CONFIG_LOGS_PER_PAGE,
    CONFIG_RANKS_PER_PAGE,
    CONFIG_ROLES_PER_PAGE,
)

from .callbacks import (
    create_cancel_assignment_callback,
    create_channel_callback,
    create_command_rank_callback,
    create_confirm_assignment_callback,
    create_delete_rank_callback,
    create_edit_rank_callback,
    create_role_selection_callback,
    create_role_update_callback,
    handle_callback_error,
    validate_author,
    validate_interaction_data,
)
from .command_discovery import get_moderation_commands
from .helpers import add_back_button_to_container, create_error_container
from .modals import CreateRankModal
from .pagination import PaginationHelper
from .ranks import initialize_default_ranks

if TYPE_CHECKING:
    from tux.core.bot import Tux


class ConfigDashboard(discord.ui.LayoutView):
    """
    Unified configuration dashboard using the new UI framework.

    Provides a clean, modular interface that scales with new configuration
    options while maintaining proper component limits and user experience.
    """

    # Button classes for Section accessories
    class RanksButton(discord.ui.Button[discord.ui.LayoutView]):
        """Button to open the Permission Ranks configuration mode."""

        def __init__(self) -> None:
            super().__init__(
                label="Open",
                style=discord.ButtonStyle.primary,
                custom_id="btn_ranks",
            )

        async def callback(self, interaction: discord.Interaction) -> None:
            """Handle button click to switch to ranks mode."""
            view = self.view
            if isinstance(view, ConfigDashboard):
                view.current_mode = "ranks"
                await view.build_layout()
                await interaction.response.edit_message(view=view)

    class RolesButton(discord.ui.Button[discord.ui.LayoutView]):
        """Button to open the Role Assignments configuration mode."""

        def __init__(self) -> None:
            super().__init__(
                label="Open",
                style=discord.ButtonStyle.primary,
                custom_id="btn_roles",
            )

        async def callback(self, interaction: discord.Interaction) -> None:
            """Handle button click to switch to roles mode."""
            view = self.view
            if isinstance(view, ConfigDashboard):
                view.current_mode = "roles"
                await view.build_layout()
                await interaction.response.edit_message(view=view)

    class CommandsButton(discord.ui.Button[discord.ui.LayoutView]):
        """Button to open the Command Permissions configuration mode."""

        def __init__(self) -> None:
            super().__init__(
                label="Open",
                style=discord.ButtonStyle.primary,
                custom_id="btn_commands",
            )

        async def callback(self, interaction: discord.Interaction) -> None:
            """Handle button click to switch to commands mode."""
            view = self.view
            if isinstance(view, ConfigDashboard):
                view.current_mode = "commands"
                await view.build_layout()
                await interaction.response.edit_message(view=view)

    class LogsButton(discord.ui.Button[discord.ui.LayoutView]):
        """Button to open the Log Channels configuration mode."""

        def __init__(self) -> None:
            super().__init__(
                label="Open",
                style=discord.ButtonStyle.primary,
                custom_id="btn_logs",
            )

        async def callback(self, interaction: discord.Interaction) -> None:
            """Handle button click to switch to logs mode."""
            view = self.view
            if isinstance(view, ConfigDashboard):
                view.current_mode = "logs"
                await view.build_layout()
                await interaction.response.edit_message(view=view)

    class ResetButton(discord.ui.Button[discord.ui.LayoutView]):
        """Button to reset all configuration to defaults."""

        def __init__(self) -> None:
            super().__init__(
                label="Reset",
                style=discord.ButtonStyle.danger,
                custom_id="btn_reset",
            )

        async def callback(self, interaction: discord.Interaction) -> None:
            """Handle button click to reset configuration."""
            view = self.view
            if isinstance(view, ConfigDashboard):
                await view._handle_quick_setup(interaction)

    def __init__(
        self,
        bot: Tux,
        guild: discord.Guild,
        author: discord.User | discord.Member,
        mode: str = "overview",
    ) -> None:
        super().__init__(timeout=CONFIG_DASHBOARD_TIMEOUT)

        self.bot = bot
        self.guild = guild
        self.author = author
        self.current_mode = mode

        # State management
        self.selected_channels: dict[str, discord.TextChannel | None] = {}
        self.current_page = 0

        # Component caching for performance
        self._built_modes: dict[str, discord.ui.Container[discord.ui.LayoutView]] = {}

        # Initialize the view (layout will be built when needed)

    def _get_cache_key(self, mode: str) -> str:
        """Generate cache key for a mode based on current pagination state."""
        page_attr = f"{mode}_current_page"
        current_page = getattr(self, page_attr, 0)
        return f"{mode}_page_{current_page}"

    def _build_pagination_footer(
        self,
        mode: str,
    ) -> discord.ui.TextDisplay[discord.ui.LayoutView]:
        """Build pagination footer showing current page info."""
        current_page = getattr(self, f"{mode}_current_page", 0)
        total_pages = getattr(self, f"{mode}_total_pages", 1)
        return discord.ui.TextDisplay[discord.ui.LayoutView](
            f"*Page {current_page + 1} of {total_pages}*",
        )

    def _build_pagination_info_footer(
        self,
        mode: str,
        start_idx: int,
        end_idx: int,
        total_items: int,
        item_name: str,
    ) -> discord.ui.TextDisplay[discord.ui.LayoutView]:
        """Build pagination info footer showing item range (e.g., 'Showing ranks 1-5 of 7')."""
        return discord.ui.TextDisplay[discord.ui.LayoutView](
            f"*Showing {item_name} {start_idx + 1}-{end_idx} of {total_items}*",
        )

    def _build_pagination_navigation(
        self,
        mode: str,
        rebuild_method: Callable[[], Awaitable[None]],
    ) -> discord.ui.ActionRow[discord.ui.LayoutView]:
        """Build navigation buttons for pagination (generic helper)."""

        async def handler(interaction: discord.Interaction) -> None:
            await PaginationHelper.handle_page_change(
                interaction,
                self,
                mode,
                f"{mode}_current_page",
                f"{mode}_total_pages",
                rebuild_method,
            )

        current_page = getattr(self, f"{mode}_current_page", 0)
        total_pages = getattr(self, f"{mode}_total_pages", 1)
        return PaginationHelper.build_navigation(
            mode,
            current_page,
            total_pages,
            handler,
        )

    async def _handle_page_change(
        self,
        interaction: discord.Interaction,
        mode: str,
        rebuild_method: Callable[[], Awaitable[None]],
    ) -> None:
        """Handle pagination button clicks (generic helper)."""
        await PaginationHelper.handle_page_change(
            interaction,
            self,
            mode,
            f"{mode}_current_page",
            f"{mode}_total_pages",
            rebuild_method,
        )

    def invalidate_cache(self, mode: str | None = None) -> None:
        """Invalidate cached components for performance optimization."""
        if mode:
            self._built_modes.pop(mode, None)
        else:
            self._built_modes.clear()

    def get_cached_mode(
        self,
        mode: str,
    ) -> discord.ui.Container[discord.ui.LayoutView] | None:
        """Get cached container for a mode if available."""
        return self._built_modes.get(mode)

    def cache_mode(
        self,
        mode: str,
        container: discord.ui.Container[discord.ui.LayoutView],
    ) -> None:
        """Cache a built container for a mode."""
        self._built_modes[mode] = container

    async def build_layout(self) -> None:
        # sourcery skip: merge-comparisons, merge-duplicate-blocks, remove-redundant-if
        """Build the dashboard layout based on current mode."""
        # Clear existing components
        self.clear_items()

        if self.current_mode == "overview":
            self._build_overview_mode()
        elif self.current_mode == "logs":
            await self.build_logs_mode()
        elif self.current_mode == "ranks":
            await self.build_ranks_mode()
        elif self.current_mode == "roles":
            await self.build_roles_mode()
        elif self.current_mode == "commands":
            await self.build_commands_mode()
        else:
            self._build_overview_mode()

    def _build_overview_mode(self) -> None:
        """Build the overview/dashboard mode with a creative card-based layout."""
        # Create a container for the dashboard content (embed-like appearance)
        container = discord.ui.Container[discord.ui.LayoutView](
            accent_color=CONFIG_COLOR_BLURPLE,
        )

        # Header
        header = discord.ui.TextDisplay[discord.ui.LayoutView](
            "# ⚙️ Configuration Dashboard\n\n"
            "Welcome to the unified configuration interface. "
            "Select a category below to manage your server settings.",
        )
        container.add_item(header)

        # Separator
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

        # Ranks Section
        ranks_section = discord.ui.Section[discord.ui.LayoutView](
            discord.ui.TextDisplay[discord.ui.LayoutView](
                "### 🎖️ Permission Ranks\n"
                "Create and manage permission ranks that define access levels. "
                "Ranks are numbered 0-10, with higher numbers granting more permissions.",
            ),
            accessory=self.RanksButton(),
        )
        container.add_item(ranks_section)

        # Roles Section
        roles_section = discord.ui.Section[discord.ui.LayoutView](
            discord.ui.TextDisplay[discord.ui.LayoutView](
                "### 👥 Role Assignments\n"
                "Assign Discord roles to permission ranks. "
                "Users with assigned roles will inherit the rank's permissions.",
            ),
            accessory=self.RolesButton(),
        )
        container.add_item(roles_section)

        # Commands Section
        commands_section = discord.ui.Section[discord.ui.LayoutView](
            discord.ui.TextDisplay[discord.ui.LayoutView](
                "### 🤖 Command Permissions\n"
                "Control which commands require which permission rank. "
                "Unassigned commands are disabled by default for security.",
            ),
            accessory=self.CommandsButton(),
        )
        container.add_item(commands_section)

        # Logs Section
        logs_section = discord.ui.Section[discord.ui.LayoutView](
            discord.ui.TextDisplay[discord.ui.LayoutView](
                "### 📝 Log Channels\n"
                "Configure channels where bot events are logged. "
                "Set up moderation logs, member events, and more.",
            ),
            accessory=self.LogsButton(),
        )
        container.add_item(logs_section)

        # Separator before quick actions
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        # Quick Actions Section
        reset_section = discord.ui.Section[discord.ui.LayoutView](
            discord.ui.TextDisplay[discord.ui.LayoutView](
                "### 🔄 Reset to Defaults\n"
                "Reset all configuration settings to their default values. "
                "**Warning:** This action cannot be undone.",
            ),
            accessory=self.ResetButton(),
        )
        container.add_item(reset_section)

        # Add the container to the view
        self.add_item(container)

    async def build_ranks_mode(self) -> None:  # noqa: PLR0915
        """Build the ranks management mode (create, delete, view ranks)."""
        try:
            # Check cache first (invalidate if pagination state changed)
            cache_key = self._get_cache_key("ranks")
            if cached := self.get_cached_mode(cache_key):
                self.clear_items()
                self.add_item(cached)
                return

            # Clear existing items first
            self.clear_items()

            # Create a container for the ranks content
            container = discord.ui.Container[discord.ui.LayoutView](
                accent_color=CONFIG_COLOR_YELLOW,
            )

            # Get ranks
            ranks = await self.bot.db.permission_ranks.get_permission_ranks_by_guild(
                self.guild.id,
            )

            if not ranks:
                # No ranks configured
                no_ranks = discord.ui.TextDisplay[discord.ui.LayoutView](
                    "**No permission ranks found.**\n\nUse the button below to create your first rank, or use `/config ranks init` to create default ranks.",
                )
                container.add_item(no_ranks)

                # Add action buttons
                init_ranks_btn = discord.ui.Button[discord.ui.LayoutView](
                    label="Init Default Ranks",
                    emoji="🔢",
                    style=discord.ButtonStyle.primary,
                    custom_id="btn_init_default_ranks",
                )
                init_ranks_btn.callback = self._handle_init_default_ranks

                create_rank_btn = discord.ui.Button[discord.ui.LayoutView](
                    label="Create Rank",
                    emoji="➕",  # noqa: RUF001
                    style=discord.ButtonStyle.success,
                    custom_id="btn_create_rank",
                )
                create_rank_btn.callback = self._handle_create_rank

                create_row = discord.ui.ActionRow[discord.ui.LayoutView]()
                create_row.add_item(init_ranks_btn)
                create_row.add_item(create_rank_btn)
                container.add_item(create_row)
            else:
                # Calculate pagination info
                sorted_ranks = sorted(ranks, key=lambda x: x.rank)
                total_ranks = len(sorted_ranks)
                start_idx, end_idx, total_pages, _ = PaginationHelper.setup_pagination(
                    self,
                    "ranks_current_page",
                    total_ranks,
                    CONFIG_RANKS_PER_PAGE,
                )
                page_ranks = sorted_ranks[start_idx:end_idx]

                # Store pagination info for navigation
                self.ranks_total_pages = total_pages

                # Page header
                page_header = discord.ui.TextDisplay[discord.ui.LayoutView](
                    "# 🎖️ Permission Ranks\n\nManage permission ranks. Higher numbers indicate greater permissions.",
                )
                container.add_item(page_header)

                # Add "Create Rank" button at the top
                create_rank_btn = discord.ui.Button[discord.ui.LayoutView](
                    label="+ Create Rank",
                    style=discord.ButtonStyle.success,
                    custom_id="btn_create_rank",
                )
                create_rank_btn.callback = self._handle_create_rank
                create_row = discord.ui.ActionRow[discord.ui.LayoutView]()
                create_row.add_item(create_rank_btn)
                container.add_item(create_row)

                # Top separator
                container.add_item(discord.ui.Separator())

                for rank_idx, rank in enumerate(page_ranks):
                    # Rank info display
                    rank_content = f"### Rank {rank.rank}: {rank.name}\n*{rank.description or 'No description'}*"
                    rank_display = discord.ui.TextDisplay[discord.ui.LayoutView](
                        rank_content,
                    )
                    container.add_item(rank_display)

                    # Edit and Delete buttons for this rank
                    rank_actions_row = discord.ui.ActionRow[discord.ui.LayoutView]()

                    edit_rank_btn = discord.ui.Button[discord.ui.LayoutView](
                        label="✏️ Edit Rank",
                        style=discord.ButtonStyle.primary,
                        custom_id=f"edit_rank_{rank.rank}",
                    )
                    edit_rank_btn.callback = create_edit_rank_callback(
                        self,
                        rank.rank,
                        rank.name,
                        rank.description,
                    )
                    rank_actions_row.add_item(edit_rank_btn)

                    delete_rank_btn = discord.ui.Button[discord.ui.LayoutView](
                        label="🗑️ Delete Rank",
                        style=discord.ButtonStyle.danger,
                        custom_id=f"delete_rank_{rank.rank}",
                    )
                    delete_rank_btn.callback = create_delete_rank_callback(
                        self,
                        rank.rank,
                        rank.name,
                    )
                    rank_actions_row.add_item(delete_rank_btn)
                    container.add_item(rank_actions_row)

                    # Separator between ranks
                    if rank_idx < len(page_ranks) - 1:
                        container.add_item(discord.ui.Separator())

                # Bottom separator
                container.add_item(discord.ui.Separator())

                # Add navigation if we have multiple pages
                if self.ranks_total_pages > 1:
                    nav_container = self._build_pagination_navigation(
                        "ranks",
                        self.build_ranks_mode,
                    )
                    container.add_item(nav_container)

                # Add pagination info footer
                # For ranks, show actual rank values instead of 1-based position indices
                if page_ranks:
                    first_rank = page_ranks[0].rank
                    last_rank = page_ranks[-1].rank
                    container.add_item(
                        discord.ui.TextDisplay[discord.ui.LayoutView](
                            f"*Showing ranks {first_rank}-{last_rank} of {total_ranks}*",
                        ),
                    )
                else:
                    container.add_item(
                        self._build_pagination_info_footer(
                            "ranks",
                            start_idx,
                            end_idx,
                            total_ranks,
                            "ranks",
                        ),
                    )

            # Back button
            add_back_button_to_container(container, self)

            self.add_item(container)

            # Cache the successfully built container
            self.cache_mode(cache_key, container)

        except Exception as e:
            logger.error(f"Error building ranks mode: {e}")
            error_container = create_error_container(
                f"Error loading ranks configuration: {e}",
                self,
            )
            self.add_item(error_container)

    def _group_assignments_by_rank(
        self,
        ranks: list[Any],
        assignments: list[Any],
    ) -> dict[int, list[dict[str, Any]]]:
        """Group role assignments by rank value."""
        assignments_by_rank: dict[int, list[dict[str, Any]]] = {}
        rank_id_to_value = {r.id: r.rank for r in ranks}

        for assignment in assignments:
            rank_value = rank_id_to_value.get(assignment.permission_rank_id)
            if rank_value is not None and (
                role := self.guild.get_role(assignment.role_id)
            ):
                if rank_value not in assignments_by_rank:
                    assignments_by_rank[rank_value] = []
                assignments_by_rank[rank_value].append(
                    {"role": role, "assignment": assignment},
                )

        return assignments_by_rank

    def _build_rank_assignment_display(
        self,
        rank: Any,
        rank_assignments: list[dict[str, Any]],
    ) -> discord.ui.TextDisplay[discord.ui.LayoutView]:
        """Build the display text for a rank with its assigned roles."""
        if rank_assignments:
            rank_content = f"### ✅ Rank {rank.rank}: {rank.name}\n*{rank.description or 'No description'}*"
        else:
            rank_content = f"### ⚠️ Rank {rank.rank}: {rank.name}\n*{rank.description or 'No description'}*"

        return discord.ui.TextDisplay[discord.ui.LayoutView](rank_content)

    def _build_rank_status_display(
        self,
        rank_assignments: list[dict[str, Any]],
    ) -> discord.ui.TextDisplay[discord.ui.LayoutView]:
        """Build the status display for a rank."""
        if rank_assignments:
            role_list = [f"• {item['role'].mention}" for item in rank_assignments[:5]]
            if len(rank_assignments) > 5:
                role_list.append(f"*... and {len(rank_assignments) - 5} more*")
            status_content = (
                f"**Status:** {len(rank_assignments)} role(s) assigned\n"
                + "\n".join(role_list)
            )
        else:
            status_content = "**Status:** No roles assigned"

        return discord.ui.TextDisplay[discord.ui.LayoutView](status_content)

    def _build_role_selector(
        self,
        rank: Any,
        rank_assignments: list[dict[str, Any]],
    ) -> discord.ui.RoleSelect[discord.ui.LayoutView] | None:
        """Build a role selector for a rank."""
        if rank.id is None:
            logger.error(f"Rank {rank.rank} has no database ID, skipping role selector")
            return None

        role_select: discord.ui.RoleSelect[discord.ui.LayoutView] = (
            discord.ui.RoleSelect[discord.ui.LayoutView](
                placeholder=f"Update roles for Rank {rank.rank}",
                min_values=0,
                max_values=25,
                custom_id=f"update_roles_{rank.rank}",
            )
        )

        if rank_assignments:
            role_select.default_values = [item["role"] for item in rank_assignments]

        role_select.callback = create_role_update_callback(self, rank.rank, rank.id)
        return role_select

    async def build_roles_mode(self) -> None:
        """Build the role-to-rank assignment mode."""
        try:
            # Check cache first (invalidate if pagination state changed)
            cache_key = self._get_cache_key("roles")
            if cached := self.get_cached_mode(cache_key):
                self.clear_items()
                self.add_item(cached)
                return

            # Clear existing items first
            self.clear_items()

            # Create a container for the roles content
            container = discord.ui.Container[discord.ui.LayoutView](
                accent_color=CONFIG_COLOR_GREEN,
            )

            # Get ranks and assignments
            ranks = await self.bot.db.permission_ranks.get_permission_ranks_by_guild(
                self.guild.id,
            )
            assignments = (
                await self.bot.db.permission_assignments.get_assignments_by_guild(
                    self.guild.id,
                )
            )

            # Group assignments by rank value
            assignments_by_rank = self._group_assignments_by_rank(ranks, assignments)

            if not ranks:
                # No ranks configured
                no_ranks = discord.ui.TextDisplay[discord.ui.LayoutView](
                    "**No permission ranks found.**\n\nUse `/config ranks init` to create default ranks first.",
                )
                container.add_item(no_ranks)
            else:
                # Calculate pagination info
                sorted_ranks = sorted(ranks, key=lambda x: x.rank)
                total_ranks = len(sorted_ranks)
                start_idx, end_idx, total_pages, _ = PaginationHelper.setup_pagination(
                    self,
                    "roles_current_page",
                    total_ranks,
                    CONFIG_ROLES_PER_PAGE,
                )
                page_ranks = sorted_ranks[start_idx:end_idx]

                # Store pagination info for navigation
                self.roles_total_pages = total_pages

                # Page header with description
                page_header = discord.ui.TextDisplay[discord.ui.LayoutView](
                    "# 👥 Role Assignments\n\nAssign Discord roles to permission ranks to control access levels.",
                )
                container.add_item(page_header)

                # Top separator
                container.add_item(discord.ui.Separator())

                for rank_idx, rank in enumerate(page_ranks):
                    rank_assignments = assignments_by_rank.get(rank.rank, [])

                    # Build rank display
                    rank_display = self._build_rank_assignment_display(
                        rank,
                        rank_assignments,
                    )
                    container.add_item(rank_display)

                    if role_select := self._build_role_selector(rank, rank_assignments):
                        selector_row = discord.ui.ActionRow[discord.ui.LayoutView]()
                        selector_row.add_item(role_select)
                        container.add_item(selector_row)

                    # Build status display
                    status_display = self._build_rank_status_display(rank_assignments)
                    container.add_item(status_display)

                    # Separator between ranks
                    if rank_idx < len(page_ranks) - 1:
                        container.add_item(discord.ui.Separator())

                # Bottom separator
                container.add_item(discord.ui.Separator())

                # Add navigation if we have multiple pages
                if self.roles_total_pages > 1:
                    nav_container = self._build_pagination_navigation(
                        "roles",
                        self.build_roles_mode,
                    )
                    container.add_item(nav_container)

                # Add pagination info footer
                container.add_item(
                    self._build_pagination_info_footer(
                        "roles",
                        start_idx,
                        end_idx,
                        total_ranks,
                        "ranks",
                    ),
                )

            # Back button
            add_back_button_to_container(container, self)

            self.add_item(container)

            # Cache the successfully built container
            self.cache_mode(cache_key, container)

        except Exception as e:
            logger.error(f"Error building roles mode: {e}")
            error_container = create_error_container(
                f"Error loading role configuration: {e}",
                self,
            )
            self.add_item(error_container)

    async def _validate_rank_for_assignment(self, rank_id: int) -> int | None:
        """Validate rank exists and return its database ID."""
        ranks = await self.bot.db.permission_ranks.get_permission_ranks_by_guild(
            self.guild.id,
        )
        rank_obj = next((r for r in ranks if r.rank == rank_id), None)
        return rank_obj.id if rank_obj and rank_obj.id is not None else None

    def _build_role_assignment_view(
        self,
        rank_id: int,
        role_select: discord.ui.RoleSelect[discord.ui.LayoutView],
    ) -> tuple[discord.ui.LayoutView, discord.ui.Container[discord.ui.LayoutView]]:
        """Build the initial role assignment view."""
        assign_view = discord.ui.LayoutView(timeout=300)
        assign_container = discord.ui.Container[discord.ui.LayoutView](
            accent_color=CONFIG_COLOR_GREEN,
        )

        header = discord.ui.TextDisplay[discord.ui.LayoutView](
            f"# + Assign Roles to Rank {rank_id}\n\n"
            "Select the Discord role(s) you want to assign to this permission rank.",
        )
        assign_container.add_item(header)

        placeholder = discord.ui.TextDisplay[discord.ui.LayoutView](
            "*No roles selected yet*",
        )
        assign_container.add_item(placeholder)

        selector_row = discord.ui.ActionRow[discord.ui.LayoutView]()
        selector_row.add_item(role_select)
        assign_container.add_item(selector_row)

        assign_view.add_item(assign_container)
        return assign_view, assign_container

    def update_role_selection_ui(
        self,
        rank_id: int,
        selected_roles: list[discord.Role],
        role_select: discord.ui.RoleSelect[discord.ui.LayoutView],
        assign_view: discord.ui.LayoutView,
        assign_container: discord.ui.Container[discord.ui.LayoutView],
        confirm_callback: Any,
        cancel_callback: Any,
    ) -> None:
        """Update the role assignment UI with selected roles."""
        assign_container.children.clear()

        header = discord.ui.TextDisplay[discord.ui.LayoutView](
            f"# + Assign Roles to Rank {rank_id}\n\n"
            "Select the Discord role(s) you want to assign to this permission rank.",
        )
        assign_container.add_item(header)

        if selected_roles:
            selected_text = discord.ui.TextDisplay[discord.ui.LayoutView](
                f"**Selected Roles ({len(selected_roles)}):**\n"
                + "\n".join(f"• {role.mention}" for role in selected_roles),
            )
            assign_container.add_item(selected_text)

            confirm_btn = discord.ui.Button[discord.ui.LayoutView](
                label="✅ Confirm Assignment",
                style=discord.ButtonStyle.success,
                custom_id=f"confirm_assign_{rank_id}",
            )
            confirm_btn.callback = confirm_callback

            actions_row = discord.ui.ActionRow[discord.ui.LayoutView]()
            actions_row.add_item(confirm_btn)

            cancel_btn = discord.ui.Button[discord.ui.LayoutView](
                label="❌ Cancel",
                style=discord.ButtonStyle.secondary,
                custom_id="cancel_assign",
            )
            cancel_btn.callback = cancel_callback
            actions_row.add_item(cancel_btn)

            assign_container.add_item(actions_row)
        else:
            placeholder = discord.ui.TextDisplay[discord.ui.LayoutView](
                "*No roles selected yet*",
            )
            assign_container.add_item(placeholder)

        selector_row = discord.ui.ActionRow[discord.ui.LayoutView]()
        selector_row.add_item(role_select)
        assign_container.add_item(selector_row)

        assign_view.children.clear()
        assign_view.add_item(assign_container)

    async def _handle_assign_role(self, interaction: discord.Interaction) -> None:
        """Handle assigning a role to a rank using a modal."""
        try:
            if not await validate_author(
                interaction,
                self.author,
                "❌ You are not authorized to modify role assignments.",
            ):
                return

            if not await validate_interaction_data(interaction):
                return

            custom_id = interaction.data.get("custom_id", "")  # type: ignore[index]
            if not custom_id.startswith("assign_"):
                return

            rank_id = int(custom_id.split("_")[-1])
            logger.trace(f"Processing assign role request for rank {rank_id}")

            # Validate rank
            rank_db_id = await self._validate_rank_for_assignment(rank_id)
            if rank_db_id is None:
                await interaction.response.send_message(
                    f"❌ Rank {rank_id} does not exist.",
                    ephemeral=True,
                )
                return

            logger.trace(f"Found rank {rank_id} with database ID {rank_db_id}")

            # Create role selector
            role_select: discord.ui.RoleSelect[discord.ui.LayoutView] = (
                discord.ui.RoleSelect[discord.ui.LayoutView](
                    placeholder=f"Select role(s) to assign to Rank {rank_id}",
                    min_values=1,
                    max_values=5,
                    custom_id=f"direct_assign_select_{rank_id}",
                )
            )

            # Track selected roles (mutable list for sharing between callbacks)
            selected_roles: list[discord.Role] = []

            # Build view
            assign_view, assign_container = self._build_role_assignment_view(
                rank_id,
                role_select,
            )

            # Create callbacks
            confirm_callback = create_confirm_assignment_callback(
                self,
                rank_id,
                rank_db_id,
                selected_roles,
            )
            cancel_callback = create_cancel_assignment_callback()
            role_select_callback = create_role_selection_callback(
                self,
                rank_id,
                role_select,
                assign_view,
                assign_container,
                selected_roles,
                confirm_callback,
                cancel_callback,
            )

            role_select.callback = role_select_callback
            await interaction.response.send_message(view=assign_view, ephemeral=True)

        except Exception as e:
            await handle_callback_error(interaction, e, "handling assign role", "")

    async def _handle_confirm_assign_role(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Handle confirming role assignment."""
        if not await validate_author(
            interaction,
            self.author,
            "❌ You are not authorized to modify role assignments.",
        ):
            return

        if not await validate_interaction_data(interaction):
            return

        custom_id = interaction.data.get("custom_id", "")  # type: ignore[index]
        if not custom_id.startswith("confirm_assign_"):
            return

        # Ephemeral messages don't expose component values, so this method is deprecated
        # Users should use the direct rank assignment buttons instead
        await interaction.response.send_message(
            "❌ This assignment method doesn't work with ephemeral messages. "
            "Please use the direct rank assignment buttons (+ Rank X) instead.",
            ephemeral=True,
        )

    async def _handle_remove_role(self, interaction: discord.Interaction) -> None:
        """Handle removing roles from a rank."""
        if not await validate_author(
            interaction,
            self.author,
            "❌ You are not authorized to modify role assignments.",
        ):
            return

        if not await validate_interaction_data(interaction):
            return

        custom_id = interaction.data.get("custom_id", "")  # type: ignore[index]
        if not custom_id.startswith("remove_"):
            return

        rank_id = int(custom_id.split("_")[-1])

        # Get the PermissionRank object to get its database ID
        ranks = await self.bot.db.permission_ranks.get_permission_ranks_by_guild(
            self.guild.id,
        )
        rank_obj = next((r for r in ranks if r.rank == rank_id), None)
        if not rank_obj:
            await interaction.response.send_message(
                f"❌ Rank {rank_id} does not exist.",
                ephemeral=True,
            )
            return

        rank_db_id = rank_obj.id
        assert rank_db_id is not None

        # Get current assignments for this rank
        try:
            assignments = (
                await self.bot.db.permission_assignments.get_assignments_by_guild(
                    self.guild.id,
                )
            )
            rank_assignments = [
                a for a in assignments if a.permission_rank_id == rank_db_id
            ]

            if not rank_assignments:
                await interaction.response.send_message(
                    f"❌ No roles assigned to Rank {rank_id}",
                    ephemeral=True,
                )
                return

            # Create removal interface
            remove_view = discord.ui.LayoutView(timeout=300)

            remove_container = discord.ui.Container[discord.ui.LayoutView](
                accent_color=CONFIG_COLOR_RED,
            )

            header = discord.ui.TextDisplay[discord.ui.LayoutView](
                f"# - Remove Roles from Rank {rank_id}\n\n"
                "Select the role(s) you want to remove from this permission rank.",
            )
            remove_container.add_item(header)

            # Create role select with current assignments
            role_select: discord.ui.RoleSelect[discord.ui.LayoutView] = (
                discord.ui.RoleSelect[discord.ui.LayoutView](
                    placeholder=f"Select role(s) to remove from Rank {rank_id}",
                    min_values=1,
                    max_values=len(rank_assignments),
                    custom_id=f"role_remove_select_{rank_id}",
                )
            )

            # Pre-select current assignments
            current_roles: list[discord.Role] = [
                role
                for assignment in rank_assignments
                if (role := self.guild.get_role(assignment.role_id))
            ]

            if current_roles:
                role_select.default_values = current_roles

            selector_row = discord.ui.ActionRow[discord.ui.LayoutView]()
            selector_row.add_item(role_select)
            remove_container.add_item(selector_row)

            # Confirm button
            confirm_btn = discord.ui.Button[discord.ui.LayoutView](
                label="🗑️ Confirm Removal",
                style=discord.ButtonStyle.danger,
                custom_id=f"confirm_remove_{rank_id}",
            )
            confirm_btn.callback = self._handle_confirm_remove_role

            # Cancel button
            cancel_btn = discord.ui.Button[discord.ui.LayoutView](
                label="❌ Cancel",
                style=discord.ButtonStyle.secondary,
                custom_id="cancel_remove",
            )
            cancel_btn.callback = self._handle_cancel_assign

            actions_row = discord.ui.ActionRow[discord.ui.LayoutView]()
            actions_row.add_item(confirm_btn)
            actions_row.add_item(cancel_btn)
            remove_container.add_item(actions_row)

            remove_view.add_item(remove_container)

            await interaction.response.send_message(view=remove_view, ephemeral=True)

        except Exception as e:
            await handle_callback_error(interaction, e, "loading assignments", "")

    def _find_role_select_from_message(
        self,
        message: discord.Message,
        custom_id: str,
    ) -> list[discord.Role] | None:
        """Find a RoleSelect component from a message and return its selected values."""
        if not hasattr(message, "components"):
            return None

        for action_row in message.components:
            if hasattr(action_row, "children"):
                for component in action_row.children:  # type: ignore[attr-defined]
                    if (
                        isinstance(component, discord.ui.RoleSelect)
                        and component.custom_id == custom_id
                    ):
                        return list(component.values)
        return None

    async def _handle_confirm_remove_role(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Handle confirming role removal."""
        if not await validate_author(
            interaction,
            self.author,
            "❌ You are not authorized to modify role assignments.",
        ):
            return

        if not await validate_interaction_data(interaction):
            return

        custom_id = interaction.data.get("custom_id", "")  # type: ignore[index]
        if not custom_id.startswith("confirm_remove_"):
            return

        rank_id = int(custom_id.split("_")[-1])

        # Validate rank exists
        ranks = await self.bot.db.permission_ranks.get_permission_ranks_by_guild(
            self.guild.id,
        )
        rank_obj = next((r for r in ranks if r.rank == rank_id), None)
        if not rank_obj or rank_obj.id is None:
            await interaction.response.send_message(
                f"❌ Rank {rank_id} does not exist.",
                ephemeral=True,
            )
            return

        # Find selected roles from message
        if not interaction.message:
            await interaction.response.send_message(
                "❌ Unable to find role selector",
                ephemeral=True,
            )
            return

        selected_roles = self._find_role_select_from_message(
            interaction.message,
            f"role_remove_select_{rank_id}",
        )
        if not selected_roles:
            await interaction.response.send_message(
                "❌ No roles selected",
                ephemeral=True,
            )
            return

        # Remove roles from rank
        try:
            removed_count = 0
            for role in selected_roles:
                deleted_count = await self.bot.db.permission_assignments.delete_where(
                    filters=(
                        PermissionAssignment.guild_id == self.guild.id,
                        PermissionAssignment.permission_rank_id == rank_obj.id,
                        PermissionAssignment.role_id == role.id,
                    ),
                )
                if deleted_count > 0:
                    removed_count += 1

            await interaction.response.send_message(
                f"✅ Successfully removed {removed_count} role(s) from Rank {rank_id}",
                ephemeral=True,
            )

            # Invalidate roles cache and rebuild
            self.invalidate_cache()
            self.current_mode = "roles"
            await self.build_roles_mode()
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                content="Removal completed! Returning to roles configuration...",
                view=self,  # type: ignore[arg-type]
                embed=None,
            )

        except Exception as e:
            await handle_callback_error(interaction, e, "removing roles", "")

    async def _handle_cancel_assign(self, interaction: discord.Interaction) -> None:
        """Handle canceling role assignment/removal."""
        await interaction.response.send_message(
            "❌ Operation cancelled",
            ephemeral=True,
        )

    def _build_command_display(
        self,
        cmd_name: str,
        rank_value: int | None,
        is_assigned: bool,
        rank_map: dict[int, Any],
    ) -> discord.ui.TextDisplay[discord.ui.LayoutView]:
        """Build the display text for a command with its rank assignment."""
        command = self.bot.get_command(cmd_name)
        command_description = command.short_doc if command else None

        cmd_content = (
            f"### ✅ `{cmd_name}`"
            if is_assigned and rank_value is not None
            else f"### ⚠️ `{cmd_name}`"
        )

        if command_description:
            cmd_content += f"\n*{command_description}*"

        return discord.ui.TextDisplay[discord.ui.LayoutView](cmd_content)

    def _build_command_status_display(
        self,
        rank_value: int | None,
        is_assigned: bool,
        rank_map: dict[int, Any],
    ) -> discord.ui.TextDisplay[discord.ui.LayoutView]:
        """Build the status display for a command."""
        if is_assigned and rank_value is not None:
            rank_info = rank_map.get(rank_value)
            rank_name = rank_info.name if rank_info else f"Rank {rank_value}"
            status_content = f"**Status:** Assigned (Rank {rank_value}: {rank_name})"
        else:
            status_content = "**Status:** Unassigned (disabled)"

        return discord.ui.TextDisplay[discord.ui.LayoutView](status_content)

    def _build_command_rank_selector(
        self,
        cmd_name: str,
        rank_value: int | None,
        is_assigned: bool,
        ranks: list[Any],
    ) -> discord.ui.Select[discord.ui.LayoutView]:
        """Build a rank selector for a command."""
        options: list[discord.SelectOption] = [
            discord.SelectOption(
                label="Unassign (Disable)",
                value="unassign",
                description="Remove rank requirement",
            ),
        ]

        for rank in sorted(ranks, key=lambda x: x.rank):
            option = discord.SelectOption(
                label=f"Rank {rank.rank}: {rank.name}",
                value=str(rank.rank),
                description=rank.description or None,
            )
            if is_assigned and rank_value is not None and rank.rank == rank_value:
                option.default = True
            options.append(option)

        rank_select = discord.ui.Select[discord.ui.LayoutView](
            placeholder=f"Select rank for {cmd_name}",
            min_values=1,
            max_values=1,
            custom_id=f"assign_command_{cmd_name}",
            options=options,
        )
        rank_select.callback = create_command_rank_callback(self, cmd_name)
        return rank_select

    async def build_commands_mode(self) -> None:
        """Build the command permissions configuration mode."""
        try:
            # Check cache first
            cache_key = self._get_cache_key("commands")
            if cached := self.get_cached_mode(cache_key):
                self.clear_items()
                self.add_item(cached)
                return

            # Clear existing items first
            self.clear_items()

            # Create a container for the commands content
            container = discord.ui.Container[discord.ui.LayoutView](
                accent_color=CONFIG_COLOR_YELLOW,
            )

            # Get all moderation commands
            moderation_commands = get_moderation_commands(self.bot)

            # Get existing command permissions
            existing_permissions = (
                await self.bot.db.command_permissions.get_all_command_permissions(
                    self.guild.id,
                )
            )
            permission_map = {perm.command_name: perm for perm in existing_permissions}

            # Get ranks for display
            ranks = await self.bot.db.permission_ranks.get_permission_ranks_by_guild(
                self.guild.id,
            )
            rank_map = {r.rank: r for r in ranks}

            # Build list of all commands with their assignment status
            # Sort alphabetically by name to maintain stable positions
            all_commands: list[tuple[str, int | None, bool]] = []
            for cmd_name in sorted(moderation_commands):
                if cmd_name in permission_map:
                    all_commands.append(
                        (cmd_name, permission_map[cmd_name].required_rank, True),
                    )
                else:
                    all_commands.append((cmd_name, None, False))

            total_commands = len(all_commands)

            # Calculate pagination info
            start_idx, end_idx, total_pages, _ = PaginationHelper.setup_pagination(
                self,
                "commands_current_page",
                total_commands,
                CONFIG_COMMANDS_PER_PAGE,
            )
            page_commands = all_commands[start_idx:end_idx]

            # Store pagination info
            self.commands_total_pages = total_pages

            # Page header with description
            page_header = discord.ui.TextDisplay[discord.ui.LayoutView](
                "# 🤖 Command Permissions\n\n"
                "Assign permission ranks to moderation commands. "
                "Commands without assigned ranks are disabled by default.",
            )
            container.add_item(page_header)

            # Top separator
            container.add_item(discord.ui.Separator())

            # Display commands
            for cmd_idx, (cmd_name, rank_value, is_assigned) in enumerate(
                page_commands,
            ):
                # Build command display
                cmd_display = self._build_command_display(
                    cmd_name,
                    rank_value,
                    is_assigned,
                    rank_map,
                )
                container.add_item(cmd_display)

                # Build rank selector
                rank_select = self._build_command_rank_selector(
                    cmd_name,
                    rank_value,
                    is_assigned,
                    ranks,
                )
                selector_row = discord.ui.ActionRow[discord.ui.LayoutView]()
                selector_row.add_item(rank_select)
                container.add_item(selector_row)

                # Build status display
                status_display = self._build_command_status_display(
                    rank_value,
                    is_assigned,
                    rank_map,
                )
                container.add_item(status_display)

                # Separator between commands
                if cmd_idx < len(page_commands) - 1:
                    container.add_item(discord.ui.Separator())

            # Bottom separator
            container.add_item(discord.ui.Separator())

            # Add navigation if we have multiple pages
            if self.commands_total_pages > 1:
                nav_container = self._build_pagination_navigation(
                    "commands",
                    self.build_commands_mode,
                )
                container.add_item(nav_container)

                # Add pagination info footer
                container.add_item(
                    self._build_pagination_info_footer(
                        "commands",
                        start_idx,
                        end_idx,
                        total_commands,
                        "commands",
                    ),
                )

            # Back button
            add_back_button_to_container(container, self)

            self.add_item(container)

            # Cache the successfully built container
            self.cache_mode(cache_key, container)

        except Exception as e:
            logger.error(f"Error building commands mode: {e}")
            error_container = create_error_container(
                f"Error loading command configuration: {e}",
                self,
            )
            self.add_item(error_container)

    def _build_log_option_display(
        self,
        option: dict[str, str],
        current_channel: discord.TextChannel | None,
    ) -> discord.ui.TextDisplay[discord.ui.LayoutView]:
        """Build the display text for a log option."""
        log_name = option["name"]
        log_description = option["description"]

        if current_channel:
            log_content = f"### ✅ {log_name}\n*{log_description}*"
        else:
            log_content = f"### ⚠️ {log_name}\n*{log_description}*"

        return discord.ui.TextDisplay[discord.ui.LayoutView](log_content)

    def _build_log_status_display(
        self,
        current_channel: discord.TextChannel | None,
    ) -> discord.ui.TextDisplay[discord.ui.LayoutView]:
        """Build the status display for a log option."""
        if current_channel:
            status_content = f"**Status:** Configured ({current_channel.mention})"
        else:
            status_content = "**Status:** Not configured"

        return discord.ui.TextDisplay[discord.ui.LayoutView](status_content)

    def _build_log_channel_selector(
        self,
        option: dict[str, str],
        current_channel: discord.TextChannel | None,
    ) -> discord.ui.ChannelSelect[discord.ui.LayoutView]:
        """Build a channel selector for a log option."""
        option_key = option["key"]
        log_name = option["name"]

        channel_select = discord.ui.ChannelSelect[discord.ui.LayoutView](
            placeholder=f"Select channel for {log_name.lower()}",
            channel_types=[discord.ChannelType.text],
            min_values=0,
            max_values=1,
            custom_id=f"log_{option_key}",
        )

        if current_channel:
            channel_select.default_values = [current_channel]

        channel_select.callback = create_channel_callback(self, option_key)
        return channel_select

    async def build_logs_mode(self) -> None:
        """Build logs configuration mode with improved organization."""
        try:
            # Check cache first
            cache_key = self._get_cache_key("logs")
            if cached := self.get_cached_mode(cache_key):
                self.clear_items()
                self.add_item(cached)
                return

            # Clear existing items first
            self.clear_items()

            # Define log channel options
            log_options = [
                {
                    "key": "mod_log_channel",
                    "name": "Moderation Logs",
                    "description": "Log moderation actions like bans, kicks, timeouts",
                    "field": "mod_log_id",
                },
                {
                    "key": "audit_log_channel",
                    "name": "Audit Logs",
                    "description": "Log server audit events and administrative changes",
                    "field": "audit_log_id",
                },
                {
                    "key": "join_log_channel",
                    "name": "Join/Leave Logs",
                    "description": "Log member join and leave events",
                    "field": "join_log_id",
                },
                {
                    "key": "private_log_channel",
                    "name": "Private Logs",
                    "description": "Private moderation logs for staff eyes only",
                    "field": "private_log_id",
                },
                {
                    "key": "report_log_channel",
                    "name": "Report Logs",
                    "description": "Log user reports and complaints",
                    "field": "report_log_id",
                },
                {
                    "key": "dev_log_channel",
                    "name": "Development Logs",
                    "description": "Debug and development logging",
                    "field": "dev_log_id",
                },
            ]

            total_logs = len(log_options)

            # Get current config to show selected channels
            config = await self.bot.db.guild_config.get_config_by_guild_id(
                self.guild.id,
            )

            # Calculate pagination info
            start_idx, end_idx, total_pages, _ = PaginationHelper.setup_pagination(
                self,
                "logs_current_page",
                total_logs,
                CONFIG_LOGS_PER_PAGE,
            )
            page_options = log_options[start_idx:end_idx]

            # Store pagination info
            self.logs_total_pages = total_pages

            # Create container
            container = discord.ui.Container[discord.ui.LayoutView](
                accent_color=CONFIG_COLOR_BLURPLE,
            )

            # Page header
            page_header = discord.ui.TextDisplay[discord.ui.LayoutView](
                "# 📝 Log Channels\n\nConfigure channels for different types of bot logging.",
            )
            container.add_item(page_header)

            # Top separator
            container.add_item(discord.ui.Separator())

            # Display log channel options
            for log_idx, option in enumerate(page_options):
                field_name = option["field"]

                # Get current channel if set
                current_channel: discord.TextChannel | None = None
                if config and (channel_id := getattr(config, field_name, None)):
                    channel = self.guild.get_channel(channel_id)
                    if isinstance(channel, discord.TextChannel):
                        current_channel = channel

                # Build log display
                log_display = self._build_log_option_display(option, current_channel)
                container.add_item(log_display)

                # Build channel selector
                channel_select = self._build_log_channel_selector(
                    option,
                    current_channel,
                )
                selector_row = discord.ui.ActionRow[discord.ui.LayoutView]()
                selector_row.add_item(channel_select)
                container.add_item(selector_row)

                # Build status display
                status_display = self._build_log_status_display(current_channel)
                container.add_item(status_display)

                # Separator between log types
                if log_idx < len(page_options) - 1:
                    container.add_item(discord.ui.Separator())

            # Bottom separator
            container.add_item(discord.ui.Separator())

            # Add navigation if we have multiple pages
            if self.logs_total_pages > 1:
                nav_container = self._build_pagination_navigation(
                    "logs",
                    self.build_logs_mode,
                )
                container.add_item(nav_container)

                # Add pagination info footer
                container.add_item(
                    self._build_pagination_info_footer(
                        "logs",
                        start_idx,
                        end_idx,
                        total_logs,
                        "logs",
                    ),
                )

            # Back button
            add_back_button_to_container(container, self)

            self.add_item(container)

            # Cache the successfully built container
            self.cache_mode(cache_key, container)

        except Exception as e:
            logger.error(f"Error building logs mode: {e}")
            error_container = create_error_container(
                f"Error loading log configuration: {e}",
                self,
            )
            self.add_item(error_container)

    def find_channel_select_component(
        self,
        custom_id: str,
    ) -> discord.ui.ChannelSelect[discord.ui.LayoutView] | None:
        """Find a ChannelSelect component by custom_id."""
        return next(
            (
                item
                for item in self.walk_children()
                if isinstance(item, discord.ui.ChannelSelect)
                and item.custom_id == custom_id
            ),
            None,
        )

    def resolve_channel_from_interaction(
        self,
        channel_select: discord.ui.ChannelSelect[discord.ui.LayoutView],
        interaction: discord.Interaction,
    ) -> discord.TextChannel | None:  # sourcery skip: use-named-expression
        """Resolve selected channel from component or interaction data."""
        # Try component values first
        if channel_select.values:
            resolved = channel_select.values[0].resolve()
            if isinstance(resolved, discord.TextChannel):
                return resolved

        # Fallback to interaction data
        if interaction.data:
            values = interaction.data.get("values", [])
            if values:
                resolved_data = (
                    interaction.data.get("resolved", {})
                    .get("channels", {})
                    .get(values[0])
                )
                if resolved_data:
                    channel = self.guild.get_channel(int(resolved_data["id"]))
                    if isinstance(channel, discord.TextChannel):
                        return channel

        return None

    async def update_channel_and_rebuild(
        self,
        option_key: str,
        channel_id: int | None,
        interaction: discord.Interaction,
        message: str,
    ) -> None:
        """Update channel config and rebuild logs mode."""
        channel = self.guild.get_channel(channel_id) if channel_id else None
        self.selected_channels[option_key] = (
            channel if isinstance(channel, discord.TextChannel) else None
        )
        await self._save_channel_config(option_key, channel_id)

        await interaction.response.defer()
        await interaction.followup.send(message, ephemeral=True)

        self.invalidate_cache()
        self.current_mode = "logs"
        await self.build_logs_mode()
        if interaction.message:
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                view=self,
            )

    async def _save_channel_config(
        self,
        option_key: str,
        channel_id: int | None,
    ) -> None:
        """Save channel configuration to database."""
        try:
            # Map option key to database field
            field_mapping = {
                "mod_log_channel": "mod_log_id",
                "audit_log_channel": "audit_log_id",
                "join_log_channel": "join_log_id",
                "private_log_channel": "private_log_id",
                "report_log_channel": "report_log_id",
                "dev_log_channel": "dev_log_id",
            }

            if field_name := field_mapping.get(option_key):
                updates = {field_name: channel_id}
                await self.bot.db.guild_config.update_config(self.guild.id, **updates)
                logger.info(
                    f"Saved {option_key} for guild {self.guild.id}: {channel_id}",
                )
        except Exception as e:
            logger.error(f"Failed to save {option_key}: {e}")

    def _build_error_mode(self, error_message: str) -> None:
        """Build an error display mode."""
        error_container = create_error_container(error_message, self)
        self.add_item(error_container)

    async def _handle_mode_change(self, interaction: discord.Interaction) -> None:
        """Handle mode changes from overview buttons."""
        if not await validate_author(
            interaction,
            self.author,
            "❌ You are not authorized to modify this configuration.",
        ):
            return

        if not await validate_interaction_data(interaction):
            return

        custom_id = interaction.data.get("custom_id", "")  # type: ignore[index]
        new_mode = custom_id.replace("btn_", "")

        if new_mode in ["logs", "ranks", "roles", "commands"]:
            self.current_mode = new_mode

            # Build the layout based on mode
            if new_mode == "logs":
                await self.build_logs_mode()
            elif new_mode == "ranks":
                await self.build_ranks_mode()
            elif new_mode == "roles":
                await self.build_roles_mode()
            elif new_mode == "commands":
                await self.build_commands_mode()
            else:
                await self.build_layout()

            await interaction.response.edit_message(view=self)

    async def _handle_create_rank(self, interaction: discord.Interaction) -> None:
        """Handle create rank button click - opens modal."""
        if not await validate_author(
            interaction,
            self.author,
            "❌ You are not authorized to create ranks.",
        ):
            return

        # Determine available ranks for creation
        existing_ranks = (
            await self.bot.db.permission_ranks.get_permission_ranks_by_guild(
                self.guild.id,
            )
        )
        existing_rank_values = {rank.rank for rank in existing_ranks}

        # Allow creating ranks 0-7 if they're missing, or ranks 8-10
        default_ranks = set(range(8))  # 0-7
        custom_ranks = set(range(8, 11))  # 8-10
        missing_default_ranks = default_ranks - existing_rank_values
        available_ranks = sorted(missing_default_ranks | custom_ranks)

        # Send modal for creating a rank with available options
        modal = CreateRankModal(self.bot, self.guild, self, available_ranks)
        await interaction.response.send_modal(modal)

    async def _handle_init_default_ranks(  # noqa: PLR0915
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Handle init default ranks button click - creates default ranks 0-7."""
        if not await validate_author(
            interaction,
            self.author,
            "❌ You are not authorized to initialize ranks.",
        ):
            return

        try:
            logger.info(
                f"Starting default rank initialization for guild {self.guild.id}",
            )

            # Ensure guild is registered in database first
            logger.debug(f"Ensuring guild {self.guild.id} is registered in database")
            guild_record = await self.bot.db.guild.get_by_id(self.guild.id)
            if not guild_record:
                logger.info(
                    f"Guild {self.guild.id} not found in database, registering it",
                )
                try:
                    await self.bot.db.guild.insert_guild_by_id(self.guild.id)
                    logger.success(f"Successfully registered guild {self.guild.id}")
                except Exception as reg_error:
                    logger.error(
                        f"Failed to register guild {self.guild.id}: {reg_error}",
                    )
                    await interaction.response.send_message(
                        "❌ **Guild Registration Failed**\n\n"
                        "Unable to register this guild in the database. Please try again later or contact support.",
                        ephemeral=True,
                    )
                    return

            # Check if ranks already exist
            logger.trace(f"Checking existing ranks for guild {self.guild.id}")
            existing_ranks = (
                await self.bot.db.permission_ranks.get_permission_ranks_by_guild(
                    self.guild.id,
                )
            )
            logger.trace(
                f"Found {len(existing_ranks)} existing ranks for guild {self.guild.id}",
            )

            if existing_ranks:
                logger.info(
                    f"Guild {self.guild.id} already has ranks, skipping initialization",
                )
                await interaction.response.send_message(
                    "⚠️ Permission ranks already exist!\n\n"
                    f"This guild already has {len(existing_ranks)} permission ranks configured.\n\n"
                    "Existing ranks will be preserved. Use the **+ Create Rank** button to add more ranks.",
                    ephemeral=True,
                )
                return

            # Initialize default ranks using permission system
            logger.info(f"Initializing default ranks for guild {self.guild.id}")
            try:
                permission_system = get_permission_system()
                logger.trace("Got permission system instance, calling initialize_guild")
                await permission_system.initialize_guild(self.guild.id)
                logger.info(
                    f"Successfully initialized ranks via permission system for guild {self.guild.id}",
                )
            except Exception as ps_error:
                # If permission system fails, log the specific error
                logger.error(
                    f"Permission system initialization failed for guild {self.guild.id}: {ps_error}",
                    exc_info=True,
                )
                logger.error(f"Permission system error repr: {ps_error!r}")
                # Try direct database approach as fallback
                logger.info(
                    f"Falling back to direct database rank creation for guild {self.guild.id}",
                )
                await initialize_default_ranks(self.bot.db, self.guild.id)
                logger.info(
                    f"Successfully initialized ranks via direct database for guild {self.guild.id}",
                )

            # Generate success message from the default ranks
            rank_lines: list[str] = []
            rank_lines.extend(
                f"• **Rank {rank_num}**: {rank_data['name']}"
                for rank_num, rank_data in sorted(DEFAULT_RANKS.items())
            )
            await interaction.response.send_message(
                "✅ **Default permission ranks initialized!**\n\n"
                "Created ranks 0-7:\n" + "\n".join(rank_lines) + "\n\n"
                "Use the role assignment screen to assign Discord roles to these ranks.",
                ephemeral=True,
            )

            # Invalidate cache and rebuild to show the new ranks
            self.invalidate_cache()
            self.current_mode = "ranks"
            await self.build_ranks_mode()
            if interaction.message:
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,
                    view=self,
                )

        except Exception as e:
            # Log detailed error information
            logger.error(
                f"CRITICAL: Error initializing default ranks for guild {self.guild.id}: {type(e).__name__}: {e}",
                exc_info=True,
            )
            logger.error(f"Exception repr: {e!r}")

            # Create safe error message
            error_parts = [f"❌ Failed to initialize ranks: {type(e).__name__}"]
            error_str = str(e).strip()
            if (
                error_str
                and error_str != str(type(e).__name__)
                and len(error_str) < 100
            ):
                error_parts.append(f"({error_str})")

            error_msg = " ".join(error_parts)

            try:
                if interaction.response.is_done():
                    await interaction.followup.send(error_msg, ephemeral=True)
                else:
                    await interaction.response.send_message(error_msg, ephemeral=True)
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
                logger.error(f"Send error details: {send_error!r}")

    async def handle_back_to_overview(self, interaction: discord.Interaction) -> None:
        """Handle back to overview navigation."""
        if not await validate_author(
            interaction,
            self.author,
            "❌ You are not authorized to modify this configuration.",
        ):
            return

        self.current_mode = "overview"
        self.current_page = 0  # Reset pagination
        await self.build_layout()
        await interaction.response.edit_message(view=self)

    async def _handle_quick_setup(self, interaction: discord.Interaction) -> None:
        """Handle quick setup actions."""
        if not await validate_author(
            interaction,
            self.author,
            "❌ You are not authorized to modify this configuration.",
        ):
            return

        if not await validate_interaction_data(interaction):
            return

        custom_id = interaction.data.get("custom_id", "")  # type: ignore[index]

        if custom_id == "btn_reset":
            await interaction.response.send_message(
                "🔄 Reset functionality coming soon...",
                ephemeral=True,
            )

    async def on_timeout(self) -> None:
        """Handle dashboard timeout."""
        logger.info(f"⏰ ConfigDashboard timed out for guild {self.guild.id}")

        # Clean up any references
        self.clear_items()
