#!/usr/bin/env python3
"""
Branch creation script for splitting misc/kaizen commit into focused branches.
Takes the branch_groups.json and creates separate branches for each group.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class BranchCreator:
    """Creates focused branches from grouped file changes."""

    def __init__(self, groups_file: str = "branch_groups.json"):
        self.groups_file = groups_file
        self.original_branch = "misc/kaizen"
        self.base_branch = "main"  # Assuming main is the base branch
        self.backup_branch = f"{self.original_branch}-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def load_groups(self) -> dict[str, list[str]]:
        """Load the file groups from JSON."""
        try:
            with open(self.groups_file) as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Error: {self.groups_file} not found. Run the analysis script first.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in {self.groups_file}: {e}")
            sys.exit(1)

    def run_git_command(self, cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command and return the result."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Git command failed: {' '.join(cmd)}")
            print(f"Error: {e.stderr}")
            if check:
                sys.exit(1)
            return e

    def verify_git_state(self) -> None:
        """Verify we're in the right git state to proceed."""
        # Check if we're in a git repository
        result = self.run_git_command(["git", "rev-parse", "--git-dir"], check=False)
        if result.returncode != 0:
            print("❌ Error: Not in a git repository")
            sys.exit(1)

        # Check if we're on the misc/kaizen branch
        result = self.run_git_command(["git", "branch", "--show-current"])
        current_branch = result.stdout.strip()
        if current_branch != self.original_branch:
            print(f"❌ Error: Not on {self.original_branch} branch (currently on {current_branch})")
            print(f"Please run: git checkout {self.original_branch}")
            sys.exit(1)

        # Check if working directory has staged or modified files (ignore untracked)
        result = self.run_git_command(["git", "status", "--porcelain"])
        dirty_files = [line for line in result.stdout.strip().split("\n") if line.strip() and not line.startswith("??")]
        if dirty_files:
            print("❌ Error: Working directory has staged or modified files")
            print("Please commit or stash your changes before proceeding")
            for line in dirty_files:
                print(f"  {line}")
            sys.exit(1)

        print("✅ Git state verified - ready to proceed")

    def create_backup(self) -> None:
        """Create a backup of the original branch."""
        print(f"📦 Creating backup branch: {self.backup_branch}")
        self.run_git_command(["git", "branch", self.backup_branch])
        print(f"✅ Backup created: {self.backup_branch}")

    def reset_to_base(self) -> None:
        """Reset the current branch to before the large commit, keeping changes staged."""
        print(f"🔄 Resetting {self.original_branch} to before the large commit (keeping changes)")

        # Reset to the commit before HEAD, but keep changes in working directory
        self.run_git_command(["git", "reset", "HEAD~1"])

        print("✅ Reset complete - all changes are now unstaged")

    def create_group_branch(self, group_name: str, files: list[str]) -> str:
        """Create a branch for a specific group of files."""
        branch_name = f"{group_name}-split"

        print(f"\n🌿 Creating branch: {branch_name}")
        print(f"   Files ({len(files)}): {', '.join(files[:3])}{'...' if len(files) > 3 else ''}")

        # Create and checkout the new branch
        self.run_git_command(["git", "checkout", "-b", branch_name])

        # Add only the files for this group
        for file in files:
            if Path(file).exists():
                self.run_git_command(["git", "add", file])
                print(f"   ✓ Added {file}")
            else:
                print(f"   ⚠️  Warning: {file} not found in working directory")

        # Create a focused commit
        commit_message = self._generate_commit_message(group_name, files)
        self.run_git_command(["git", "commit", "-m", commit_message])

        print(f"✅ Branch {branch_name} created with {len(files)} files")

        # Return to the original branch for the next group
        self.run_git_command(["git", "checkout", self.original_branch])

        return branch_name

    def _generate_commit_message(self, group_name: str, files: list[str]) -> str:
        """Generate a descriptive commit message for a group."""
        # Map group names to descriptive commit messages
        commit_messages = {
            "01-core-foundation": "feat: implement core bot infrastructure and monitoring system\n\n"
            "- Add comprehensive task management system\n"
            "- Implement distributed tracing and monitoring\n"
            "- Refactor bot core with new sentry integration\n"
            "- Update database controllers with tracing support\n"
            "- Rename emoji.py to emoji_manager.py",
            "02-error-handling": "refactor: modernize error handling and sentry integration\n\n"
            "- Replace old sentry.py with new sentry_manager.py\n"
            "- Update error handlers with improved context\n"
            "- Streamline sentry error reporting",
            "03-services": "feat: enhance service cogs with improved functionality\n\n"
            "- Add new reminders service\n"
            "- Update levels service integration\n"
            "- Improve influxdb logging capabilities\n"
            "- Enhance gif limiter and status roles",
            "04-other-cogs": "feat: update moderation, tools, and utility cogs\n\n"
            "- Improve tempban functionality\n"
            "- Update wolfram integration\n"
            "- Enhance AFK and reminder utilities",
            "05-dependencies-and-cli": "chore: update dependencies and CLI tools\n\n"
            "- Update poetry.lock and pyproject.toml\n"
            "- Enhance CLI test functionality",
        }

        return commit_messages.get(group_name, f"feat: implement {group_name} changes")

    def verify_completeness(self, created_branches: list[str]) -> None:
        """Verify that all changes are preserved across the created branches."""
        print(f"\n🔍 Verifying completeness across {len(created_branches)} branches...")

        # Get the original commit's file list
        result = self.run_git_command(["git", "show", "--name-only", "--pretty=format:", self.backup_branch])
        original_files = set()
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line and (line.endswith(".py") or line.endswith(".lock") or line.endswith(".toml")):
                original_files.add(line)

        # Get files from all created branches
        branch_files = set()
        for branch in created_branches:
            result = self.run_git_command(["git", "show", "--name-only", "--pretty=format:", branch])
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line and (line.endswith(".py") or line.endswith(".lock") or line.endswith(".toml")):
                    branch_files.add(line)

        missing_files = original_files - branch_files
        extra_files = branch_files - original_files

        if missing_files:
            print(f"❌ Missing files ({len(missing_files)}):")
            for file in sorted(missing_files):
                print(f"   - {file}")

        if extra_files:
            print(f"⚠️  Extra files ({len(extra_files)}):")
            for file in sorted(extra_files):
                print(f"   + {file}")

        if not missing_files and not extra_files:
            print(f"✅ Perfect! All {len(original_files)} files are preserved across branches")

        return len(missing_files) == 0 and len(extra_files) == 0

    def generate_summary(self, created_branches: list[str]) -> None:
        """Generate a summary of created branches and next steps."""
        print("\n" + "=" * 80)
        print("🎉 BRANCH SPLITTING COMPLETE!")
        print("=" * 80)

        print(f"\n📋 CREATED BRANCHES ({len(created_branches)}):")
        for i, branch in enumerate(created_branches, 1):
            # Get commit info for each branch
            result = self.run_git_command(["git", "log", "-1", "--oneline", branch])
            commit_info = result.stdout.strip()
            print(f"  {i}. {branch}")
            print(f"     {commit_info}")

        print("\n💾 BACKUP BRANCH:")
        print(f"  📦 {self.backup_branch} (original misc/kaizen)")

        print("\n🚀 NEXT STEPS:")
        print("  1. Push branches to remote:")
        for branch in created_branches:
            print(f"     git push origin {branch}")

        print("\n  2. Create Pull Requests in this order:")
        for i, branch in enumerate(created_branches, 1):
            print(f"     {i}. {branch} → main")

        print("\n  3. Merge order (to handle dependencies):")
        print("     - Merge 01-core-foundation first (contains all dependencies)")
        print("     - Then merge 02-error-handling")
        print("     - Finally merge 03-services, 04-other-cogs, 05-dependencies-and-cli")

        print("\n📝 BRANCH DESCRIPTIONS:")
        descriptions = {
            "01-core-foundation-split": "Core bot infrastructure, monitoring system, and database controllers",
            "02-error-handling-split": "Error handling and sentry integration refactor",
            "03-services-split": "Service cogs enhancements and new reminders service",
            "04-other-cogs-split": "Moderation, tools, and utility cogs updates",
            "05-dependencies-and-cli-split": "Dependency updates and CLI improvements",
        }

        for branch in created_branches:
            desc = descriptions.get(branch, "Feature updates")
            print(f"  • {branch}: {desc}")

    def run(self) -> None:
        """Main execution method."""
        print("🚀 Starting branch splitting process...")

        # Load groups and verify state
        groups = self.load_groups()
        self.verify_git_state()

        print("\n📊 SPLITTING PLAN:")
        total_files = 0
        for group_name, files in groups.items():
            print(f"  📁 {group_name}: {len(files)} files")
            total_files += len(files)
        print(f"  📈 Total: {total_files} files across {len(groups)} branches")

        # Confirm before proceeding
        response = input(f"\n❓ Proceed with splitting {self.original_branch}? (y/N): ").strip().lower()
        if response != "y":
            print("❌ Aborted by user")
            sys.exit(0)

        # Execute the splitting process
        self.create_backup()
        self.reset_to_base()

        created_branches = []
        for group_name, files in groups.items():
            branch_name = self.create_group_branch(group_name, files)
            created_branches.append(branch_name)

        # Verify and summarize
        completeness_ok = self.verify_completeness(created_branches)
        self.generate_summary(created_branches)

        if not completeness_ok:
            print("\n⚠️  WARNING: Some files may be missing. Please review before pushing.")
        else:
            print("\n✅ All files accounted for - safe to push branches!")


def main():
    """Main entry point."""
    creator = BranchCreator()
    creator.run()


if __name__ == "__main__":
    main()
