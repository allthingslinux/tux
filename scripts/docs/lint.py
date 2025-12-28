"""
Command: docs lint.

Lints documentation files.
"""

from pathlib import Path

from typer import Exit

from scripts.core import create_app
from scripts.ui import (
    create_progress_bar,
    print_error,
    print_pretty,
    print_section,
    print_success,
    print_warning,
)

app = create_app()

# Constants
YAML_FRONTMATTER_PARTS = 3


@app.command(name="lint")
def lint() -> None:
    """Lint documentation files."""
    print_section("Linting Documentation", "blue")

    docs_dir = Path("docs/content")
    if not docs_dir.exists():
        print_error("docs/content directory not found")
        raise Exit(1)

    all_md_files = list(docs_dir.rglob("*.md"))
    issues: list[str] = []

    with create_progress_bar(
        total=len(all_md_files),
    ) as progress:
        task = progress.add_task("Scanning Documentation...", total=len(all_md_files))

        for md_file in all_md_files:
            progress.update(task, description=f"Scanning {md_file.name}...")
            try:
                content = md_file.read_text()

                # Skip YAML frontmatter if present
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= YAML_FRONTMATTER_PARTS:
                        content = parts[2].strip()
                else:
                    content = content.strip()

                if content == "":
                    issues.append(f"Empty file: {md_file}")
                elif not content.startswith("#"):
                    issues.append(f"Missing title: {md_file}")
                elif "TODO" in content.upper() or "FIXME" in content.upper():
                    issues.append(f"Contains TODO/FIXME: {md_file}")
            except (UnicodeDecodeError, OSError) as e:
                issues.append(f"Could not read {md_file}: {e}")

            progress.advance(task)

    if issues:
        print_warning(f"Found {len(issues)} issues in documentation:")
        print_pretty(issues)
        raise Exit(1)
    print_success("No issues found in documentation!")


if __name__ == "__main__":
    app()
