import traceback

from aiopath import AsyncPath  # type: ignore
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants as C


class CogLoader(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cog_ignore_list = (
            C.PROD_COG_IGNORE_LIST if C.STAGING == "False" else C.STAGING_COG_IGNORE_LIST
        )

    async def is_cog_eligible(self, filepath: AsyncPath) -> bool:
        cog_name = filepath.stem

        return (
            filepath.suffix == ".py"
            and cog_name not in self.cog_ignore_list
            and not filepath.name.startswith("_")
            and await filepath.is_file()
        )

    async def load_cogs(self, apath: AsyncPath) -> None:
        if await apath.is_dir():
            async for item in apath.iterdir():
                await self.load_cogs(item)
        elif await self.is_cog_eligible(apath):
            relative_path = apath.relative_to(AsyncPath(__file__).parent)

            module = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]

            try:
                await self.bot.load_extension(module)
                logger.debug(f"Successfully loaded cog: {module}")
            except Exception as e:
                logger.error(f"Failed to load cog {module}. Error: {e}\n{traceback.format_exc()}")

    async def load_cogs_from_folder(self, folder_name: str) -> None:
        cog_path = AsyncPath(__file__).parent / folder_name

        await self.load_cogs(cog_path)

    @classmethod
    async def setup(cls, bot: commands.Bot) -> None:
        cog_loader = cls(bot)

        await cog_loader.load_cogs_from_folder("cogs")
        await bot.add_cog(cog_loader)
