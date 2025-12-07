#!/usr/bin/env python3

"""Cursor rules and commands validation CLI for Tux.

This script provides commands for validating Cursor rules and commands
to ensure they follow the Tux project standards.
"""

import re
from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel
from rich.table import Table
from typer import Option  # type: ignore[attr-defined]

from scripts.base import BaseCLI
from scripts.registry import Command


class CursorCLI(BaseCLI):
    """Cursor rules and commands validation CLI."""

    def __init__(self) -> None:
        """Initialize the CursorCLI."""
        super().__init__(
            name="cursor",
            description="Cursor rules and commands validation",
        )
        self._setup_command_registry()
        self._setup_commands()

    def _setup_command_registry(self) -> None:
        """Set up the command registry with all cursor commands."""
        all_commands = [
            Command(
                "validate",
                self.validate,
                "Validate all Cursor rules and commands",
            ),
        ]

        for cmd in all_commands:
            self._command_registry.register_command(cmd)

    def _setup_commands(self) -> None:
        """Set up all cursor CLI commands using the command registry."""

        # Add a no-op callback to force Typer into subcommand mode
        # This prevents Typer from treating a single command with only Options as the main command
        @self.app.callback(invoke_without_command=False)
        def _main_callback() -> None:  # pyright: ignore[reportUnusedFunction]
            """Cursor rules and commands validation CLI."""

        # Now register commands as subcommands
        for command in self._command_registry.get_commands().values():
            self.add_command(
                command.func,
                name=command.name,
                help_text=command.help_text,
            )

    def _check_rule_frontmatter(
        self,
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

        if "---\n" not in content[4:]:
            errors.append(f"{file_path}: Rule must have closing frontmatter (---)")

        frontmatter_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not frontmatter_match:
            errors.append(f"{file_path}: Invalid frontmatter format")
            return errors, None

        frontmatter = frontmatter_match[1]

        # Check globs format (must be comma-separated, not array format)
        if "globs:" in frontmatter:
            globs_line_match = re.search(r"^globs:\s*(.+)$", frontmatter, re.MULTILINE)
            if globs_line_match:
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
        self,
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
        self,
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

    def _validate_rule(self, file_path: Path) -> list[str]:
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
        content = file_path.read_text(encoding="utf-8")

        # Special cases: reference files, specifications, and documentation rules
        is_reference = file_path.name == "rules.mdc"
        is_spec = "meta/" in str(file_path)
        is_docs_rule = "docs/" in str(file_path)
        is_large_reference = "ui/cv2.mdc" in str(file_path)  # Large reference file

        # Check extension
        if file_path.suffix != ".mdc":
            errors.append(f"{file_path}: Rule must use .mdc extension")

        # Check frontmatter
        frontmatter_errors, frontmatter = self._check_rule_frontmatter(
            file_path,
            content,
        )
        errors.extend(frontmatter_errors)
        if frontmatter is None:
            return errors  # Can't continue without valid frontmatter

        # Check description
        errors.extend(
            self._check_rule_description(file_path, frontmatter, is_spec, is_reference),
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
                self._check_rule_content(
                    file_path,
                    content,
                    frontmatter_match.end(),
                    is_spec,
                    is_reference,
                    is_docs_rule,
                ),
            )

        return errors

    def _validate_command(self, file_path: Path) -> list[str]:
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
        content = file_path.read_text(encoding="utf-8")

        # Check extension
        if file_path.suffix != ".md":
            errors.append(f"{file_path}: Command must use .md extension")

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
            errors.append(f"{file_path}: Steps should be numbered (1., 2., etc.)")

        # Check checklist format
        if not re.search(r"- \[ \]", content):
            errors.append(f"{file_path}: Checklist should use - [ ] format")

        return errors

    def validate(
        self,
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
        """Validate all Cursor rules and commands.

        This command validates that all rules and commands follow the Tux project
        standards for structure, content, and metadata.

        Parameters
        ----------
        rules_dir : Path
            Directory containing rule files (default: .cursor/rules).
        commands_dir : Path
            Directory containing command files (default: .cursor/commands).

        Raises
        ------
        Exit
            If validation fails.
        """
        self.console.print(
            Panel.fit("Cursor Rules & Commands Validator", style="bold blue"),
        )

        if not rules_dir.exists():
            self.console.print(
                f"Error: {rules_dir} does not exist",
                style="red",
            )
            raise typer.Exit(code=1)

        if not commands_dir.exists():
            self.console.print(
                f"Error: {commands_dir} does not exist",
                style="red",
            )
            raise typer.Exit(code=1)

        all_errors: list[str] = []

        # Validate rules
        rule_files = sorted(rules_dir.rglob("*.mdc"))
        self.console.print(f"\n[bold]Validating {len(rule_files)} rule files...[/bold]")
        for rule_file in rule_files:
            errors = self._validate_rule(rule_file)
            all_errors.extend(errors)
            if errors:
                for error in errors:
                    self.console.print(f"  [red]✗[/red] {error}")

        # Validate commands
        cmd_files = sorted(commands_dir.rglob("*.md"))
        self.console.print(
            f"\n[bold]Validating {len(cmd_files)} command files...[/bold]",
        )
        for cmd_file in cmd_files:
            errors = self._validate_command(cmd_file)
            all_errors.extend(errors)
            if errors:
                for error in errors:
                    self.console.print(f"  [red]✗[/red] {error}")

        # Report results
        self._print_validation_summary(
            rule_files,
            cmd_files,
            all_errors,
        )

        if all_errors:
            raise typer.Exit(code=1)

    def _print_validation_summary(
        self,
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
            self.console.print("\n")
            self.console.print(table)
            self.console.print(
                f"\n[bold red]Validation failed with {len(all_errors)} error(s)[/bold red]",
            )
        else:
            table.add_row("Status", "✓ All valid", style="bold green")
            self.console.print("\n")
            self.console.print(table)
            self.console.print(
                "\n[bold green]✓ All rules and commands are valid![/bold green]",
            )


# Create the CLI app instance
app = CursorCLI().app


def main() -> None:
    """Entry point for the cursor CLI script."""
    cli = CursorCLI()
    cli.run()


if __name__ == "__main__":
    main()
