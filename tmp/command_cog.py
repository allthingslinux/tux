from discord import Member, User
from discord.ext import commands
from discord.ext.commands import MissingPermissions

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class CommandCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    def cog_check(self, ctx):
        """
        This function is called before every command in the cog.

        Args:
        - ctx (commands.Context): The context of the command.

        Returns:
        - bool: True if the user has the required permission, False otherwise.
        """
        if not ctx.guild:
            logger.warning("Command used outside of a guild.")
            return False

        if isinstance(ctx.author, Member):
            author_roles = [role.id for role in ctx.author.roles]
            command_name = ctx.command.name if ctx.command else ""

            missing_permissions = self.bot.permissions.missing_permissions(
                author_roles, command_name
            )

            logger.info(f"User '{ctx.author.name}' has attempted to use {command_name}.")
            if missing_permissions is None:
                logger.debug(f"User '{ctx.author.name}' has permission to use {command_name}.")
                return True
            else:
                raise MissingPermissions(missing_permissions)
        elif isinstance(ctx.author, User):
            return False
