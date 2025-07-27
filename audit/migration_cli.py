#!/usr/bin/env python3
"""CLI tool for migrating cogs to use dependency injection."""

import argparse
import sys
from pathlib import Path

from loguru import logger

from tux.core.migration import CogMigrationTool


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Tux Cog Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migration_cli.py scan tux/cogs
  python migration_cli.py analyze tux/cogs/admin/dev.py
  python migration_cli.py report tux/cogs --output migration_report.md
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan directory for migration candidates")
    scan_parser.add_argument("directory", type=Path, help="Directory to scan")
    scan_parser.add_argument("--output", "-o", type=Path, help="Output file for results")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a specific file")
    analyze_parser.add_argument("file", type=Path, help="File to analyze")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate migration report")
    report_parser.add_argument("directory", type=Path, help="Directory to scan")
    report_parser.add_argument("--output", "-o", type=Path, help="Output file for report")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tool = CogMigrationTool()

    try:
        if args.command == "scan":
            handle_scan_command(tool, args)
        elif args.command == "analyze":
            handle_analyze_command(tool, args)
        elif args.command == "report":
            handle_report_command(tool, args)
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


def handle_scan_command(tool: CogMigrationTool, args: argparse.Namespace) -> None:
    """Handle the scan command."""
    logger.info(f"Scanning directory: {args.directory}")

    results = tool.scan_cogs_directory(args.directory)

    print(f"Scan Results for {args.directory}")
    print("=" * 50)
    print(f"Total files: {results['total_files']}")
    print(f"Analyzed files: {results['analyzed_files']}")
    print(f"Migration candidates: {len(results['migration_candidates'])}")

    if results["errors"]:
        print(f"Errors: {len(results['errors'])}")

    print("\nMigration Candidates by Complexity:")
    complexity_counts = {"low": 0, "medium": 0, "high": 0}

    for candidate in results["migration_candidates"]:
        complexity = candidate["plan"]["estimated_effort"]
        complexity_counts[complexity] += 1

    for complexity, count in complexity_counts.items():
        if count > 0:
            print(f"  {complexity.title()}: {count} files")

    if args.output:
        import json

        with args.output.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {args.output}")


def handle_analyze_command(tool: CogMigrationTool, args: argparse.Namespace) -> None:
    """Handle the analyze command."""
    logger.info(f"Analyzing file: {args.file}")

    analysis = tool.analyze_cog_file(args.file)

    if "error" in analysis:
        print(f"Error analyzing file: {analysis['error']}")
        return

    print(f"Analysis Results for {args.file}")
    print("=" * 50)
    print(f"Has __init__ method: {analysis['has_init_method']}")
    print(f"Uses DatabaseController: {analysis['uses_database_controller']}")
    print(f"Service instantiations: {len(analysis['service_instantiations'])}")
    print(f"Migration complexity: {analysis['migration_complexity']}")

    if analysis["service_instantiations"]:
        print("\nService Instantiations:")
        for service in analysis["service_instantiations"]:
            print(f"  - {service['attribute']}: {service['service']}")

    if analysis["imports_to_update"]:
        print("\nImports to Update:")
        for import_name in analysis["imports_to_update"]:
            print(f"  - {import_name}")

    # Generate and display migration plan
    plan = tool.generate_migration_plan(analysis)
    print(f"\nMigration Plan (Estimated effort: {plan['estimated_effort']}):")
    for step in plan["steps"]:
        print(f"\nStep {step['step']}: {step['description']}")
        for change in step["changes"]:
            print(f"  - {change}")


def handle_report_command(tool: CogMigrationTool, args: argparse.Namespace) -> None:
    """Handle the report command."""
    logger.info(f"Generating report for directory: {args.directory}")

    results = tool.scan_cogs_directory(args.directory)
    report = tool.create_migration_report(results)

    if args.output:
        with args.output.open("w", encoding="utf-8") as f:
            f.write(report)
        print(f"Migration report saved to: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
