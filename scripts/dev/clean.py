"""
Command: dev clean.

Cleans temporary files, cache directories, and build artifacts.
"""

import shutil
from pathlib import Path

from scripts.core import ROOT, create_app
from scripts.ui import (
    create_progress_bar,
    print_info,
    print_section,
    print_success,
    print_warning,
    rich_print,
)

app = create_app()


def _remove_item(item: Path, project_root: Path) -> tuple[int, int]:
    """Remove a file or directory and return (count, size)."""
    try:
        if item.is_file():
            size = item.stat().st_size
            item.unlink()
            rich_print(f"[dim]Removed: {item.relative_to(project_root)}[/dim]")
            return (1, size)
        if item.is_dir():
            dir_size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
            shutil.rmtree(item)
            rich_print(f"[dim]Removed: {item.relative_to(project_root)}/[/dim]")
            return (1, dir_size)
    except OSError as e:
        print_warning(f"Could not remove {item.relative_to(project_root)}: {e}")
    return (0, 0)


def _clean_empty_directories(project_root: Path) -> int:
    """Clean empty directories and replica structures in scripts."""
    cleaned = 0
    for dir_path in [
        project_root / "scripts",
    ]:
        if not dir_path.exists():
            continue

        for subdir in dir_path.iterdir():
            if not subdir.is_dir() or subdir.name in ("__pycache__", ".pytest_cache"):
                continue

            contents = list(subdir.iterdir())
            if not contents or all(
                item.name == "__pycache__" and item.is_dir() for item in contents
            ):
                try:
                    shutil.rmtree(subdir)
                    cleaned += 1
                    rich_print(
                        f"[dim]Removed empty directory: {subdir.relative_to(project_root)}/[/dim]",
                    )
                except OSError as e:
                    print_warning(
                        f"Could not remove {subdir.relative_to(project_root)}: {e}",
                    )
    return cleaned


@app.command(name="clean")
def clean() -> None:
    """Clean temporary files, cache directories, and build artifacts."""
    print_section("Cleaning Project", "blue")

    project_root = ROOT
    cleaned_count = 0
    total_size = 0

    patterns_to_clean = [
        ("**/__pycache__", "Python cache directories"),
        ("**/*.pyc", "Python compiled files"),
        ("**/*.pyo", "Python optimized files"),
        ("**/*$py.class", "Python class files"),
        (".pytest_cache", "Pytest cache directory"),
        (".coverage", "Coverage data file"),
        (".coverage.*", "Coverage data files"),
        (".ruff_cache", "Ruff cache directory"),
        (".mypy_cache", "Mypy cache directory"),
        ("build", "Build directory"),
        ("dist", "Distribution directory"),
        ("*.egg-info", "Egg info directories"),
        ("htmlcov", "HTML coverage reports"),
        ("coverage.xml", "Coverage XML report"),
        ("coverage.json", "Coverage JSON report"),
        ("lcov.info", "LCOV coverage report"),
        ("junit.xml", "JUnit XML report"),
        (".hypothesis", "Hypothesis cache"),
    ]

    protected_dirs = {".venv", "venv"}

    with create_progress_bar(
        total=len(patterns_to_clean),
    ) as progress:
        task = progress.add_task("Cleaning Project...", total=len(patterns_to_clean))

        for pattern, description in patterns_to_clean:
            progress.update(task, description=f"Cleaning {description}...")
            matches = list(project_root.glob(pattern))
            if not matches:
                progress.advance(task)
                continue

            # Better component-based check for protected dirs
            matches = [
                m
                for m in matches
                if not any(part in protected_dirs for part in m.parts)
            ]

            if not matches:
                progress.advance(task)
                continue

            for item in matches:
                count, size = _remove_item(item, project_root)
                cleaned_count += count
                total_size += size

            progress.advance(task)

    cleaned_count += _clean_empty_directories(project_root)

    if cleaned_count > 0:
        size_mb = total_size / (1024 * 1024)
        print_success(f"Cleaned {cleaned_count} item(s), freed {size_mb:.2f} MB")
    else:
        print_info("Nothing to clean - project is already clean!")


if __name__ == "__main__":
    app()
