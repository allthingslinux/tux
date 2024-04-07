import traceback

from aiopath import AsyncPath  # type: ignore
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants as CONST


class CogLoader(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cog_ignore_list: set[str] = (
            CONST.PROD_COG_IGNORE_LIST
            if CONST.STAGING == "False"
            else CONST.STAGING_COG_IGNORE_LIST
        )

    async def is_cog_eligible(self, filepath: AsyncPath) -> bool:
        """
        Checks if a cog file is eligible for loading based on specific criteria.

        Args:
            filepath (AsyncPath): The path to the cog file.

        Returns:
            bool: True if the cog file is eligible, False otherwise.
        """

        cog_name: str = filepath.stem

        return (
            filepath.suffix == ".py"
            and cog_name not in self.cog_ignore_list
            and not filepath.name.startswith("_")
            and await filepath.is_file()
        )

    async def load_cogs(self, apath: AsyncPath) -> None:
        """
        Recursively loads eligible cogs from the specified directory.

        Args:
            apath (AsyncPath): The path to the directory containing cogs.

        Returns:
            None
        """

        if await apath.is_dir():
            async for item in apath.iterdir():
                await self.load_cogs(apath=item)
        elif await self.is_cog_eligible(filepath=apath):
            relative_path: AsyncPath = apath.relative_to(AsyncPath(__file__).parent)

            module: str = str(object=relative_path).replace("/", ".").replace("\\", ".")[:-3]

            try:
                await self.bot.load_extension(name=module)
                logger.debug(f"Successfully loaded cog: {module}")
            except Exception as e:
                logger.error(f"Failed to load cog {module}. Error: {e}\n{traceback.format_exc()}")

    async def load_cogs_from_folder(self, folder_name: str) -> None:
        """
        Loads cogs from the specified folder by calling the load_cogs function.

        Args:
            folder_name (str): The name of the folder containing cogs.

        Returns:
            None
        """

        cog_path: AsyncPath = AsyncPath(__file__).parent / folder_name

        await self.load_cogs(apath=cog_path)

    @classmethod
    async def setup(cls, bot: commands.Bot) -> None:
        cog_loader = cls(bot)

        await cog_loader.load_cogs_from_folder(folder_name="cogs")
        await bot.add_cog(cog_loader)
