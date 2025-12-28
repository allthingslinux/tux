"""File utilities for hot reload system."""

import ast
import hashlib
import importlib
import sys
from contextlib import contextmanager, suppress
from pathlib import Path

from loguru import logger

from .config import ModuleReloadError


def path_from_extension(extension: str, *, base_dir: Path | None = None) -> Path:
    """
    Convert extension name to file path.

    Returns
    -------
    Path
        The file path for the extension.
    """
    if base_dir is None:
        base_dir = Path("src")

    # Convert dot notation to path
    parts = extension.split(".")
    return base_dir / Path(*parts[1:]) / f"{parts[-1]}.py"


def get_extension_from_path(file_path: Path, base_dir: Path) -> str | None:
    """
    Convert file path to extension name.

    Handles both flat and nested plugin structures:
    - src/tux/modules/admin/ban.py → tux.modules.admin.ban
    - src/tux/plugins/atl/deepfry.py → tux.plugins.atl.deepfry

    Returns
    -------
    str | None
        The extension name if found, None otherwise.
    """
    try:
        relative_path = file_path.relative_to(base_dir)
    except ValueError:
        return None

    if relative_path.suffix != ".py":
        return None

    # Convert path to dot notation
    *path_parts, filename = relative_path.parts
    stem = Path(filename).stem
    parts = [*path_parts, stem]
    module_name = "tux." + ".".join(parts)

    logger.trace(f"Checking if {module_name} is a loadable extension")

    # Check if this module has a setup function (it's a cog)
    with suppress(ImportError, AttributeError):
        module = importlib.import_module(module_name)
        if hasattr(module, "setup") and callable(module.setup):
            logger.trace(f"Found cog with setup: {module_name}")
            return module_name

    # Check parent directory for cog (for supporting files in subdirs)
    if len(parts) > 1:
        parent_module_name = "tux." + ".".join(parts[:-1])

        # Try parent's __init__.py for setup
        with suppress(ImportError, AttributeError):
            parent_module = importlib.import_module(parent_module_name)
            if hasattr(parent_module, "setup") and callable(parent_module.setup):
                logger.trace(f"Found parent cog: {parent_module_name}")
                return parent_module_name

        # Try cog.py in parent directory
        with suppress(ImportError, AttributeError):
            cog_module = importlib.import_module(f"{parent_module_name}.cog")
            if hasattr(cog_module, "setup") and callable(cog_module.setup):
                logger.trace(f"Found cog.py: {parent_module_name}.cog")
                return f"{parent_module_name}.cog"

    logger.trace(f"Not a loadable extension: {module_name}")
    return None


def validate_python_syntax(file_path: Path) -> bool:
    """
    Validate Python syntax of a file.

    Returns
    -------
    bool
        True if syntax is valid, False otherwise.
    """
    try:
        with file_path.open(encoding="utf-8") as f:
            source = f.read()
        ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError) as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating syntax for {file_path}: {e}")
        return False
    else:
        return True


@contextmanager
def module_reload_context(module_name: str):
    """Context manager for safe module reloading."""
    original_module = sys.modules.get(module_name)
    try:
        yield
    except Exception:
        # Restore original module on error
        if original_module is not None:
            sys.modules[module_name] = original_module
        elif module_name in sys.modules:
            del sys.modules[module_name]
        raise


def reload_module_by_name(module_name: str) -> bool:
    """
    Reload a module by name.

    Returns
    -------
    bool
        True if reload was successful.

    Raises
    ------
    ModuleReloadError
        If the module fails to reload.
    """
    try:
        with module_reload_context(module_name):
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            else:
                importlib.import_module(module_name)
    except Exception as e:
        logger.error(f"Failed to reload module {module_name}: {e}")
        msg = f"Failed to reload {module_name}"
        raise ModuleReloadError(msg) from e
    else:
        return True


class FileHashTracker:
    """Tracks file hashes to detect changes."""

    def __init__(self) -> None:
        """Initialize the file hash tracker."""
        self._hashes: dict[Path, str] = {}

    def get_file_hash(self, file_path: Path) -> str:
        """
        Get SHA-256 hash of file contents.

        Returns
        -------
        str
            The SHA-256 hash of the file, or empty string if error.
        """
        try:
            with file_path.open("rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash file {file_path}: {e}")
            return ""

    def has_changed(self, file_path: Path) -> bool:
        """
        Check if file has changed since last check.

        Returns
        -------
        bool
            True if file has changed, False otherwise.
        """
        current_hash = self.get_file_hash(file_path)
        previous_hash = self._hashes.get(file_path)

        if previous_hash is None or current_hash != previous_hash:
            self._hashes[file_path] = current_hash
            return True
        return False

    def update_hash(self, file_path: Path) -> None:
        """Update stored hash for a file."""
        self._hashes[file_path] = self.get_file_hash(file_path)

    def clear(self) -> None:
        """Clear all stored hashes."""
        self._hashes.clear()

    def remove_file(self, file_path: Path) -> None:
        """Remove file from tracking."""
        self._hashes.pop(file_path, None)
