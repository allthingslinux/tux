#!/usr/bin/env python3
"""
Branch splitting analysis tool for misc/kaizen branch.
Analyzes file changes and dependencies to help split a large commit into focused PRs.
"""

import ast
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileChange:
    """Represents a changed file with its statistics."""

    path: str
    lines_added: int
    lines_removed: int
    change_type: str  # 'modified', 'added', 'deleted', 'renamed'


@dataclass
class FileDependency:
    """Represents a dependency relationship between files."""

    source_file: str
    target_file: str
    import_type: str  # 'import', 'from_import', 'relative_import'
    line_content: str


class BranchAnalyzer:
    """Analyzes a git branch for file changes and dependencies."""

    def __init__(self, branch_name: str = "misc/kaizen"):
        self.branch_name = branch_name
        self.changed_files: list[FileChange] = []
        self.dependencies: list[FileDependency] = []
        self.project_root = Path.cwd()

    def analyze_commit_changes(self) -> None:
        """Analyze the file changes in the latest commit."""
        print(f"🔍 Analyzing changes in {self.branch_name}...")

        # Get the diff stat for the latest commit
        result = subprocess.run(["git", "diff", "HEAD~1", "--stat"], capture_output=True, text=True, check=True)

        # Parse the diff stat output
        for line in result.stdout.strip().split("\n"):
            if "|" in line and ("+" in line or "-" in line):
                self._parse_diff_stat_line(line)

        print(f"📊 Found {len(self.changed_files)} changed files")

    def _parse_diff_stat_line(self, line: str) -> None:
        """Parse a single line from git diff --stat output."""
        # Example: " tux/bot.py | 845 ++++++++++++++++++++++++++++++---------------------------"
        parts = line.strip().split("|")
        if len(parts) != 2:
            return

        file_path = parts[0].strip()
        stats_part = parts[1].strip()

        # Count + and - characters
        lines_added = stats_part.count("+")
        lines_removed = stats_part.count("-")

        # Determine change type and extract filename
        change_type = "modified"
        if "=>" in file_path:
            change_type = "renamed"
            # Extract new filename from rename notation
            # Handle both "old => new" and "{old => new}" formats
            if "{" in file_path and "}" in file_path:
                # Format: "tux/utils/{emoji.py => emoji_manager.py}"
                base_path = file_path.split("{")[0]
                rename_part = file_path.split("{")[1].split("}")[0]
                new_name = rename_part.split(" => ")[1]
                file_path = base_path + new_name
            else:
                # Format: "old => new"
                file_path = re.sub(r".*=> (.+)", r"\1", file_path)

        # Debug: check emoji file processing
        if "emoji" in file_path:
            print(
                f"DEBUG: Processing emoji file: {file_path}, added={lines_added}, removed={lines_removed}, type={change_type}",
            )

        # Include renamed files even if they have 0 changes
        if lines_added > 0 or lines_removed > 0 or change_type == "renamed":
            self.changed_files.append(
                FileChange(
                    path=file_path,
                    lines_added=lines_added,
                    lines_removed=lines_removed,
                    change_type=change_type,
                ),
            )

    def analyze_dependencies(self) -> None:
        """Analyze import dependencies between changed files."""
        print("🔗 Analyzing dependencies between changed files...")

        changed_file_paths = {f.path for f in self.changed_files}

        for file_change in self.changed_files:
            if file_change.path.endswith(".py"):
                self._analyze_python_file_dependencies(file_change.path, changed_file_paths)

        print(f"🔗 Found {len(self.dependencies)} dependencies between changed files")

    def _analyze_python_file_dependencies(self, file_path: str, changed_files: set[str]) -> None:
        """Analyze Python import dependencies for a single file."""
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return

            with open(full_path, encoding="utf-8") as f:
                content = f.read()

            # Parse the AST to find imports
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self._check_import_dependency(file_path, alias.name, "import", changed_files)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self._check_import_dependency(file_path, node.module, "from_import", changed_files)
            except SyntaxError:
                # If AST parsing fails, fall back to regex
                self._analyze_imports_with_regex(file_path, content, changed_files)

        except Exception as e:
            print(f"⚠️  Warning: Could not analyze {file_path}: {e}")

    def _analyze_imports_with_regex(self, file_path: str, content: str, changed_files: set[str]) -> None:
        """Fallback regex-based import analysis."""
        import_patterns = [
            r"^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)",
            r"^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import",
        ]

        for line in content.split("\n"):
            line = line.strip()
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    module_name = match.group(1)
                    self._check_import_dependency(file_path, module_name, "regex_import", changed_files)

    def _check_import_dependency(
        self,
        source_file: str,
        module_name: str,
        import_type: str,
        changed_files: set[str],
    ) -> None:
        """Check if an import creates a dependency on another changed file."""
        # Convert module name to potential file paths
        potential_paths = [
            f"{module_name.replace('.', '/')}.py",
            f"{module_name.replace('.', '/')}/__init__.py",
        ]

        # Check for relative imports within the tux package
        if module_name.startswith("tux."):
            potential_paths.extend(
                [
                    f"{module_name.replace('.', '/')}.py",
                    f"{module_name.replace('.', '/')}/__init__.py",
                ],
            )

        for potential_path in potential_paths:
            if potential_path in changed_files:
                self.dependencies.append(
                    FileDependency(
                        source_file=source_file,
                        target_file=potential_path,
                        import_type=import_type,
                        line_content=f"{import_type}: {module_name}",
                    ),
                )

    def suggest_groupings(self) -> dict[str, list[str]]:
        """Suggest logical groupings based on file paths and dependencies."""
        groups = defaultdict(list)

        for file_change in self.changed_files:
            path = file_change.path

            # Group by directory structure and file type
            if path in ["poetry.lock", "pyproject.toml"]:
                groups["dependencies"].append(path)
            elif path.startswith("tux/cli/"):
                groups["cli-tools"].append(path)
            elif path.startswith("tux/cogs/services/"):
                groups["services"].append(path)
            elif path.startswith("tux/cogs/moderation/"):
                groups["moderation"].append(path)
            elif path.startswith("tux/cogs/tools/"):
                groups["tools"].append(path)
            elif path.startswith("tux/cogs/utility/"):
                groups["utility"].append(path)
            elif path.startswith("tux/database/"):
                groups["database"].append(path)
            elif path.startswith("tux/handlers/"):
                groups["handlers"].append(path)
            elif path.startswith("tux/utils/"):
                if "sentry" in path or "task_manager" in path or "tracing" in path:
                    groups["monitoring-system"].append(path)
                else:
                    groups["utils"].append(path)
            elif path in ["tux/app.py", "tux/bot.py", "tux/cog_loader.py"]:
                groups["core-infrastructure"].append(path)
            else:
                groups["other"].append(path)

        return dict(groups)

    def analyze_dependency_conflicts(self, groups: dict[str, list[str]]) -> list[str]:
        """Analyze potential conflicts when files are split into different groups."""
        conflicts = []

        # Create a mapping of file to group
        file_to_group = {}
        for group_name, files in groups.items():
            for file_path in files:
                file_to_group[file_path] = group_name

        # Check for cross-group dependencies
        for dep in self.dependencies:
            source_group = file_to_group.get(dep.source_file)
            target_group = file_to_group.get(dep.target_file)

            if source_group and target_group and source_group != target_group:
                conflicts.append(
                    f"⚠️  DEPENDENCY CONFLICT: {dep.source_file} ({source_group}) "
                    f"depends on {dep.target_file} ({target_group})",
                )

        return conflicts

    def display_analysis(self) -> None:
        """Display the complete analysis results."""
        print("\n" + "=" * 80)
        print("📋 BRANCH SPLITTING ANALYSIS REPORT")
        print("=" * 80)

        # Show file changes by size
        print(f"\n📊 FILE CHANGES (Total: {len(self.changed_files)})")
        print("-" * 50)

        # Sort by total changes (additions + deletions)
        sorted_files = sorted(self.changed_files, key=lambda f: f.lines_added + f.lines_removed, reverse=True)

        for file_change in sorted_files:
            total_changes = file_change.lines_added + file_change.lines_removed
            print(
                f"  {file_change.path:<40} +{file_change.lines_added:<4} -{file_change.lines_removed:<4} ({total_changes} total)",
            )

        # Show suggested groupings
        groups = self.suggest_groupings()
        print(f"\n🎯 SUGGESTED GROUPINGS ({len(groups)} groups)")
        print("-" * 50)

        for group_name, files in groups.items():
            total_changes = sum(f.lines_added + f.lines_removed for f in self.changed_files if f.path in files)
            print(f"\n  📁 {group_name.upper()} ({len(files)} files, {total_changes} total changes)")
            for file_path in sorted(files):
                file_change = next(f for f in self.changed_files if f.path == file_path)
                changes = file_change.lines_added + file_change.lines_removed
                print(f"     • {file_path} ({changes} changes)")

        # Show dependency analysis
        if self.dependencies:
            print(f"\n🔗 DEPENDENCIES BETWEEN CHANGED FILES ({len(self.dependencies)})")
            print("-" * 50)

            # Group dependencies by source file
            deps_by_source = defaultdict(list)
            for dep in self.dependencies:
                deps_by_source[dep.source_file].append(dep)

            for source_file, deps in sorted(deps_by_source.items()):
                print(f"\n  📄 {source_file}")
                for dep in deps:
                    print(f"     → {dep.target_file} ({dep.import_type})")

        # Show potential conflicts
        conflicts = self.analyze_dependency_conflicts(groups)
        if conflicts:
            print(f"\n⚠️  POTENTIAL CONFLICTS ({len(conflicts)})")
            print("-" * 50)
            for conflict in conflicts:
                print(f"  {conflict}")

            print("\n💡 RECOMMENDATIONS:")
            print("   • Consider keeping dependent files in the same group")
            print("   • Or plan merge order: merge dependency branches first")
            print("   • Or duplicate shared changes across dependent branches")
        else:
            print("\n✅ NO DEPENDENCY CONFLICTS DETECTED")
            print("   Files can be safely split into the suggested groups")

    def interactive_grouping(self) -> dict[str, list[str]]:
        """Interactive interface for grouping files with dependency awareness."""
        print("\n" + "=" * 80)
        print("🎯 INTERACTIVE FILE GROUPING")
        print("=" * 80)

        # Show strategy options
        print("\nChoose your splitting strategy:")
        print("1. 📦 Dependency-First (Recommended) - Group by dependency order")
        print("2. 🎨 Feature-Based - Keep original suggested groups")
        print("3. 🔧 Custom - Create your own groups")

        while True:
            choice = input("\nEnter your choice (1-3): ").strip()
            if choice in ["1", "2", "3"]:
                break
            print("Please enter 1, 2, or 3")

        if choice == "1":
            return self._dependency_first_grouping()
        if choice == "2":
            return self._feature_based_grouping()
        return self._custom_grouping()

    def _dependency_first_grouping(self) -> dict[str, list[str]]:
        """Create dependency-first groupings to minimize conflicts."""
        print("\n📦 Creating dependency-first groupings...")

        # More aggressive grouping - put ALL core dependencies together to eliminate conflicts
        groups = {
            "01-core-foundation": [
                # Core bot infrastructure
                "tux/bot.py",
                "tux/app.py",
                "tux/cog_loader.py",
                # New monitoring system (heavily imported by core)
                "tux/utils/task_manager.py",
                "tux/utils/sentry_manager.py",
                "tux/utils/tracing.py",
                "tux/utils/context_utils.py",
                "tux/utils/protocols.py",
                "tux/utils/banner.py",
                # Database controllers (imported by bot.py and many cogs)
                "tux/database/controllers/__init__.py",
                "tux/database/controllers/base.py",
                "tux/database/controllers/levels.py",
                # Hot reload (depends on tracing)
                "tux/utils/hot_reload.py",
            ],
            "02-error-handling": ["tux/handlers/error.py", "tux/handlers/sentry.py", "tux/utils/sentry.py"],
            "03-services": [
                "tux/cogs/services/gif_limiter.py",
                "tux/cogs/services/influxdblogger.py",
                "tux/cogs/services/levels.py",
                "tux/cogs/services/reminders.py",
                "tux/cogs/services/status_roles.py",
            ],
            "04-other-cogs": [
                "tux/cogs/moderation/tempban.py",
                "tux/cogs/tools/wolfram.py",
                "tux/cogs/utility/afk.py",
                "tux/cogs/utility/remindme.py",
            ],
            "05-dependencies-and-cli": ["poetry.lock", "pyproject.toml", "tux/cli/test.py"],
        }

        # Filter out files that don't exist in our changed files
        changed_paths = {f.path for f in self.changed_files}
        filtered_groups = {}

        for group_name, files in groups.items():
            filtered_files = [f for f in files if f in changed_paths]
            if filtered_files:
                filtered_groups[group_name] = filtered_files

        self._display_proposed_groups(filtered_groups)
        return filtered_groups

    def _feature_based_grouping(self) -> dict[str, list[str]]:
        """Use the original suggested groupings with conflict warnings."""
        print("\n🎨 Using feature-based groupings (with dependency conflicts)...")

        groups = self.suggest_groupings()
        conflicts = self.analyze_dependency_conflicts(groups)

        print(f"\n⚠️  This approach has {len(conflicts)} dependency conflicts.")
        print("You'll need to merge branches in a specific order or duplicate changes.")

        proceed = input("\nProceed with feature-based grouping? (y/n): ").strip().lower()
        if proceed != "y":
            return self.interactive_grouping()

        self._display_proposed_groups(groups)
        return groups

    def _custom_grouping(self) -> dict[str, list[str]]:
        """Allow user to create custom groups."""
        print("\n🔧 Creating custom groups...")
        print("You can create groups and assign files to them.")

        groups = {}
        remaining_files = [f.path for f in self.changed_files]

        while remaining_files:
            print(f"\n📋 Remaining files ({len(remaining_files)}):")
            for i, file_path in enumerate(remaining_files, 1):
                print(f"  {i:2d}. {file_path}")

            # Create or select group
            print(f"\nCurrent groups: {list(groups.keys()) if groups else 'None'}")
            group_name = input("Enter group name (or 'list' to see files again): ").strip()

            if group_name == "list":
                continue
            if not group_name:
                continue

            if group_name not in groups:
                groups[group_name] = []

            # Select files for this group
            print(f"\nSelect files for group '{group_name}' (comma-separated numbers or 'all'):")
            selection = input("File numbers: ").strip()

            if selection.lower() == "all":
                groups[group_name].extend(remaining_files)
                remaining_files = []
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(",")]
                    selected_files = [remaining_files[i] for i in indices if 0 <= i < len(remaining_files)]
                    groups[group_name].extend(selected_files)
                    remaining_files = [f for f in remaining_files if f not in selected_files]
                except (ValueError, IndexError):
                    print("Invalid selection. Please use comma-separated numbers.")

        self._display_proposed_groups(groups)
        return groups

    def _display_proposed_groups(self, groups: dict[str, list[str]]) -> None:
        """Display the proposed groups with statistics."""
        print(f"\n📊 PROPOSED GROUPS ({len(groups)} groups)")
        print("-" * 50)

        for group_name, files in groups.items():
            total_changes = sum(f.lines_added + f.lines_removed for f in self.changed_files if f.path in files)
            print(f"\n  📁 {group_name.upper()} ({len(files)} files, {total_changes} changes)")
            for file_path in sorted(files):
                file_change = next((f for f in self.changed_files if f.path == file_path), None)
                if file_change:
                    changes = file_change.lines_added + file_change.lines_removed
                    print(f"     • {file_path} ({changes} changes)")

        # Check for conflicts in the proposed grouping
        conflicts = self.analyze_dependency_conflicts(groups)
        if conflicts:
            print(f"\n⚠️  DEPENDENCY CONFLICTS ({len(conflicts)})")
            print("-" * 50)
            for conflict in conflicts[:10]:  # Show first 10 conflicts
                print(f"  {conflict}")
            if len(conflicts) > 10:
                print(f"  ... and {len(conflicts) - 10} more conflicts")
        else:
            print("\n✅ NO DEPENDENCY CONFLICTS!")


def main():
    """Main entry point for the branch analysis tool."""
    analyzer = BranchAnalyzer()

    try:
        analyzer.analyze_commit_changes()
        analyzer.analyze_dependencies()
        analyzer.display_analysis()

        # Interactive grouping
        final_groups = analyzer.interactive_grouping()

        print("\n🎉 Grouping complete! Next step: create branches from these groups.")

        # Save the grouping for the next step
        import json

        with open("branch_groups.json", "w") as f:
            json.dump(final_groups, f, indent=2)
        print("💾 Groups saved to 'branch_groups.json'")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git command failed: {e}")
        print("Make sure you're in a git repository and on the misc/kaizen branch")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")


if __name__ == "__main__":
    main()
