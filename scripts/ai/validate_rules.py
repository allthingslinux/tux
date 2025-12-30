"""
Command: ai validate-rules.

Validates Cursor rules and commands to ensure they follow Tux project standards.
"""

import re
from pathlib import Path
from typing import Annotated

from rich.panel import Panel
from rich.table import Table
from typer import Exit, Option

from scripts.core import create_app
from scripts.ui import console

app = create_app()

# Files exempt from the 500-line limit
LARGE_FILE_EXCEPTIONS: set[str] = {"**/ui/cv2.mdc"}


def _check_rule_frontmatter(
    file_path: Path,
    content: str,
) -> tuple[list[str], str | None]:
    """Check rule frontmatter format.

    Parameters
    ----------
    file_path : Path
        Path to the rule file.
    content : str
        File content.

    Returns
    -------
    tuple[list[str], str | None]
        List of errors and frontmatter content (or None if invalid).
    """
    errors: list[str] = []

    if not content.startswith("---"):
        errors.append(f"{file_path}: Rule must start with frontmatter (---)")
        return errors, None

    frontmatter_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not frontmatter_match:
        errors.append(
            f"{file_path}: Invalid or missing closing frontmatter (---)",
        )
        return errors, None

    frontmatter = frontmatter_match[1]

    # Check globs format (must be comma-separated, not array format)
    if "globs:" in frontmatter:  # noqa: SIM102
        if globs_line_match := re.search(
            r"^globs:\s*(.+)$",
            frontmatter,
            re.MULTILINE,
        ):
            globs_value = globs_line_match[1].strip()
            # Check for array format (incorrect)
            if globs_value.startswith("[") and globs_value.endswith("]"):
                errors.append(
                    f"{file_path}: globs must use comma-separated format, not array format. "
                    f"Use 'globs: pattern1, pattern2' instead of 'globs: [\"pattern1\", \"pattern2\"]'",
                )
            # Check for quoted individual patterns (incorrect)
            elif '"' in globs_value or "'" in globs_value:
                errors.append(
                    f"{file_path}: globs patterns should not be quoted. "
                    f"Use 'globs: pattern1, pattern2' instead of 'globs: \"pattern1\", \"pattern2\"'",
                )

    return errors, frontmatter


def _check_rule_description(
    file_path: Path,
    frontmatter: str,
    is_spec: bool,
    is_reference: bool,
) -> list[str]:
    """Check rule description requirements.

    Parameters
    ----------
    file_path : Path
        Path to the rule file.
    frontmatter : str
        Frontmatter content.
    is_spec : bool
        Whether this is a specification file.
    is_reference : bool
        Whether this is a reference file.

    Returns
    -------
    list[str]
        List of errors.
    """
    errors: list[str] = []

    # Check description (required for intelligent rules, except specs)
    if (
        "description:" not in frontmatter
        and "alwaysApply: true" not in frontmatter
        and not is_spec
    ):
        errors.append(f"{file_path}: Rule must include description field")

    # Check description length (skip for specs and references)
    if not is_spec and not is_reference:  # noqa: SIM102
        if desc_match := re.search(r"description:\s*(.+)", frontmatter):
            desc = desc_match[1].strip().strip('"').strip("'")
            if len(desc) < 60 or len(desc) > 120:
                errors.append(
                    f"{file_path}: Description should be 60-120 chars (found {len(desc)})",
                )

    return errors


def _check_rule_content(
    file_path: Path,
    content: str,
    frontmatter_end: int,
    is_spec: bool,
    is_reference: bool,
    is_docs_rule: bool,
) -> list[str]:
    """Check rule content requirements.

    Parameters
    ----------
    file_path : Path
        Path to the rule file.
    content : str
        File content.
    frontmatter_end : int
        End position of frontmatter.
    is_spec : bool
        Whether this is a specification file.
    is_reference : bool
        Whether this is a reference file.
    is_docs_rule : bool
        Whether this is a documentation rule.

    Returns
    -------
    list[str]
        List of errors.
    """
    errors: list[str] = []

    if not is_reference:
        body = content[frontmatter_end:]
        if "# " not in body:
            errors.append(f"{file_path}: Rule must have title (H1)")

        # Check for patterns section (skip for specs, references, and docs rules)
        should_check_patterns = not (is_spec or is_reference or is_docs_rule)
        if should_check_patterns:
            if "✅" not in body and "❌" not in body:
                errors.append(
                    f"{file_path}: Rule should include patterns with ✅ GOOD / ❌ BAD examples",
                )

            # Check for code examples
            if "```" not in body:
                errors.append(f"{file_path}: Rule should include code examples")

    return errors


def _validate_rule(file_path: Path) -> list[str]:
    """Validate a rule file.

    Parameters
    ----------
    file_path : Path
        Path to the rule file to validate.

    Returns
    -------
    list[str]
        List of error messages, empty if valid.
    """
    errors: list[str] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        return [f"{file_path}: Failed to read file: {e}"]
    except UnicodeDecodeError as e:
        return [f"{file_path}: Invalid encoding: {e}"]

    # Special cases: reference files, specifications, and documentation rules
    is_reference = file_path.name == "rules.mdc"
    is_spec = "meta" in file_path.parts
    is_docs_rule = "docs" in file_path.parts
    is_large_reference = any(
        file_path.match(pattern) for pattern in LARGE_FILE_EXCEPTIONS
    )

    # Check frontmatter
    frontmatter_errors, frontmatter = _check_rule_frontmatter(
        file_path,
        content,
    )
    errors.extend(frontmatter_errors)
    if frontmatter is None:
        return errors  # Can't continue without valid frontmatter

    # Check description
    errors.extend(
        _check_rule_description(file_path, frontmatter, is_spec, is_reference),
    )

    # Check size (max 500 lines, but allow exceptions for specs and large references)
    line_count = len(content.split("\n"))
    if line_count > 500 and not is_spec and not is_large_reference:
        errors.append(
            f"{file_path}: Rule exceeds 500 lines (found {line_count} lines)",
        )

    # Check content
    if frontmatter_match := re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL):
        errors.extend(
            _check_rule_content(
                file_path,
                content,
                frontmatter_match.end(),
                is_spec,
                is_reference,
                is_docs_rule,
            ),
        )

    return errors


def _validate_command(file_path: Path) -> list[str]:
    """Validate a command file.

    Parameters
    ----------
    file_path : Path
        Path to the command file to validate.

    Returns
    -------
    list[str]
        List of error messages, empty if valid.
    """
    errors: list[str] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        return [f"{file_path}: Failed to read file: {e}"]
    except UnicodeDecodeError as e:
        return [f"{file_path}: Invalid encoding: {e}"]

    # Check for frontmatter (commands should NOT have frontmatter)
    if content.startswith("---"):
        errors.append(
            f"{file_path}: Command must NOT have frontmatter (use plain Markdown)",
        )

    # Check for required sections
    if "# " not in content:
        errors.append(f"{file_path}: Command must have title (H1)")

    if "## Overview" not in content:
        errors.append(f"{file_path}: Command must have Overview section")

    if "## Steps" not in content:
        errors.append(f"{file_path}: Command must have Steps section")

    # Check for checklist (flexible naming)
    if not re.search(r"## .*[Cc]hecklist", content):
        errors.append(f"{file_path}: Command must have Checklist section")

    # Check for numbered steps
    if not re.search(r"^\d+\.\s+\*\*", content, re.MULTILINE):
        errors.append(
            f"{file_path}: Steps should be numbered and bolded (1. **Title**, 2. **Title**)",
        )

    # Check checklist format
    if not re.search(r"- \[ \]", content):
        errors.append(f"{file_path}: Checklist should use - [ ] format")

    return errors


def _print_validation_summary(
    rule_files: list[Path],
    cmd_files: list[Path],
    all_errors: list[str],
) -> None:
    """Print validation summary table.

    Parameters
    ----------
    rule_files : list[Path]
        List of rule files validated.
    cmd_files : list[Path]
        List of command files validated.
    all_errors : list[str]
        List of validation errors.
    """
    has_errors = len(all_errors) > 0
    header_style = "bold red" if has_errors else "bold green"
    count_style = "red" if has_errors else "green"

    table = Table(
        title="Validation Summary",
        show_header=True,
        header_style=header_style,
    )
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Count", style=count_style, justify="right")
    table.add_row("Rules", str(len(rule_files)))
    table.add_row("Commands", str(len(cmd_files)))

    if has_errors:
        table.add_row("Errors", str(len(all_errors)), style="bold red")
        console.print("\n")
        console.print(table)
        console.print(
            f"\n[bold red]Validation failed with {len(all_errors)} error(s)[/bold red]",
        )
    else:
        table.add_row("Status", "✓ All valid", style="bold green")
        console.print("\n")
        console.print(table)
        console.print(
            "\n[bold green]✓ All rules and commands are valid![/bold green]",
        )


@app.command(name="validate-rules")
def validate_rules(
    rules_dir: Annotated[
        Path,
        Option(
            "--rules-dir",
            help="Directory containing rule files",
        ),
    ] = Path(".cursor/rules"),
    commands_dir: Annotated[
        Path,
        Option(
            "--commands-dir",
            help="Directory containing command files",
        ),
    ] = Path(".cursor/commands"),
) -> None:
    """Validate all rules and commands.

    This command validates that all rules and commands follow the Tux project
    standards for structure, content, and metadata.

    Parameters
    ----------
    rules_dir : Path
        Directory containing rule files (default: .cursor/rules).
    commands_dir : Path
        Directory containing command files (default: .cursor/commands).
    """
    console.print(
        Panel.fit("Rules & Commands Validator", style="bold blue"),
    )

    all_errors: list[str] = []

    # Validate rules (treat missing directory as empty set)
    if rules_dir.exists():
        rule_files = sorted(rules_dir.rglob("*.mdc"))
        console.print(f"\n[bold]Validating {len(rule_files)} rule files...[/bold]")
        for rule_file in rule_files:
            errors = _validate_rule(rule_file)
            all_errors.extend(errors)
            if errors:
                for error in errors:
                    console.print(f"  [red]✗[/red] {error}")
    else:
        console.print(
            f"\n[yellow]Warning: {rules_dir} does not exist, skipping rules validation[/yellow]",
        )
        rule_files = []

    # Validate commands (treat missing directory as empty set)
    if commands_dir.exists():
        cmd_files = sorted(commands_dir.rglob("*.md"))
        console.print(
            f"\n[bold]Validating {len(cmd_files)} command files...[/bold]",
        )
        for cmd_file in cmd_files:
            errors = _validate_command(cmd_file)
            all_errors.extend(errors)
            if errors:
                for error in errors:
                    console.print(f"  [red]✗[/red] {error}")
    else:
        console.print(
            f"\n[yellow]Warning: {commands_dir} does not exist, skipping commands validation[/yellow]",
        )
        cmd_files = []

    # Report results
    _print_validation_summary(
        rule_files,
        cmd_files,
        all_errors,
    )

    if all_errors:
        raise Exit(code=1)


if __name__ == "__main__":
    app()
