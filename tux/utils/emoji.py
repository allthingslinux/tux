import asyncio
from pathlib import Path

import discord
from discord.ext import commands


class EmojiManager:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache: dict[str, discord.Emoji] = {}
        self.emojis_path = Path(__file__).parents[2] / "assets" / "emojis"

    def get(self, name: str) -> discord.Emoji:
        return self.cache.get(name)

    async def init(self) -> dict[str, discord.Emoji]:
        """Initializes the emoji cache.

        This function retrieves all application emojis and caches them for later use.
        If no emojis are found, it synchronizes emojis from the assets directory.

        Returns:
            A dictionary mapping emoji names to discord.Emoji objects.
        """
        app_emojis = await self.bot.fetch_application_emojis()

        if not app_emojis:
            await self.sync_emojis()
            app_emojis = await self.bot.fetch_application_emojis()

        if not self.cache:
            self.cache = {emoji.name: emoji for emoji in app_emojis}

        return self.cache

    async def _make_emoji(self, name: str, file: bytes) -> discord.Emoji:
        """Creates a new application emoji.

        This function creates a new application emoji with the given name and
        image file. The created emoji is then cached for later use.

        Args:
            name: The name of the emoji to create.
            file: The image file as bytes.

        Returns:
            The created discord.Emoji object.
        """
        emoji = await self.bot.create_application_emoji(name=name, image=file)
        self.cache[name] = emoji
        return emoji

    async def _emoji_exists(self, name: str) -> bool:
        """Checks if an emoji with the given name exists.

        This function first checks the local cache for the emoji. If not found,
        it fetches all application emojis and checks if the given name exists.

        Args:
            name: The name of the emoji to check.

        Returns:
            True if the emoji exists, False otherwise.
        """
        if self.get(name):
            return True

        existing = await self.bot.fetch_application_emojis()
        return discord.utils.get(existing, name=name) is not None

    async def sync_emojis(self) -> list[discord.Emoji]:
        """Synchronizes emojis from the assets directory to the application.

        This function iterates through the emoji files in the assets directory
        and creates new application emojis if they don't already exist. Existing
        emojis are skipped and recorded as duplicates.

        Returns:
            A list of created discord.Emoji objects.
        """
        dupes = []
        created = []

        for file in self.emojis_path.iterdir():
            filename = file.stem

            if not file.is_file():
                continue

            if await self._emoji_exists(filename):
                dupes.append(file)
                continue

            with file.open("rb") as f:
                img_bytes = f.read()

            # uh ratelimits idk if theres a better way to avoid them
            await asyncio.sleep(1.0)
            emoji = await self._make_emoji(filename, img_bytes)
            created.append(emoji)

        return created
