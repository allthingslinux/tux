#!/usr/bin/env python3
"""
Branch validation script for split branches.
Validates that each split branch can build and test independently.
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationResult:
    """Represents the validation result for a branch."""

    branch_name: str
    build_success: bool
    test_success: bool
    lint_success: bool
    error_messages: list[str]
    warnings: list[str]


class BranchValidator:
    """Validates split branches for independent functionality."""

    def __init__(self, groups_file: str = "branch_groups.json"):
        self.groups_file = groups_file
        self.original_branch = None
        self.validation_results: list[ValidationResult] = []

    def load_groups(self) -> dict[str, list[str]]:
        """Load the file groups from JSON."""
        try:
            with open(self.groups_file) as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Error: {self.groups_file} not found. Run the branch creation script first.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in {self.groups_file}: {e}")
            sys.exit(1)

    def run_command(self, cmd: list[str], cwd: Path | None = None, timeout: int = 300) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        try:
            return subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(cmd, 1, "", f"Command timed out after {timeout} seconds")
        except Exception as e:
            return subprocess.CompletedProcess(cmd, 1, "", str(e))

    def get_current_branch(self) -> str:
        """Get the current git branch."""
        result = self.run_command(["git", "branch", "--show-current"])
        if result.returncode == 0:
            return result.stdout.strip()
        return ""

    def checkout_branch(self, branch_name: str) -> bool:
        """Checkout a specific branch."""
        result = self.run_command(["git", "checkout", branch_name])
        return result.returncode == 0

    def validate_build(self, branch_name: str) -> tuple[bool, list[str]]:
        """Validate that the branch can build successfully."""
        print(f"  🔨 Testing build for {branch_name}...")
        errors = []

        # Check if pyproject.toml exists and try poetry install
        if Path("pyproject.toml").exists():
            result = self.run_command(["poetry", "install", "--no-dev"], timeout=180)
            if result.returncode != 0:
                errors.append(f"Poetry install failed: {result.stderr}")
                return False, errors

        # Try to import the main module
        result = self.run_command(["python", "-c", "import tux; print('Import successful')"])
        if result.returncode != 0:
            errors.append(f"Module import failed: {result.stderr}")
            return False, errors

        return True, []

    def validate_tests(self, branch_name: str) -> tuple[bool, list[str]]:
        """Validate that tests pass for the branch."""
        print(f"  🧪 Running tests for {branch_name}...")
        errors = []

        # Check if pytest is available and run tests
        result = self.run_command(["python", "-m", "pytest", "--version"])
        if result.returncode != 0:
            errors.append("pytest not available")
            return False, errors

        # Run tests with timeout
        result = self.run_command(["python", "-m", "pytest", "tests/", "-v", "--tb=short", "--maxfail=5"], timeout=300)

        if result.returncode != 0:
            errors.append(f"Tests failed: {result.stderr}")
            return False, errors

        return True, []

    def validate_linting(self, branch_name: str) -> tuple[bool, list[str]]:
        """Validate code quality with linting."""
        print(f"  🔍 Running linting for {branch_name}...")
        errors = []
        warnings = []

        # Check with ruff if available
        result = self.run_command(["ruff", "check", ".", "--output-format=text"])
        if result.returncode == 0:
            return True, []
        if result.returncode == 1:
            # Ruff found issues but didn't crash
            if result.stdout:
                warnings.extend(result.stdout.split("\n"))
            return True, warnings  # Treat as warning, not error
        errors.append(f"Linting failed: {result.stderr}")
        return False, errors

    def validate_branch(self, branch_name: str) -> ValidationResult:
        """Validate a single branch comprehensively."""
        print(f"\n🔍 Validating branch: {branch_name}")

        # Checkout the branch
        if not self.checkout_branch(branch_name):
            return ValidationResult(
                branch_name=branch_name,
                build_success=False,
                test_success=False,
                lint_success=False,
                error_messages=[f"Failed to checkout branch {branch_name}"],
                warnings=[],
            )

        # Run validations
        build_success, build_errors = self.validate_build(branch_name)
        test_success, test_errors = self.validate_tests(branch_name)
        lint_success, lint_warnings = self.validate_linting(branch_name)

        all_errors = build_errors + test_errors

        result = ValidationResult(
            branch_name=branch_name,
            build_success=build_success,
            test_success=test_success,
            lint_success=lint_success,
            error_messages=all_errors,
            warnings=lint_warnings,
        )

        # Print immediate results
        status = "✅" if build_success and test_success else "❌"
        print(
            f"  {status} Build: {'✅' if build_success else '❌'} | Tests: {'✅' if test_success else '❌'} | Lint: {'✅' if lint_success else '⚠️'}",
        )

        return result

    def find_split_branches(self) -> list[str]:
        """Find all branches that end with '-split'."""
        result = self.run_command(["git", "branch", "--list", "*-split"])
        if result.returncode != 0:
            return []

        branches = []
        for line in result.stdout.strip().split("\n"):
            branch = line.strip().replace("*", "").strip()
            if branch and branch.endswith("-split"):
                branches.append(branch)

        return branches

    def generate_validation_report(self) -> None:
        """Generate a comprehensive validation report."""
        print("\n" + "=" * 80)
        print("🔍 BRANCH VALIDATION REPORT")
        print("=" * 80)

        total_branches = len(self.validation_results)
        successful_branches = sum(1 for r in self.validation_results if r.build_success and r.test_success)

        print(f"\n📊 SUMMARY: {successful_branches}/{total_branches} branches passed validation")

        # Detailed results
        for result in self.validation_results:
            print(f"\n📋 {result.branch_name}")
            print(f"   Build: {'✅ PASS' if result.build_success else '❌ FAIL'}")
            print(f"   Tests: {'✅ PASS' if result.test_success else '❌ FAIL'}")
            print(f"   Lint:  {'✅ PASS' if result.lint_success else '⚠️  WARN'}")

            if result.error_messages:
                print("   ❌ Errors:")
                for error in result.error_messages[:3]:  # Show first 3 errors
                    print(f"      • {error}")
                if len(result.error_messages) > 3:
                    print(f"      ... and {len(result.error_messages) - 3} more errors")

            if result.warnings:
                print("   ⚠️  Warnings:")
                for warning in result.warnings[:3]:  # Show first 3 warnings
                    if warning.strip():
                        print(f"      • {warning.strip()}")

        # Recommendations
        failed_branches = [r for r in self.validation_results if not (r.build_success and r.test_success)]

        if failed_branches:
            print(f"\n⚠️  FAILED BRANCHES ({len(failed_branches)}):")
            for result in failed_branches:
                print(f"   • {result.branch_name}")

            print("\n💡 RECOMMENDATIONS:")
            print("   • Fix build/test issues before creating PRs")
            print("   • Consider merging dependency branches first")
            print("   • Check if missing files need to be added to branches")
        else:
            print("\n✅ ALL BRANCHES VALIDATED SUCCESSFULLY!")
            print("   • All branches can build and test independently")
            print("   • Safe to create Pull Requests")

        # Save detailed report
        self.save_validation_report()

    def save_validation_report(self) -> None:
        """Save validation results to a JSON file."""
        report_data = {
            "timestamp": subprocess.run(
                ["date", "-Iseconds"],
                check=False,
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "total_branches": len(self.validation_results),
            "successful_branches": sum(1 for r in self.validation_results if r.build_success and r.test_success),
            "results": [
                {
                    "branch_name": r.branch_name,
                    "build_success": r.build_success,
                    "test_success": r.test_success,
                    "lint_success": r.lint_success,
                    "error_count": len(r.error_messages),
                    "warning_count": len(r.warnings),
                    "errors": r.error_messages,
                    "warnings": r.warnings,
                }
                for r in self.validation_results
            ],
        }

        with open("branch_validation_report.json", "w") as f:
            json.dump(report_data, f, indent=2)

        print("\n💾 Detailed report saved to: branch_validation_report.json")

    def run(self) -> None:
        """Main execution method."""
        print("🚀 Starting branch validation...")

        # Store original branch
        self.original_branch = self.get_current_branch()
        if not self.original_branch:
            print("❌ Error: Could not determine current branch")
            sys.exit(1)

        # Find split branches
        split_branches = self.find_split_branches()
        if not split_branches:
            print("❌ No split branches found. Run the branch creation script first.")
            sys.exit(1)

        print(f"📋 Found {len(split_branches)} split branches to validate")

        # Validate each branch
        for branch in split_branches:
            try:
                result = self.validate_branch(branch)
                self.validation_results.append(result)
            except Exception as e:
                print(f"❌ Error validating {branch}: {e}")
                self.validation_results.append(
                    ValidationResult(
                        branch_name=branch,
                        build_success=False,
                        test_success=False,
                        lint_success=False,
                        error_messages=[f"Validation error: {e}"],
                        warnings=[],
                    ),
                )

        # Return to original branch
        if self.original_branch:
            self.checkout_branch(self.original_branch)

        # Generate report
        self.generate_validation_report()


def main():
    """Main entry point."""
    validator = BranchValidator()
    validator.run()


if __name__ == "__main__":
    main()
