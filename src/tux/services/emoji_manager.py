"""
Emoji Manager Service for Tux Bot.

This module provides comprehensive emoji management functionality for the Tux Discord bot,
including creating, updating, and managing custom emojis across guilds. It supports
bulk operations, file-based emoji storage, and automatic cleanup.
"""

import asyncio
import contextlib
from pathlib import Path

import discord
from discord.ext import commands
from loguru import logger

from tux.services.sentry import capture_exception_safe

# --- Configuration Constants ---

DEFAULT_EMOJI_ASSETS_PATH = Path(__file__).parents[3] / "assets" / "emojis"
DOCKER_EMOJI_ASSETS_PATH = Path("/app/assets/emojis")
DEFAULT_EMOJI_CREATE_DELAY = 1.0
VALID_EMOJI_EXTENSIONS = [".png", ".gif", ".jpg"]
MIN_EMOJI_NAME_LENGTH = 2


# --- Utility Functions ---


def _is_valid_emoji_name(name: str) -> bool:
    """
    Check if an emoji name meets basic validity criteria.

    Returns
    -------
    bool
        True if the name is valid, False otherwise.
    """
    return bool(name and len(name) >= MIN_EMOJI_NAME_LENGTH)


def _find_emoji_file(base_path: Path, name: str) -> Path | None:
    """
    Find the local file corresponding to an emoji name within a base path.

    Returns
    -------
    Path | None
        The path to the emoji file if found, None otherwise.
    """
    if not _is_valid_emoji_name(name):
        logger.warning(f"Attempted to find file for invalid emoji name: '{name}'")
        return None

    for ext in VALID_EMOJI_EXTENSIONS:
        potential_path = base_path / f"{name}{ext}"

        if potential_path.is_file():
            logger.trace(f"Found local file for '{name}': {potential_path}")

            return potential_path

    logger.error(f"Cannot find local file for emoji '{name}' in {base_path}.")
    return None


def _read_emoji_file(file_path: Path) -> bytes | None:
    """
    Read image bytes from a file path, handling errors.

    Returns
    -------
    bytes | None
        The file contents as bytes if successful, None otherwise.
    """
    try:
        with file_path.open("rb") as f:
            img_bytes = f.read()
        logger.trace(f"Read {len(img_bytes)} bytes from {file_path}.")

        return img_bytes  # noqa: TRY300

    except OSError as e:
        logger.error(f"Failed to read local file '{file_path}': {e}")
        return None

    except Exception as e:
        logger.error(
            f"An unexpected error occurred reading file '{file_path}': {e}",
        )
        capture_exception_safe(
            e,
            extra_context={
                "operation": "read_local_file",
                "file_path": str(file_path),
            },
        )
        return None


# --- Emoji Manager Class ---


class EmojiManager:
    """Manages application emojis, caching, and synchronization from local files."""

    def __init__(
        self,
        bot: commands.Bot,
        emojis_path: Path | None = None,
        create_delay: float | None = None,
    ) -> None:
        """Initialize the EmojiManager.

        Parameters
        ----------
        bot : commands.Bot
            The discord bot instance.
        emojis_path : Optional[Path], optional
            Path to the directory containing local emoji files.
            Defaults to DEFAULT_EMOJI_ASSETS_PATH.
        create_delay : Optional[float], optional
            Delay in seconds before creating an emoji to mitigate rate limits.
            Defaults to DEFAULT_EMOJI_CREATE_DELAY.
        """
        self.bot = bot
        self.cache: dict[str, discord.Emoji] = {}
        self.emojis_path = emojis_path or DEFAULT_EMOJI_ASSETS_PATH
        self.create_delay = (
            create_delay if create_delay is not None else DEFAULT_EMOJI_CREATE_DELAY
        )
        self._init_lock = asyncio.Lock()
        self._initialized = False

        # If in Docker and no custom path was provided, use the Docker path
        if (
            not emojis_path
            and DOCKER_EMOJI_ASSETS_PATH.exists()
            and DOCKER_EMOJI_ASSETS_PATH.is_dir()
        ):
            logger.info(
                f"Docker environment detected, using emoji path: {DOCKER_EMOJI_ASSETS_PATH}",
            )
            self.emojis_path = DOCKER_EMOJI_ASSETS_PATH

        # Ensure the emoji path exists and is a directory
        if not self.emojis_path.is_dir():
            logger.critical(
                f"Emoji assets path is invalid or not a directory: {self.emojis_path}. "
                f"Emoji synchronization and resync features will be unavailable.",
            )

            # Do not attempt to create it. Subsequent operations that rely on this path
            # (like sync_emojis) will fail gracefully or log errors.
            # The manager itself is initialized, but operations requiring the path won't work.

        else:
            # Log path relative to project root for cleaner logs
            try:
                project_root = Path(__file__).parents[2]
                log_path = self.emojis_path.relative_to(project_root)
            except ValueError:
                log_path = self.emojis_path  # Fallback if path isn't relative
            logger.info(f"Using emoji assets directory: {log_path}")

    async def init(self) -> bool:
        """Initialize the emoji cache by fetching application emojis.

        Ensures the cache reflects the current state of application emojis on Discord.
        This method is locked to prevent concurrent initialization attempts.

        Returns
        -------
        bool
            True if initialization was successful or already done, False otherwise.
        """
        async with self._init_lock:
            if self._initialized:
                logger.debug("Emoji cache already initialized.")
                return True

            logger.info("Initializing emoji manager and cache...")

            try:
                app_emojis = await self.bot.fetch_application_emojis()
                self.cache = {
                    emoji.name: emoji
                    for emoji in app_emojis
                    if _is_valid_emoji_name(emoji.name)
                }

                logger.success(
                    f"Initialized emoji cache with {len(self.cache)} emojis.",
                )
                self._initialized = True

            except discord.HTTPException as e:
                logger.error(f"Failed to fetch application emojis during init: {e}")
                self._initialized = False
                return False
            except discord.DiscordException as e:
                logger.error(
                    "Unexpected Discord error during emoji cache initialization.",
                )
                capture_exception_safe(
                    e,
                    extra_context={
                        "operation": "emoji_cache_initialization",
                        "error_type": "DiscordException",
                    },
                )
                self._initialized = False
                return False
            except Exception as e:
                logger.error(
                    "Unexpected non-Discord error during emoji cache initialization.",
                )
                capture_exception_safe(
                    e,
                    extra_context={
                        "operation": "emoji_cache_initialization",
                        "error_type": "non-Discord",
                    },
                )
                self._initialized = False
                return False

            else:
                return True

    def get(self, name: str) -> discord.Emoji | None:
        """Retrieve an emoji from the cache.

        Ensures initialization before attempting retrieval.

        Parameters
        ----------
        name : str
            The name of the emoji to retrieve.

        Returns
        -------
        discord.Emoji | None
            The discord.Emoji object if found, None otherwise.
        """
        if not self._initialized:
            logger.warning(
                "Attempted to get emoji before cache initialization. Call await manager.init() first.",
            )

            # Avoid deadlocks: Do not call init() here directly.
            # Rely on the initial setup_hook call.
            return None

        return self.cache.get(name)

    async def _create_discord_emoji(
        self,
        name: str,
        image_bytes: bytes,
    ) -> discord.Emoji | None:
        """Create a Discord emoji with error handling and delay.

        Parameters
        ----------
        name : str
            The name of the emoji to create.
        image_bytes : bytes
            The image bytes of the emoji to create.

        Returns
        -------
        discord.Emoji | None
            The newly created emoji if successful, otherwise None.
        """
        if not _is_valid_emoji_name(name):
            logger.error(f"Attempted to create emoji with invalid name: '{name}'")
            return None

        try:
            await asyncio.sleep(self.create_delay)
            emoji = await self.bot.create_application_emoji(
                name=name,
                image=image_bytes,
            )
            self.cache[name] = emoji  # Update cache immediately
            logger.success(f"Successfully created emoji '{name}'. ID: {emoji.id}")
            return emoji  # noqa: TRY300

        except discord.HTTPException as e:
            logger.error(f"Failed to create emoji '{name}': {e}")
        except ValueError as e:
            logger.error(f"Invalid value for creating emoji '{name}': {e}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred creating emoji '{name}': {e}",
            )
            capture_exception_safe(
                e,
                extra_context={
                    "operation": "create_emoji",
                    "emoji_name": name,
                },
            )

        return None

    async def _process_emoji_file(
        self,
        file_path: Path,
    ) -> tuple[discord.Emoji | None, Path | None]:
        """Process a single emoji file.

        Parameters
        ----------
        file_path : Path
            The path to the emoji file to process

        Returns
        -------
        tuple[discord.Emoji | None, Path | None]
            A tuple where the first element is the newly created emoji (if created)
            and the second element is the file_path if processing failed or was skipped.
        """
        if not file_path.is_file():
            logger.trace(f"Skipping non-file item: {file_path.name}")
            return None, file_path

        emoji_name = file_path.stem

        if not _is_valid_emoji_name(emoji_name):
            logger.warning(
                f"Skipping file with invalid potential emoji name: {file_path.name}",
            )
            return None, file_path

        if self.get(emoji_name):
            logger.trace(f"Emoji '{emoji_name}' already exists, skipping.")
            return None, file_path

        logger.debug(
            f"Emoji '{emoji_name}' not found in cache, attempting to create from {file_path.name}.",
        )

        if img_bytes := _read_emoji_file(file_path):
            new_emoji = await self._create_discord_emoji(emoji_name, img_bytes)
            if new_emoji:
                return new_emoji, None

        return None, file_path  # Failed creation or read

    async def sync_emojis(self) -> tuple[list[discord.Emoji], list[Path]]:
        """Synchronize emojis from the local assets directory to the application.

        Ensures the cache is initialized, then iterates through local emoji files.
        If an emoji with the same name doesn't exist in the cache, it attempts to create it.

        Returns
        -------
        tuple[list[discord.Emoji], list[Path]]
            A tuple containing:
            - A list of successfully created discord.Emoji objects.
            - A list of file paths for emojis that already existed or failed.
        """
        if not await self._ensure_initialized():
            logger.error("Cannot sync emojis: Cache initialization failed.")
            # Attempt to list files anyway for the return value

            with contextlib.suppress(Exception):
                return [], list(self.emojis_path.iterdir())
            return [], []

        logger.info(f"Starting emoji synchronization from {self.emojis_path}...")

        duplicates_or_failed: list[Path] = []
        created_emojis: list[discord.Emoji] = []

        try:
            files_to_process = list(self.emojis_path.iterdir())
        except OSError as e:
            logger.error(
                f"Failed to list files in emoji directory {self.emojis_path}: {e}",
            )
            return [], []

        if not files_to_process:
            logger.warning(f"No files found in emoji directory: {self.emojis_path}")
            return [], []

        for file_path in files_to_process:
            emoji, failed_file = await self._process_emoji_file(file_path)
            if emoji:
                created_emojis.append(emoji)
            elif failed_file:
                duplicates_or_failed.append(failed_file)

        logger.info(
            f"Emoji synchronization finished. "
            f"Created: {len(created_emojis)}, Duplicates/Skipped/Failed: {len(duplicates_or_failed)}.",
        )

        return created_emojis, duplicates_or_failed

    async def _ensure_initialized(self) -> bool:
        """
        Check if cache is initialized, logs warning if not.

        Returns
        -------
        bool
            True if initialized, False otherwise.
        """
        if self._initialized:
            return True
        logger.warning(
            "Operation called before cache was initialized. Call await manager.init() first.",
        )
        # Attempting init() again might lead to issues/deadlocks depending on context.
        # Force initialization in setup_hook.
        return False

    async def _delete_discord_emoji(self, name: str) -> bool:
        """Delete an existing Discord emoji by name and updates cache.

        Parameters
        ----------
        name : str
            The name of the emoji to delete.

        Returns
        -------
        bool
            True if the emoji was deleted, False otherwise.
        """
        existing_emoji = self.get(name)
        if not existing_emoji:
            logger.info(
                f"No existing emoji '{name}' found in cache. Skipping deletion.",
            )
            return False  # Indicate no deletion occurred

        logger.debug(f"Attempting deletion of application emoji '{name}'...")
        deleted_on_discord = False

        try:
            await existing_emoji.delete()
            logger.success(f"Successfully deleted existing application emoji '{name}'.")
            deleted_on_discord = True

        except discord.NotFound:
            logger.warning(
                f"Emoji '{name}' was in cache but not found on Discord for deletion.",
            )
        except discord.Forbidden:
            logger.error(f"Missing permissions to delete application emoji '{name}'.")
        except discord.HTTPException as e:
            logger.error(f"Failed to delete application emoji '{name}': {e}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred deleting emoji '{name}': {e}",
            )
            capture_exception_safe(
                e,
                extra_context={
                    "operation": "delete_emoji",
                    "emoji_name": name,
                },
            )

        finally:
            # Always remove from cache if it was found initially
            if self.cache.pop(name, None):
                logger.debug(f"Removed '{name}' from cache.")

        return deleted_on_discord

    async def resync_emoji(self, name: str) -> discord.Emoji | None:
        """Resync a specific emoji: Deletes existing, finds local file, creates new.

        Parameters
        ----------
        name : str
            The name of the emoji to resync.

        Returns
        -------
        Optional[discord.Emoji]
            The newly created emoji if successful, otherwise None.
        """
        logger.info(f"Starting resync process for emoji: '{name}'...")

        if not await self._ensure_initialized():
            return None  # Stop if initialization failed

        # Step 1 & 2: Delete existing emoji (if any) and remove from cache
        await self._delete_discord_emoji(name)

        # Step 3: Find the local file
        local_file_path = _find_emoji_file(self.emojis_path, name)
        if not local_file_path:
            # Error logged in utility function
            logger.error(f"Resync failed for '{name}': Could not find local file.")
            return None

        # Step 4: Process the found emoji file
        new_emoji, _ = await self._process_emoji_file(local_file_path)

        if new_emoji:
            logger.info(
                f"Resync completed successfully for '{name}'. New ID: {new_emoji.id}",
            )
        else:
            logger.error(f"Resync failed for '{name}' during creation step.")

        logger.info(
            f"Resync process for emoji '{name}' finished.",
        )  # Log finish regardless of success
        return new_emoji

    async def delete_all_emojis(self) -> tuple[list[str], list[str]]:
        """Delete all application emojis that match names from the emoji assets directory.

        This method:
        1. Ensures the emoji cache is initialized
        2. Finds all potential emoji names from the assets directory
        3. Deletes any matching emojis from Discord and updates the cache

        Returns
        -------
        tuple[list[str], list[str]]
            A tuple containing:
            - A list of successfully deleted emoji names
            - A list of emoji names that failed to delete or weren't found
        """
        if not await self._ensure_initialized():
            logger.error("Cannot delete emojis: Cache initialization failed.")
            return [], []

        logger.info(
            "Starting deletion of all application emojis matching asset directory...",
        )

        # Get all potential emoji names from the asset directory
        emoji_names_to_delete: set[str] = set()
        try:
            for file_path in self.emojis_path.iterdir():
                if file_path.is_file() and _is_valid_emoji_name(file_path.stem):
                    emoji_names_to_delete.add(file_path.stem)
        except OSError as e:
            logger.error(
                f"Failed to list files in emoji directory {self.emojis_path}: {e}",
            )
            return [], []

        if not emoji_names_to_delete:
            logger.warning(
                f"No valid emoji names found in directory: {self.emojis_path}",
            )
            return [], []

        deleted_names: list[str] = []
        failed_names: list[str] = []

        # Process each emoji name
        for emoji_name in emoji_names_to_delete:
            logger.debug(f"Attempting to delete emoji: '{emoji_name}'")

            if await self._delete_discord_emoji(emoji_name):
                deleted_names.append(emoji_name)
            else:
                failed_names.append(emoji_name)

        logger.info(
            f"Emoji deletion finished. Deleted: {len(deleted_names)}, Failed/Not Found: {len(failed_names)}.",
        )

        return deleted_names, failed_names
