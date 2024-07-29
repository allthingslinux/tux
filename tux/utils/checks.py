from discord.ext import commands

from tux.handlers.error import PermissionLevelError


async def has_permission(
    ctx: commands.Context[commands.Bot],
    lower_bound: int,
    higher_bound: int | None = None,
) -> bool:
    """
    Check if the user has permission level between the lower and higher bounds.

    Parameters
    ----------
    ctx : commands.Context[commands.Bot]
        The discord context object.
    lower_bound : int
        The lower bound of the permission level.
    higher_bound : int, optional
        The higher bound of the permission level, by default None
    """

    # TODO: Add functionality
    return False


def level_to_name(level: int, or_higher: bool = False) -> str:
    """
    Convert a permission level to a name.

    Parameters
    ----------
    level : int
        The permission level to convert.
    or_higher : bool, optional
        Whether the user should have the permission level or higher, by default False

    Returns
    -------
    str
        The name of the permission level.
    """
    dictionary = {
        0: "Everyone",
        1: "Support",
        2: "Junior Moderator",
        3: "Moderator",
        4: "Senior Moderator",
        5: "Administrator",
        6: "Head Administrator",
        7: "Server Owner",
        8: "Sys Admin",
        9: "Bot Owner",
    }

    if or_higher:
        return f"{dictionary[level]} or higher"
    return dictionary[level]


# checks if the user has permission level 1 (Support)
def has_pl(level: int, or_higher: bool = False):
    """
    Check if the user has a permission level equal to or higher than the given level.

    Parameters
    ----------
    level : int
        The permission level to check against.
    or_higher : bool, optional
        Whether the user should have the permission level or higher, by default False
    """

    async def predicate(ctx: commands.Context[commands.Bot]) -> bool:
        if not await has_permission(ctx, level):
            raise PermissionLevelError(level_to_name(level, or_higher))
        return True

    return commands.check(predicate)
