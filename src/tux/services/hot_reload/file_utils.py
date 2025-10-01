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
    """Convert extension name to file path."""
    if base_dir is None:
        base_dir = Path("src")

    # Convert dot notation to path
    parts = extension.split(".")
    return base_dir / Path(*parts[1:]) / f"{parts[-1]}.py"


def get_extension_from_path(file_path: Path, base_dir: Path) -> str | None:
    """Convert file path to extension name."""
    try:
        relative_path = file_path.relative_to(base_dir)
        if relative_path.suffix != ".py":
            return None

        # Convert path to dot notation
        *path_parts, filename = relative_path.parts
        stem = Path(filename).stem
        parts = [*path_parts, stem]

        # For files in cog directories, return the cog extension, not the individual module
        # Check if this is a cog by looking for setup function in the module
        module_name = "tux." + ".".join(parts)
        with suppress(ImportError):
            module = importlib.import_module(module_name)
            if hasattr(module, "setup") and callable(module.setup):
                # This is a cog, return its full path
                return module_name

        # Not a cog, check if parent directory contains a cog
        # Remove the last part (filename) and check the parent module
        if len(parts) > 1:
            parent_module_name = "tux." + ".".join(parts[:-1])
            # Check if there's a cog.py file in the parent directory
            cog_module_name = f"{parent_module_name}.cog"
            with suppress(ImportError):
                cog_module = importlib.import_module(cog_module_name)
                if hasattr(cog_module, "setup") and callable(cog_module.setup):
                    # Found cog.py with setup, return the cog module name
                    return cog_module_name

        # This is not a cog or cog-related module, don't treat as extension
        return None  # noqa: TRY300
    except ValueError:
        return None


def validate_python_syntax(file_path: Path) -> bool:
    """Validate Python syntax of a file."""
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
    """Reload a module by name."""
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
        self._hashes: dict[Path, str] = {}

    def get_file_hash(self, file_path: Path) -> str:
        """Get SHA-256 hash of file contents."""
        try:
            with file_path.open("rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash file {file_path}: {e}")
            return ""

    def has_changed(self, file_path: Path) -> bool:
        """Check if file has changed since last check."""
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
