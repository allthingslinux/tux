#!/usr/bin/env python3
"""Script to update import paths from tux.bot to tux.core.bot."""

import os
import re
from pathlib import Path


def update_imports_in_file(file_path: Path) -> bool:
    """Update import paths in a single file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Only update if the file contains the old import
        if "from tux.core.bot" in content or "from tux.bot " in content:
            new_content = re.sub(
                r"from\s+tux\.bot(?:\s+import|\s+import\s+(.*))",
                r"from tux.core.bot\1",
                content,
            )
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return False


def main():
    """Main function to update imports in all Python files."""
    root_dir = Path(__file__).parent.parent
    updated_files = 0

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                if update_imports_in_file(file_path):
                    print(f"Updated imports in: {file_path.relative_to(root_dir)}")
                    updated_files += 1

    print(f"\nUpdated imports in {updated_files} files.")


if __name__ == "__main__":
    main()
