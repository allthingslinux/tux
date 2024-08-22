from discord import app_commands
from discord.ext import commands


class PermissionLevelError(commands.CheckFailure):
    def __init__(self, permission: str) -> None:
        self.permission = permission
        super().__init__(f"User does not have the required permission: {permission}")


class AppCommandPermissionLevelError(app_commands.CheckFailure):
    def __init__(self, permission: str) -> None:
        self.permission = permission
        super().__init__(f"User does not have the required permission: {permission}")
