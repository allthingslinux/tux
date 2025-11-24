"""
Shared Regular Expressions for Tux Bot.

This module contains compiled regular expression patterns used throughout the Tux Discord bot
for parsing Discord entities, URLs, code blocks, and other common patterns.

Notes
-----
Various regex patterns are taken from the following sources:
- https://github.com/statch/gitbot/blob/main/lib/utils/regex.py
-

"""

import re

DISCORD_ID_RE = re.compile(r"(\d{15,20})$")
DISCORD_USER_MENTION_RE = re.compile(r"<@!?(\d{15,20})>$")
DISCORD_CHANNEL_MENTION_RE = re.compile(r"<#(\d{15,20})>$")
DISCORD_ROLE_MENTION_RE = re.compile(r"<@&(\d{15,20})>$")

MARKDOWN_EMOJI_RE = re.compile(r"<?:.*:([0-9]{18})?>?", re.IGNORECASE)

MULTILINE_CODEBLOCK_RE = re.compile(
    r"```(?P<extension>[a-z]*)\n*(?P<content>[\s\S]+)\n*```",
)
SINGLE_LINE_CODEBLOCK_RE = re.compile(r"^`(?P<content>[\s\S]+)`$")

DISCORD_INVITE_RE = re.compile(
    r"(?:https?://)?discord(?:app)?\.(?:com/invite|gg)/[a-zA-Z0-9]+/?",
    flags=re.IGNORECASE,
)

DISCORD_FILE_RE = re.compile(
    r"(https://|http://)?(cdn\.|media\.)discord(app)?\.(com|net)/(attachments|avatars|icons|banners|splashes)/[0-9]{17,22}/([0-9]{17,22}/(?P<filename>.{1,256})|(?P<hash>.{32}))\.(?P<mime>[0-9a-zA-Z]{2,4})?",
)

DISCORD_MESSAGE_RE = re.compile(
    r"(?:https?://)?(?:canary\.|ptb\.|www\.)?discord(?:app)?.(?:com/channels|gg)/(?P<guild_id>[0-9]{17,22})/(?P<channel_id>[0-9]{17,22})/(?P<message_id>[0-9]{17,22})",
)

CUSTOM_EMOJI_RE = re.compile(r"<(a)?:([a-zA-Z0-9_]{2,32}):([0-9]{18,22})>")


TENOR_PAGE_URL_RE = re.compile(r"https?://(www\.)?tenor\.com/view/\S+/?")
TENOR_GIF_URL_RE = re.compile(r"https?://(www\.)?c\.tenor\.com/\S+/\S+\.gif/?")

IMGUR_PAGE_URL_RE = re.compile(r"https?://(www\.)?imgur.com/(\S+)/?")

URL_RE = re.compile(
    r"((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*",
    flags=re.IGNORECASE,
)

URL_NO_PROTOCOL_RE = re.compile(
    r"[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
    flags=re.IGNORECASE,
)

GITHUB_NAME_RE = re.compile(r"^[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38}$", re.IGNORECASE)
GITHUB_REPO_URL_RE = re.compile(
    r"^(?:https?://)?github\.com/(?P<repo>[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38}/[a-z\d.](?:[a-z\d.]|-(?=[a-z\d.])){0,38})$",
    re.IGNORECASE,
)
GITHUB_USER_ORG_URL_RE = re.compile(
    r"^(?:https?://)?github\.com/(?P<name>[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38})$",
    re.IGNORECASE,
)
GITHUB_PULL_REQUEST_URL_RE = re.compile(
    r"(?:https?://)?github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/pull/(?P<number>\d+)",
    re.IGNORECASE,
)
GITHUB_PULL_REQUESTS_PLAIN_URL_RE = re.compile(
    r"(?:https?://)?github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/pulls",
    re.IGNORECASE,
)
GITHUB_ISSUE_URL_RE = re.compile(
    r"(?:https?://)?github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/issues/(?P<number>\d+)",
    re.IGNORECASE,
)
GITHUB_ISSUES_PLAIN_URL_RE = re.compile(
    r"(?:https?://)?github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/issues",
    re.IGNORECASE,
)
GITHUB_REPO_GIT_URL_RE = re.compile(
    r"(?:https?://)?github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)\.git",
    re.IGNORECASE,
)
GITHUB_LINES_URL_RE = re.compile(
    r"(?:https?://)?(?P<platform>github)\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/blob/(.+?)/(.+?)#L(?P<first_line_number>\d+)[-~]?L?(?P<second_line_number>\d*)",
    re.IGNORECASE,
)
GITLAB_LINES_URL_RE = re.compile(
    r"(?:https?://)?(?P<platform>gitlab)\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/-/blob/(.+?)/(.+?)#L(?P<first_line_number>\d+)-?(?P<second_line_number>\d*)",
    re.IGNORECASE,
)
GITHUB_COMMIT_URL_RE = re.compile(
    r"(?:https?://)?github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/commit/(?P<oid>\b([a-f0-9]{40})\b)",
)
GITHUB_REPO_TREE_RE = re.compile(
    r"(?:https?://)?github\.com/(?P<repo>[\w-]+/[\w-]+)/tree/(?P<ref>[\w-]+)/(?P<path>[\w/-]+)",
)
