import os
from pathlib import Path


def replace_in_file(file_path, old_str, new_str):
    try:
        # Read the file
        with open(file_path, encoding="utf-8") as file:
            file_contents = file.read()

        # Skip binary files
        if "\0" in file_contents:
            return 0

        # Replace the string
        new_contents = file_contents.replace(old_str, new_str)

        # Only write if changes were made
        if new_contents != file_contents:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(new_contents)
            return 1
        return 0
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0


def process_directory(root_dir, old_str, new_str):
    # File extensions to process
    extensions = {".py", ".md", ".txt", ".ini", ".toml", ".yaml", ".yml"}

    total_replacements = 0
    processed_files = 0

    for root, _, files in os.walk(root_dir):
        # Skip certain directories
        if any(skip_dir in root for skip_dir in ["__pycache__", ".git", ".mypy_cache", ".pytest_cache", "venv"]):
            continue

        for file in files:
            if file.endswith(tuple(extensions)):
                file_path = os.path.join(root, file)
                replacements = replace_in_file(file_path, old_str, new_str)
                if replacements > 0:
                    print(f"Updated: {file_path}")
                    total_replacements += replacements
                    processed_files += 1

    print(f"\nTotal files processed: {processed_files}")
    print(f"Total replacements made: {total_replacements}")


if __name__ == "__main__":
    # Get the project root directory (one level up from the current file's directory)
    project_root = str(Path(__file__).parent)

    print("Starting import updates...")

    # Replace 'tux.modules' with 'tux.modules'
    print("\nUpdating 'tux.modules' to 'tux.modules'...")
    process_directory(project_root, "tux.modules", "tux.modules")

    # Also replace any relative imports that might have been using cogs
    print("\nUpdating relative imports...")
    process_directory(project_root, "from .modules", "from .modules")
    process_directory(project_root, "from ..modules", "from ..modules")

    print("\nReplacement complete!")
