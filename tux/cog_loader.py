import traceback
from pathlib import Path

import aiofiles
import aiofiles.os
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants as CONST


class CogLoader(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cog_ignore_list: set[str] = CONST.COG_IGNORE_LIST

    async def is_cog_eligible(self, filepath: Path) -> bool:
        """
        Checks if the specified file is a cog.

        Parameters
        ----------
        filepath : Path
            The path to the file to check.

        Returns
        -------
        bool
            True if the file is a cog, False otherwise.
        """

        cog_name: str = filepath.stem

        return (
            filepath.suffix == ".py"
            and cog_name not in self.cog_ignore_list
            and not filepath.name.startswith("_")
            and await aiofiles.os.path.isfile(filepath)
        )

    async def load_cogs(self, path: Path) -> None:
        """
        Recursively loads eligible cogs from the specified directory.

        Parameters
        ----------
        path : Path
            The path to the directory containing cogs.

        Returns
        -------
        None

        Raises
        -------
        Exception
            If an error occurs while processing the specified path.
        """

        try:
            if await aiofiles.os.path.isdir(path):
                for item in path.iterdir():
                    try:
                        await self.load_cogs(path=item)

                    except Exception as error:
                        logger.error(f"Error loading cog from {item}: {error}")

            elif await self.is_cog_eligible(filepath=path):
                relative_path: Path = path.relative_to(Path(__file__).parent)
                module: str = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]

                try:
                    await self.bot.load_extension(name=module)
                    logger.debug(f"Successfully loaded cog: {module}")

                except Exception as e:
                    logger.error(
                        f"Failed to load cog {module}. Error: {e}\n{traceback.format_exc()}",
                    )

        except Exception as e:
            logger.error(f"An error occurred while processing {path}: {e}")

    async def load_cogs_from_folder(self, folder_name: str) -> None:
        """
        Loads cogs from the specified folder.

        Parameters
        ----------
        folder_name : str
            The name of the folder containing the cogs.

        Returns
        -------
        None
        """

        cog_path: Path = Path(__file__).parent / folder_name

        await self.load_cogs(path=cog_path)

    @classmethod
    async def setup(cls, bot: commands.Bot) -> None:
        cog_loader = cls(bot)
        await cog_loader.load_cogs_from_folder(folder_name="cogs")
        await cog_loader.load_cogs_from_folder(folder_name="handlers")
        await bot.add_cog(cog_loader)
