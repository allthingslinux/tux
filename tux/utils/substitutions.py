from tux.bot import Tux
from tux.utils.config import CONFIG


def _get_member_count(bot: Tux) -> int:
    """
    Returns the total member count of all guilds the bot is in.

    Returns
    -------
    int
        The total member count of all guilds the bot is in.
    """
    return sum(guild.member_count for guild in bot.guilds if guild.member_count is not None)


async def handle_substitution(
    bot: Tux,
    text: str,
):
    # Available substitutions:
    # {member_count} - total member count of all guilds
    # {guild_count} - total guild count
    # {bot_name} - bot name
    # {bot_version} - bot version
    # {prefix} - bot prefix

    if text and "{member_count}" in text:
        text = text.replace("{member_count}", str(_get_member_count(bot)))
    if text and "{guild_count}" in text:
        text = text.replace("{guild_count}", str(len(bot.guilds)))
    if text and "{bot_name}" in text:
        text = text.replace("{bot_name}", CONFIG.BOT_NAME)
    if text and "{bot_version}" in text:
        text = text.replace("{bot_version}", CONFIG.BOT_VERSION)
    if text and "{prefix}" in text:
        text = text.replace("{prefix}", CONFIG.DEFAULT_PREFIX)

    return text
