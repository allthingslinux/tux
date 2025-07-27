"""Migration utilities for converting cogs to use dependency injection."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from loguru import logger


class CogMigrationTool:
    """Tool to help migrate existing cogs to use dependency injection."""

    def __init__(self) -> None:
        self.patterns = {
            "old_init": re.compile(r"def __init__\(self, bot: Tux\) -> None:"),
            "bot_assignment": re.compile(r"self\.bot = bot"),
            "db_instantiation": re.compile(r"self\.db = DatabaseController\(\)"),
            "service_instantiation": re.compile(r"self\.(\w+) = (\w+Service)\(\)"),
        }

    def analyze_cog_file(self, file_path: Path) -> dict[str, Any]:
"
        Analyze a cog file for migration opportunities.

        Parameters
        ----------
        file_path : Path
            Path to the cog file to analyze.

        Returns
        -------
        dict[str, Any]
            Analysis results.
        """
        if not file_path.exists():
            return {"error": "File not found"}

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            analysis = {
                "file_path": str(file_path),
                "has_init_method": False,
                "uses_database_controller": False,
                "service_instantiations": [],
                "imports_to_update": [],
                "migration_complexity": "low",
            }

            # Analyze AST
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                    analysis["has_init_method"] = True
                    self._analyze_init_method(node, analysis)

                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    self._analyze_imports(node, analysis)

            # Determine migration complexity
            analysis["migration_complexity"] = self._determine_complexity(analysis)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {"error": str(e)}

    def _analyze_init_method(self, init_node: ast.FunctionDef, analysis: dict[str, Any]) -> None:
        """Analyze the __init__ method for migration patterns."""
        for node in ast.walk(init_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                        if target.value.id == "self":
                            if target.attr == "db" and isinstance(node.value, ast.Call):
                                if isinstance(node.value.func, ast.Name) and node.value.func.id == "DatabaseController":
                                    analysis["uses_database_controller"] = True

                            # Check for service instantiations
                            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                                service_name = node.value.func.id
                                if service_name.endswith("Service"):
                                    analysis["service_instantiations"].append({
                                        "attribute": target.attr,
                                        "service": service_name,
                                    })

    def _analyze_imports(self, import_node: ast.Import | ast.ImportFrom, analysis: dict[str, Any]) -> None:
        """Analyze imports for potential updates."""
        if isinstance(import_node, ast.ImportFrom):
            if import_node.module == "tux.database.controllers":
                analysis["imports_to_update"].append("DatabaseController")

    def _determine_complexity(self, analysis: dict[str, Any]) -> str:
        """Determine migration complexity based on analysis."""
        complexity_score = 0

        if analysis["uses_database_controller"]:
            complexity_score += 1

        if len(analysis["service_instantiations"]) > 2:
            complexity_score += 2

        if len(analysis["imports_to_update"]) > 3:
            complexity_score += 1

        if complexity_score <= 1:
            return "low"
        elif complexity_score <= 3:
            return "medium"
        else:
            return "high"

    def generate_migration_plan(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a migration plan based on analysis.

        Parameters
        ----------
        analysis : dict[str, Any]
            The analysis results.

        Returns
        -------
        dict[str, Any]
            Migration plan.
        """
        plan = {
            "steps": [],
            "estimated_effort": analysis.get("migration_complexity", "unknown"),
            "backup_recommended": True,
        }

        # Step 1: Update imports
        if analysis.get("imports_to_update"):
            plan["steps"].append({
                "step": 1,
                "description": "Update imports to include DI interfaces",
                "changes": [
                    "Add: from tux.core.base_cog import BaseCog",
                    "Add: from tux.core.interfaces import IDatabaseService",
                ],
            })

        # Step 2: Update base class
        plan["steps"].append({
            "step": 2,
            "description": "Change base class to BaseCog",
            "changes": ["Replace commands.Cog with BaseCog"],
        })

        # Step 3: Update __init__ method
        if analysis.get("has_init_method"):
            changes = ["Remove direct service instantiations"]
            if analysis.get("uses_database_controller"):
                changes.append("Use self.db_service instead of self.db = DatabaseController()")

            plan["steps"].append({
                "step": 3,
                "description": "Update __init__ method",
                "changes": changes,
            })

        # Step 4: Update service usage
        if analysis.get("service_instantiations"):
            plan["steps"].append({
                "step": 4,
                "description": "Update service usage patterns",
                "changes": [
                    f"Update {service['attribute']} usage"
                    for service in analysis["service_instantiations"]
                ],
            })

        return plan

    def scan_cogs_directory(self, cogs_dir: Path) -> dict[str, Any]:
        """
        Scan the cogs directory for migration opportunities.

        Parameters
        ----------
        cogs_dir : Path
            Path to the cogs directory.

        Returns
        -------
        dict[str, Any]
            Scan results.
        """
        results = {
            "total_files": 0,
            "analyzed_files": 0,
            "migration_candidates": [],
            "errors": [],
        }

        if not cogs_dir.exists():
            results["errors"].append(f"Cogs directory not found: {cogs_dir}")
            return results

        # Find all Python files in cogs directory
        python_files = list(cogs_dir.rglob("*.py"))
        results["total_files"] = len(python_files)

        for file_path in python_files:
            if file_path.name.startswith("_"):
                continue  # Skip private files

            analysis = self.analyze_cog_file(file_path)
            if "error" not in analysis:
                results["analyzed_files"] += 1

                # Check if file is a migration candidate
                if (
                    analysis.get("has_init_method")
                    and (analysis.get("uses_database_controller") or analysis.get("service_instantiations"))
                ):
                    migration_plan = self.generate_migration_plan(analysis)
                    results["migration_candidates"].append({
                        "file": str(file_path),
                        "analysis": analysis,
                        "plan": migration_plan,
                    })
            else:
                results["errors"].append(f"{file_path}: {analysis['error']}")

        return results

    def create_migration_report(self, scan_results: dict[str, Any]) -> str:
        """
        Create a human-readable migration report.

        Parameters
        ----------
        scan_results : dict[str, Any]
            Results from scanning the cogs directory.

        Returns
        -------
        str
            Formatted migration report.
        """
        report = []
        report.append("# Cog Migration Report")
        report.append("")
        report.append(f"**Total files scanned:** {scan_results['total_files']}")
        report.append(f"**Files analyzed:** {scan_results['analyzed_files']}")
        report.append(f"**Migration candidates:** {len(scan_results['migration_candidates'])}")
        report.append("")

        if scan_results["errors"]:
            report.append("## Errors")
            for error in scan_results["errors"]:
                report.append(f"- {error}")
            report.append("")

        if scan_results["migration_candidates"]:
            report.append("## Migration Candidates")
            report.append("")

            # Group by complexity
            by_complexity = {"low": [], "medium": [], "high": []}
            for candidate in scan_results["migration_candidates"]:
                complexity = candidate["plan"]["estimated_effort"]
                by_complexity[complexity].append(candidate)

            for complexity in ["low", "medium", "high"]:
                candidates = by_complexity[complexity]
                if candidates:
                    report.append(f"### {complexity.title()} Complexity ({len(candidates)} files)")
                    for candidate in candidates:
                        file_path = Path(candidate["file"]).name
                        report.append(f"- **{file_path}**")
                        for step in candidate["plan"]["steps"]:
                            report.append(f"  - {step['description']}")
                    report.append("")

        return "\n".join(report)
