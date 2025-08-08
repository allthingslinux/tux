#!/usr/bin/env python3
"""
Dependency Injection Validation Script

This script validates the completeness of the dependency injection system migration
and measures success metrics for the Tux Discord bot codebase.

Usage:
    python scripts/validate_dependency_injection.py [--format json|table|summary]
    python scripts/validate_dependency_injection.py --export results.json
"""

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ValidationResult:
    """Results of dependency injection validation."""

    total_cogs: int
    base_cog_inheritance: int
    direct_instantiations: int
    migration_completeness: float
    performance_impact: float | None = None
    boilerplate_reduction: float | None = None
    errors: list[str] | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class DependencyInjectionValidator:
    """Validates dependency injection implementation completeness."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.cogs_dir = self.project_root / "tux" / "cogs"
        self.modules_dir = self.project_root / "tux" / "modules"
        self.core_dir = self.project_root / "tux" / "core"

    def validate_migration_completeness(self) -> ValidationResult:
        """Validate the completeness of dependency injection migration."""
        results = ValidationResult(
            total_cogs=0,
            base_cog_inheritance=0,
            direct_instantiations=0,
            migration_completeness=0.0,
        )

        # Find all cog files
        cog_files = self._find_cog_files()
        results.total_cogs = len(cog_files)

        # Check BaseCog inheritance
        base_cog_inheritance = self._check_base_cog_inheritance(cog_files)
        results.base_cog_inheritance = len(base_cog_inheritance)

        # Check for direct DatabaseController instantiations
        direct_instantiations = self._check_direct_instantiations(cog_files)
        results.direct_instantiations = len(direct_instantiations)

        # Calculate migration completeness
        if results.total_cogs > 0:
            results.migration_completeness = (results.base_cog_inheritance / results.total_cogs) * 100

        # Add errors for any issues found
        if direct_instantiations and results.errors is not None:
            results.errors.append(f"Found {len(direct_instantiations)} direct DatabaseController instantiations")

        missing_base_cog = results.total_cogs - results.base_cog_inheritance
        if missing_base_cog > 0 and results.errors is not None:
            results.errors.append(f"Found {missing_base_cog} cogs not inheriting from BaseCog")

        return results

    def _find_cog_files(self) -> list[Path]:
        """Find all Python files that define cog classes."""
        cog_files: list[Path] = []

        search_dirs = []
        if self.cogs_dir.exists():
            search_dirs.append(self.cogs_dir)
        if hasattr(self, "modules_dir") and self.modules_dir.exists():
            search_dirs.append(self.modules_dir)

        for directory in search_dirs:
            for py_file in directory.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue

                try:
                    with open(py_file, encoding="utf-8") as f:
                        content = f.read()

                    # Check if file contains cog class definitions
                    if any(
                        keyword in content
                        for keyword in ["class", "commands.Cog", "BaseCog", "ModerationCogBase", "SnippetsBaseCog"]
                    ):
                        cog_files.append(py_file)

                except Exception as e:
                    print(f"Error reading {py_file}: {e}")

        return cog_files

    def _check_base_cog_inheritance(self, cog_files: list[Path]) -> list[Path]:
        """Check which cog files inherit from BaseCog or related base classes."""
        base_cog_files = []

        for cog_file in cog_files:
            try:
                with open(cog_file, encoding="utf-8") as f:
                    content = f.read()

                # Parse the file to find class definitions
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if class inherits from BaseCog or related classes
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                if base.id in ["BaseCog", "ModerationCogBase", "SnippetsBaseCog"]:
                                    base_cog_files.append(cog_file)
                                    break
                            elif isinstance(base, ast.Attribute):
                                if base.attr in ["BaseCog", "ModerationCogBase", "SnippetsBaseCog"]:
                                    base_cog_files.append(cog_file)
                                    break

            except Exception as e:
                print(f"Error parsing {cog_file}: {e}")

        return base_cog_files

    def _check_direct_instantiations(self, cog_files: list[Path]) -> list[tuple[Path, int, int]]:
        """Check for direct DatabaseController instantiations in cog files."""
        direct_instantiations = []

        for cog_file in cog_files:
            try:
                with open(cog_file, encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                # Check for DatabaseController() patterns
                for line_num, line in enumerate(lines, 1):
                    if "DatabaseController()" in line:
                        direct_instantiations.append((cog_file, line_num, len(line)))

            except Exception as e:
                print(f"Error checking {cog_file}: {e}")

        return direct_instantiations

    def measure_performance_impact(self) -> float | None:
        """Measure performance impact of dependency injection system."""
        # This would require actual performance testing
        # For now, return None to indicate not measured
        return None

    def measure_boilerplate_reduction(self) -> float | None:
        """Measure boilerplate code reduction."""
        # Count lines of boilerplate code before and after
        # This is a simplified measurement
        return None


def format_results_table(results: ValidationResult) -> str:
    """Format validation results as a table."""
    table = []
    table.append("=" * 60)
    table.append("DEPENDENCY INJECTION MIGRATION VALIDATION")
    table.append("=" * 60)
    table.append(f"Total Cogs Analyzed: {results.total_cogs}")
    table.append(f"BaseCog Inheritance: {results.base_cog_inheritance}")
    table.append(f"Migration Completeness: {results.migration_completeness:.1f}%")
    table.append(f"Direct Instantiations: {results.direct_instantiations}")

    if results.errors:
        table.append("\nISSUES FOUND:")
        for error in results.errors:
            table.append(f"  ❌ {error}")
    else:
        table.append("\n✅ All validation checks passed!")

    table.append("=" * 60)
    return "\n".join(table)


def format_results_summary(results: ValidationResult) -> str:
    """Format validation results as a summary."""
    summary = []
    summary.append("Dependency Injection Migration Summary")
    summary.append("-" * 40)

    if results.migration_completeness >= 95:
        status = "✅ EXCELLENT"
    elif results.migration_completeness >= 80:
        status = "✅ GOOD"
    elif results.migration_completeness >= 60:
        status = "⚠️  NEEDS WORK"
    else:
        status = "❌ POOR"

    summary.append(f"Migration Status: {status}")
    summary.append(f"Completeness: {results.migration_completeness:.1f}%")
    summary.append(f"BaseCog Usage: {results.base_cog_inheritance}/{results.total_cogs}")

    if results.direct_instantiations > 0:
        summary.append(f"Remaining Issues: {results.direct_instantiations} direct instantiations")

    return "\n".join(summary)


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate dependency injection migration completeness")
    parser.add_argument("--format", choices=["json", "table", "summary"], default="table", help="Output format")
    parser.add_argument("--export", type=str, help="Export results to JSON file")
    parser.add_argument("--project-root", type=str, default=".", help="Project root directory")
    parser.add_argument("--modules", action="store_true", help="Also scan tux/modules alongside tux/cogs")

    args = parser.parse_args()

    # Initialize validator
    validator = DependencyInjectionValidator(args.project_root)

    # Run validation
    print("Running dependency injection validation...")
    results = validator.validate_migration_completeness()

    # Format output
    if args.format == "json":
        output = json.dumps(asdict(results), indent=2)
    elif args.format == "summary":
        output = format_results_summary(results)
    else:  # table
        output = format_results_table(results)

    print(output)

    # Export if requested
    if args.export:
        with open(args.export, "w") as f:
            json.dump(asdict(results), f, indent=2)
        print(f"\nResults exported to {args.export}")

    # Exit with error code if issues found
    if results.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
