import re

DISCORD_ID = re.compile(r"(\d{15,20})$")

DISCORD_USER_MENTION = re.compile(r"<@!?(\d{15,20})>$")
DISCORD_CHANNEL_MENTION = re.compile(r"<#(\d{15,20})>$")
DISCORD_ROLE_MENTION = re.compile(r"<@&(\d{15,20})>$")

DISCORD_INVITE = re.compile(
    r"(?:https?://)?discord(?:app)?\.(?:com/invite|gg)/[a-zA-Z0-9]+/?",
    flags=re.IGNORECASE,
)

DISCORD_FILE = re.compile(
    r"(https://|http://)?(cdn\.|media\.)discord(app)?\.(com|net)/(attachments|avatars|icons|banners|splashes)/[0-9]{17,22}/([0-9]{17,22}/(?P<filename>.{1,256})|(?P<hash>.{32}))\.(?P<mime>[0-9a-zA-Z]{2,4})?",
)

DISCORD_MESSAGE = re.compile(
    r"(?:https?://)?(?:canary\.|ptb\.|www\.)?discord(?:app)?.(?:com/channels|gg)/(?P<guild_id>[0-9]{17,22})/(?P<channel_id>[0-9]{17,22})/(?P<message_id>[0-9]{17,22})",
)

CUSTOM_EMOJI = re.compile(r"<(a)?:([a-zA-Z0-9_]{2,32}):([0-9]{18,22})>")

MULTILINE_CODEBLOCK = re.compile(r"```(?P<extension>[a-z]*)\n*(?P<content>[\s\S]+)\n*```")
SINGLE_LINE_CODEBLOCK = re.compile(r"^`(?P<content>[\s\S]+)`$")

TENOR_PAGE_URL = re.compile(r"https?://(www\.)?tenor\.com/view/\S+/?")
TENOR_GIF_URL = re.compile(r"https?://(www\.)?c\.tenor\.com/\S+/\S+\.gif/?")

IMGUR_PAGE_URL = re.compile(r"https?://(www\.)?imgur.com/(\S+)/?")

URL = re.compile(
    r"((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*",
    flags=re.IGNORECASE,
)

URL_NO_PROTOCOL = re.compile(
    r"[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
    flags=re.IGNORECASE,
)
