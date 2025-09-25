import discord


class XkcdButtons(discord.ui.View):
    def __init__(self, explain_url: str, webpage_url: str) -> None:
        super().__init__()
        self.add_item(
            discord.ui.Button(style=discord.ButtonStyle.link, label="Explainxkcd", url=explain_url),
        )
        self.add_item(
            discord.ui.Button(style=discord.ButtonStyle.link, label="Webpage", url=webpage_url),
        )


class GithubButton(discord.ui.View):
    def __init__(self, url: str) -> None:
        super().__init__()
        self.add_item(
            discord.ui.Button(style=discord.ButtonStyle.link, label="View on Github", url=url),
        )
