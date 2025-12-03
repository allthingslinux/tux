"""
Discord UI Button Components for Tux Bot.

This module provides reusable Discord UI button components for various bot features,
including xkcd comic links and GitHub repository links.
"""

import discord


class XkcdButtons(discord.ui.View):
    """Button view for xkcd comic links."""

    def __init__(self, explain_url: str, webpage_url: str) -> None:
        """Initialize xkcd buttons with explain and webpage links.

        Parameters
        ----------
        explain_url : str
            URL to the explainxkcd page for the comic.
        webpage_url : str
            URL to the original xkcd webpage.
        """
        super().__init__()
        self.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="Explainxkcd",
                url=explain_url,
            ),
        )
        self.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="Webpage",
                url=webpage_url,
            ),
        )


class GithubButton(discord.ui.View):
    """Button view for GitHub repository links."""

    def __init__(self, url: str) -> None:
        """Initialize GitHub button with repository URL.

        Parameters
        ----------
        url : str
            URL to the GitHub repository or issue.
        """
        super().__init__()
        self.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="View on Github",
                url=url,
            ),
        )
