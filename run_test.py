#!/usr/bin/env python3
"""
Test runner that bypasses pytest configuration by using a clean environment.
"""

import os
import shutil
import subprocess
import sys
import tempfile


def run_tests():
    # Create a temporary directory for test execution
    temp_dir = tempfile.mkdtemp(prefix="tux_test_")

    try:
        # Copy the test file to the temporary directory
        test_file = "tests/unit/tux/modules/snippets/test_snippets_base.py"
        test_dir = os.path.join(temp_dir, os.path.dirname(test_file))
        os.makedirs(test_dir, exist_ok=True)
        shutil.copy2(test_file, os.path.join(test_dir, os.path.basename(test_file)))

        # Copy any required test fixtures
        fixture_dir = os.path.join(temp_dir, "tests/fixtures")
        if os.path.exists("tests/fixtures"):
            shutil.copytree("tests/fixtures", fixture_dir)

        # Run pytest with clean environment
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(".")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            os.path.join(test_dir, os.path.basename(test_file)),
            "-v",
            "--tb=short",
        ]

        result = subprocess.run(cmd, cwd=temp_dir, env=env, check=False)
        return result.returncode

    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    print("Running tests in a clean environment...")
    sys.exit(run_tests())


if __name__ == "__main__":
    main()
