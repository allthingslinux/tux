import configparser
import logging

from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class PermissionNotFoundError(Exception):
    pass


class Permissions:
    def __init__(self, debug: bool = False):
        config = configparser.ConfigParser()
        config.read("config/settings.ini")
        self.feature_permissions_section = config["Feature_Permissions"]
        self.permissions_section = config["Permissions"]

        if debug:
            logger.setLevel(logging.DEBUG)

    def _get_command_permissions_group(self, command):
        """
        Retrieve the permission group associated with a command.

        Args:
            command (str): The command to get the permission group for.

        Returns:
            str: The permission group for the command.

        Raises:
            commands.CommandNotFound: If the command is not found in the configuration.
        """
        command_permissions_group = self.feature_permissions_section.get(command, None)
        if command_permissions_group is None:
            raise commands.CommandNotFound(command)
        return command_permissions_group

    def _get_command_permissions(self, command_permissions_group):
        """
        Retrieve the permissions associated with a permission group.

        Args:
            command_permissions_group (str): The permission group to get permissions for.

        Returns:
            str | None: The permissions for the group or None if it's the "Everyone" group.

        Raises:
            PermissionNotFoundError: If permissions for the group are not found in the configuration.
        """
        if command_permissions_group == "Everyone":
            return None
        command_permissions = self.permissions_section.get(
            command_permissions_group, None
        )
        if command_permissions is None:
            raise PermissionNotFoundError(
                f"Permissions for group '{command_permissions_group}' not found in the configuration."
            )
        return command_permissions

    def _get_required_permissions(self, command_permissions):
        """
        Retrieve the required permissions from a string.

        Args:
            command_permissions (str): The comma-separated string of required permissions.

        Returns:
            List[str]: The list of required permissions.
        """
        return [role.strip() for role in command_permissions.split(",")]

    def missing_permissions(self, roles, command) -> list[str] | None:
        """
        Check for missing permissions for a command and roles.

        Args:
            roles (List[str]): The list of roles to check against required permissions.
            command (str): The command to check for permissions.

        Returns:
            List[str] | None: List of missing permissions or None if all are present.
        """
        command_permissions_group = self._get_command_permissions_group(command)

        command_permissions = self._get_command_permissions(command_permissions_group)

        if command_permissions is None:
            return None

        required_permissions = self._get_required_permissions(command_permissions)

        shared_permissions = [
            role for role in required_permissions if int(role) in roles
        ]

        return [command_permissions_group] if not shared_permissions else None

    def reload_ini_file(self, file_path):
        """
        Reload the INI file.

        Args:
            file_path (str): The path to the INI file.

        Returns:
            ConfigParser: The reloaded configuration.
        """
        config = configparser.ConfigParser()
        config.read(file_path)
        self.feature_permissions_section = config["Feature_Permissions"]
        self.permissions_section = config["Permissions"]
