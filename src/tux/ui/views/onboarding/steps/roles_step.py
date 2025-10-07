"""Roles step for the onboarding wizard."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from ..components.buttons import BackButtonRoles, ContinueButtonRoles
from ..components.selects import JailRoleSelect, PermissionRankRoleSelect
from .base_step import BaseWizardStep

if TYPE_CHECKING:
    from tux.ui.views.onboarding.wizard import SetupWizardView


class RolesStep(BaseWizardStep):
    """Permission ranks assignment step of the onboarding wizard."""

    def build(self) -> None:
        """Build the roles step."""
        self.clear_items()

        # Main container for roles step
        roles_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
            accent_color=0x9B59B6,  # Purple accent
            id=1000,
        )

        # Title
        title_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "# 👥 Step 3: Permission Ranks",
            id=1001,
        )
        roles_container.add_item(title_text)

        # Description
        description_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "Assign your server roles to Tux permission ranks (0-7). Higher ranks have more permissions.",
            id=1002,
        )
        roles_container.add_item(description_text)

        self.add_item(roles_container)

        # Add permission rank selectors in groups to stay under component limits
        self._add_permission_rank_groups()

        # Add jail role section
        self._add_jail_role_section()

        # Selected roles display container
        self._add_selection_display()

        # Action row with buttons
        self._add_action_buttons()

    def _add_permission_rank_groups(self) -> None:
        """Add permission rank selectors in groups to stay under component limits."""
        # Group ranks to reduce component count
        # Group 1: Ranks 1-3 (Lower ranks)
        self._add_permission_rank_group_1()
        # Group 2: Ranks 4-7 (Higher ranks)
        self._add_permission_rank_group_2()

    def _add_permission_rank_group_1(self) -> None:
        """Add permission rank selectors for ranks 1-3."""
        # Group 1 container - Lower ranks
        group1_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
            accent_color=0x3498DB,  # Blue accent
            id=1010,
        )

        group1_title: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "**Lower Permission Ranks**",
            id=1011,
        )
        group1_container.add_item(group1_title)

        group1_desc: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "Assign roles for basic moderation permissions.",
            id=1012,
        )
        group1_container.add_item(group1_desc)

        # Add ranks 1-3 individually (3 ranks x 2 components each = 6 components)
        self._add_rank_select_to_container(1, "Trusted", "Trusted server member", group1_container)
        self._add_rank_select_to_container(2, "Junior Moderator", "Can warn, timeout, jail", group1_container)
        self._add_rank_select_to_container(3, "Moderator", "Can kick, ban", group1_container)

        self.add_item(group1_container)

    def _add_permission_rank_group_2(self) -> None:
        """Add permission rank selectors for ranks 4-7."""
        # Group 2 container - Higher ranks
        group2_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
            accent_color=0xE74C3C,  # Red accent
            id=1020,
        )

        group2_title: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "**Higher Permission Ranks**",
            id=1021,
        )
        group2_container.add_item(group2_title)

        group2_desc: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "Assign roles for advanced administration permissions.",
            id=1022,
        )
        group2_container.add_item(group2_desc)

        # Add ranks 4-7 individually (4 ranks x 2 components each = 8 components)
        self._add_rank_select_to_container(4, "Senior Moderator", "Can unban, manage others", group2_container)
        self._add_rank_select_to_container(5, "Administrator", "Server administration", group2_container)
        self._add_rank_select_to_container(6, "Head Administrator", "Full server control", group2_container)
        self._add_rank_select_to_container(7, "Server Owner", "Complete access", group2_container)

        self.add_item(group2_container)

    def _add_rank_select_to_container(
        self,
        rank: int,
        rank_name: str,
        description: str,
        container: discord.ui.Container[SetupWizardView],
    ) -> None:
        """Add a single permission rank selector to a container."""
        # Action row with role select
        action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow(id=800 + rank)
        role_select: PermissionRankRoleSelect = PermissionRankRoleSelect(
            rank=rank,
            rank_name=rank_name,
            placeholder=f"Choose {rank_name} role...",
        )
        action_row.add_item(role_select)
        container.add_item(action_row)

    def _add_jail_role_section(self) -> None:
        """Add jail role section."""
        jail_role_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
            accent_color=0x8E44AD,  # Purple accent for jail
            id=1030,
        )

        jail_role_text: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "**Jail Role:**",
            id=1031,
        )
        jail_role_container.add_item(jail_role_text)

        jail_role_desc: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "Role assigned to jailed users to restrict their permissions.",
            id=1032,
        )
        jail_role_container.add_item(jail_role_desc)

        # Action row with jail role select
        jail_role_action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow(id=900)
        jail_role_select: JailRoleSelect = JailRoleSelect()
        jail_role_action_row.add_item(jail_role_select)
        jail_role_container.add_item(jail_role_action_row)

        self.add_item(jail_role_container)

    def _add_action_buttons(self) -> None:
        """Add action buttons."""
        # Action row with buttons
        action_row: discord.ui.ActionRow[SetupWizardView] = discord.ui.ActionRow(id=901)

        # Continue button
        continue_button: ContinueButtonRoles = ContinueButtonRoles()
        action_row.add_item(continue_button)

        # Back button
        back_button: BackButtonRoles = BackButtonRoles()
        action_row.add_item(back_button)

        self.add_item(action_row)

    def _add_selection_display(self) -> None:
        """Add selected roles display container."""
        selection_container: discord.ui.Container[SetupWizardView] = discord.ui.Container(
            accent_color=0x2ECC71,  # Green accent for selections
            id=1040,
        )

        # Selected roles section
        selection_title: discord.ui.TextDisplay[SetupWizardView] = discord.ui.TextDisplay(
            "**Selected Roles:**",
            id=1041,
        )
        selection_container.add_item(selection_title)

        self.wizard.selected_roles_text = discord.ui.TextDisplay(
            "No roles assigned yet.",
            id=1042,
        )
        selection_container.add_item(self.wizard.selected_roles_text)
        self.add_item(selection_container)
