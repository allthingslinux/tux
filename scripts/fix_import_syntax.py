#!/usr/bin/env python3
"""Script to fix import syntax after path updates."""

import os
from pathlib import Path


def fix_imports_in_file(file_path: Path) -> bool:
    """Fix import syntax in a single file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Fix missing 'import' keyword
        if "from tux.core.bot import Tux" in content:
            new_content = content.replace(
                "from tux.core.bot import Tux",
                "from tux.core.bot import Tux",
            )
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return False


def main():
    """Main function to fix imports in all Python files."""
    root_dir = Path(__file__).parent.parent
    fixed_files = 0

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                if fix_imports_in_file(file_path):
                    print(f"Fixed imports in: {file_path.relative_to(root_dir)}")
                    fixed_files += 1

    print(f"\nFixed imports in {fixed_files} files.")


if __name__ == "__main__":
    main()
