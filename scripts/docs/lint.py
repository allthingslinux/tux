"""
Command: docs lint.

Lints documentation files.
"""

from pathlib import Path

from scripts.core import create_app
from scripts.ui import (
    create_progress_bar,
    print_error,
    print_section,
    print_success,
    print_warning,
)

app = create_app()


@app.command(name="lint")
def lint() -> None:
    """Lint documentation files."""
    print_section("Linting Documentation", "blue")

    docs_dir = Path("docs/content")
    if not docs_dir.exists():
        print_error("docs/content directory not found")
        return

    all_md_files = list(docs_dir.rglob("*.md"))
    issues: list[str] = []

    with create_progress_bar(
        "Scanning Documentation...",
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
                    if len(parts) >= 3:
                        content = parts[2].strip()

                if content.strip() == "":
                    issues.append(f"Empty file: {md_file}")
                elif not content.startswith("#"):
                    issues.append(f"Missing title: {md_file}")
                elif "TODO" in content or "FIXME" in content:
                    issues.append(f"Contains TODO/FIXME: {md_file}")
            except Exception as e:
                issues.append(f"Error reading {md_file}: {e}")

            progress.advance(task)

    if issues:
        print_warning("\nDocumentation linting issues found:")
        for issue in issues:
            print_warning(f"  • {issue}")
    else:
        print_success("No documentation linting issues found")


if __name__ == "__main__":
    app()
