# Static Analysis Integration Configuration

## Overview

This document provides detailed configuration for integrating advanced static analysis tools into the Tux Discord bot development workflow. These configurations build upon the existing Ruff and Pyright setup to provide comprehensive code quality analysis.

## 1. Bandit Security Analysis Integration

### Installation and Configuration

#### Poetry Dependencies

```toml
# Add to pyproject.toml [tool.poetry.group.dev.dependencies]
bandit = "^1.7.5"
bandit-sarif-formatter = "^1.1.1"  # For GitHub Security tab integration
```

#### Bandit Configuration

```toml
# Add to pyproject.toml
[tool.bandit]
# Exclude test files and virtual environments
exclude_dirs = [
    "tests",
    ".venv", 
    ".archive",
    "typings",
    "__pycache__",
    ".pytest_cache"
]

# Skip specific checks that are not relevant for Discord bots
skips = [
    "B101",  # assert_used - asserts are acceptable in tests
    "B601",  # paramiko_calls - not using paramiko
    "B602",  # subprocess_popen_with_shell_equals_true - controlled usage
]

# Test patterns to identify test files
tests = ["test_*.py", "*_test.py"]

# Confidence levels: LOW, MEDIUM, HIGH
confidence = "MEDIUM"

# Severity levels: LOW, MEDIUM, HIGH
severity = "M"

# Additional security patterns specific to Discord bots
[tool.bandit.plugins]
# Custom plugin for Discord token validation
discord_token_check = true
# Check for hardcoded secrets in configuration
hardcoded_secrets = true
```

#### Pre-commit Integration

```yaml
# Add to .pre-commit-config.yaml
- repo: https://github.com/PyCQA/bandit
  rev: 1.7.5
  hooks:
    - id: bandit
      args: ['-c', 'pyproject.toml']
      additional_dependencies: ['bandit[toml]']
```

#### GitHub Actions Integration

```yaml
# Add to .github/workflows/security.yml
- name: Run Bandit Security Analysis
  run: |
    poetry run bandit -r tux/ -f sarif -o bandit-results.sarif
    poetry run bandit -r tux/ -f json -o bandit-results.json
    
- name: Upload Bandit SARIF results
  uses: github/codeql-action/upload-sarif@v2
  if: always()
  with:
    sarif_file: bandit-results.sarif
```

## 2. Vulture Dead Code Detection

### Installation and Configuration

#### Poetry Dependencies

```toml
# Add to pyproject.toml [tool.poetry.group.dev.dependencies]
vulture = "^2.10"
```

#### Vulture Configuration

```toml
# Add to pyproject.toml
[tool.vulture]
# Directories to exclude from analysis
exclude = [
    "tests/",
    ".venv/",
    ".archive/",
    "typings/",
    "__pycache__/",
    "migrations/"
]

# Ignore decorators that create "unused" functions
ignore_decorators = [
    "@app_commands.command",
    "@commands.command", 
    "@commands.group",
    "@tasks.loop",
    "@commands.Cog.listener",
    "@property",
    "@staticmethod",
    "@classmethod",
    "@cached_property"
]

# Ignore names that appear unused but are required
ignore_names = [
    "setUp",
    "tearDown", 
    "test_*",
    "cog_*",
    "*_command",
    "*_group",
    "on_*",  # Discord.py event handlers
    "setup",  # Cog setup function
    "interaction",  # Common Discord interaction parameter
]

# Minimum confidence level (0-100)
min_confidence = 80

# Make whitelist (allowlist) for known false positives
make_whitelist = true

# Sort results by confidence
sort_by_size = true
```

#### Vulture Whitelist Generation

```python
# scripts/generate_vulture_whitelist.py
"""Generate vulture whitelist for Discord bot patterns."""

import ast
import os
from pathlib import Path
from typing import List

def generate_discord_whitelist() -> List[str]:
    """Generate whitelist for common Discord.py patterns."""
    whitelist = [
        # Discord.py event handlers
        "on_ready",
        "on_message", 
        "on_member_join",
        "on_member_remove",
        "on_guild_join",
        "on_guild_remove",
        "on_command_error",
        
        # Common Discord.py attributes
        "bot",
        "guild",
        "channel", 
        "user",
        "member",
        "message",
        "interaction",
        "ctx",
        
        # Cog lifecycle methods
        "cog_load",
        "cog_unload",
        "cog_check",
        "cog_command_error",
        
        # Database model attributes (Prisma generated)
        "id",
        "created_at",
        "updated_at",
    ]
    return whitelist

if __name__ == "__main__":
    whitelist = generate_discord_whitelist()
    with open("vulture_whitelist.py", "w") as f:
        for item in whitelist:
            f.write(f"{item}\n")
```

#### Pre-commit Integration

```yaml
# Add to .pre-commit-config.yaml
- repo: https://github.com/jendrikseipp/vulture
  rev: v2.10
  hooks:
    - id: vulture
      args: ['--min-confidence', '80']
```

## 3. Radon Complexity Analysis

### Installation and Configuration

#### Poetry Dependencies

```toml
# Add to pyproject.toml [tool.poetry.group.dev.dependencies]
radon = "^6.0.1"
xenon = "^0.9.1"  # Radon integration for monitoring
```

#### Radon Configuration

```ini
# Create .radonrc file
[radon]
# Exclude patterns
exclude = tests/*,migrations/*,.venv/*,.archive/*,typings/*

# Complexity thresholds
cc_min = C  # Minimum complexity to show (A, B, C, D, E, F)
mi_min = A  # Minimum maintainability index to show

# Output format
output_format = json

# Show complexity for all functions
show_complexity = true

# Include average complexity
average = true

# Sort results by complexity
sort = true
```

#### Complexity Monitoring Script

```python
# scripts/complexity_monitor.py
"""Monitor code complexity metrics."""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any

class ComplexityMonitor:
    """Monitor and report code complexity metrics."""
    
    def __init__(self, source_dir: str = "tux"):
        self.source_dir = source_dir
        self.thresholds = {
            "cyclomatic_complexity": 10,
            "maintainability_index": 20,
            "lines_of_code": 100,
        }
    
    def run_cyclomatic_complexity(self) -> Dict[str, Any]:
        """Run cyclomatic complexity analysis."""
        result = subprocess.run([
            "radon", "cc", self.source_dir, 
            "--json", "--average"
        ], capture_output=True, text=True)
        
        return json.loads(result.stdout) if result.stdout else {}
    
    def run_maintainability_index(self) -> Dict[str, Any]:
        """Run maintainability index analysis."""
        result = subprocess.run([
            "radon", "mi", self.source_dir, "--json"
        ], capture_output=True, text=True)
        
        return json.loads(result.stdout) if result.stdout else {}
    
    def run_raw_metrics(self) -> Dict[str, Any]:
        """Run raw metrics analysis."""
        result = subprocess.run([
            "radon", "raw", self.source_dir, "--json"
        ], capture_output=True, text=True)
        
        return json.loads(result.stdout) if result.stdout else {}
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive complexity report."""
        return {
            "cyclomatic_complexity": self.run_cyclomatic_complexity(),
            "maintainability_index": self.run_maintainability_index(),
            "raw_metrics": self.run_raw_metrics(),
            "thresholds": self.thresholds,
        }
    
    def check_thresholds(self, report: Dict[str, Any]) -> List[str]:
        """Check if complexity exceeds thresholds."""
        violations = []
        
        # Check cyclomatic complexity
        cc_data = report.get("cyclomatic_complexity", {})
        for file_path, metrics in cc_data.items():
            if isinstance(metrics, list):
                for metric in metrics:
                    if metric.get("complexity", 0) > self.thresholds["cyclomatic_complexity"]:
                        violations.append(
                            f"High complexity in {file_path}:{metric.get('name')}: "
                            f"{metric.get('complexity')}"
                        )
        
        return violations

if __name__ == "__main__":
    monitor = ComplexityMonitor()
    report = monitor.generate_report()
    violations = monitor.check_thresholds(report)
    
    if violations:
        print("Complexity violations found:")
        for violation in violations:
            print(f"  - {violation}")
    else:
        print("All complexity checks passed!")
```

#### GitHub Actions Integration

```yaml
# Add to .github/workflows/ci.yml
- name: Run Complexity Analysis
  run: |
    poetry run python scripts/complexity_monitor.py
    poetry run radon cc tux/ --average --json > complexity-report.json
    poetry run radon mi tux/ --json > maintainability-report.json
    
- name: Upload Complexity Reports
  uses: actions/upload-artifact@v3
  with:
    name: complexity-reports
    path: |
      complexity-report.json
      maintainability-report.json
```

## 4. Enhanced Ruff Configuration

### Advanced Rule Configuration

```toml
# Enhanced pyproject.toml [tool.ruff.lint] section
select = [
    # Existing rules...
    "I",     # isort
    "E",     # pycodestyle-error
    "F",     # pyflakes
    "PERF",  # perflint
    "N",     # pep8-naming
    "TRY",   # tryceratops
    "UP",    # pyupgrade
    "FURB",  # refurb
    "PL",    # pylint
    "B",     # flake8-bugbear
    "SIM",   # flake8-simplify
    "ASYNC", # flake8-async
    "A",     # flake8-builtins
    "C4",    # flake8-comprehensions
    "DTZ",   # flake8-datetimez
    "EM",    # flake8-errmsg
    "PIE",   # flake8-pie
    "T20",   # flake8-print
    "Q",     # flake8-quotes
    "RET",   # flake8-return
    "PTH",   # flake8-use-pathlib
    "INP",   # flake8-no-pep420
    "RSE",   # flake8-raise
    "ICN",   # flake8-import-conventions
    "RUF",   # ruff
    
    # New security and quality rules
    "S",     # flake8-bandit (security)
    "BLE",   # flake8-blind-except
    "FBT",   # flake8-boolean-trap
    "G",     # flake8-logging-format
    "LOG",   # flake8-logging
    "T10",   # flake8-debugger
    "ERA",   # eradicate (commented code)
    "PGH",   # pygrep-hooks
    "FLY",   # flynt (f-string conversion)
    "SLOT",  # flake8-slots
    "COM",   # flake8-commas
]

# Enhanced ignore patterns
ignore = [
    "E501",    # line-too-long (handled by formatter)
    "N814",    # camelcase-imported-as-constant
    "PLR0913", # too-many-arguments
    "PLR2004", # magic-value-comparison
    "S101",    # assert (acceptable in tests)
    "T201",    # print (acceptable for CLI tools)
    "FBT001",  # boolean-positional-arg (common in Discord.py)
    "FBT002",  # boolean-default-arg (common in Discord.py)
]

# Per-file ignores for specific contexts
[tool.ruff.lint.per-file-ignores]
"tests/*" = [
    "S101",    # assert statements in tests
    "PLR2004", # magic values in tests
    "S106",    # hardcoded passwords in test fixtures
    "ARG001",  # unused function arguments in fixtures
]
"migrations/*" = [
    "ERA001",  # commented code acceptable in migrations
    "T201",    # print statements for migration logging
]
"scripts/*" = [
    "T201",    # print statements in scripts
    "S602",    # subprocess calls in utility scripts
]
"tux/cli/*" = [
    "T201",    # print statements in CLI
    "PLR0912", # too many branches in CLI logic
]

# Enhanced flake8-bugbear configuration
[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = [
    "discord.Embed",
    "discord.Color",
    "datetime.datetime",
    "datetime.date",
]

# Enhanced flake8-quotes configuration
[tool.ruff.lint.flake8-quotes]
docstring-quotes = "double"
inline-quotes = "double"
multiline-quotes = "double"

# Enhanced isort configuration
[tool.ruff.lint.isort]
known-first-party = ["tux"]
known-third-party = ["discord", "prisma"]
section-order = [
    "future",
    "standard-library", 
    "third-party",
    "first-party",
    "local-folder"
]
```

### Custom Ruff Rules for Discord Bots

```python
# scripts/custom_ruff_rules.py
"""Custom Ruff rules for Discord bot patterns."""

from typing import List, Dict, Any

class DiscordBotRules:
    """Custom rules specific to Discord bot development."""
    
    @staticmethod
    def check_command_docstrings(node: Any) -> List[Dict[str, Any]]:
        """Ensure all Discord commands have proper docstrings."""
        violations = []
        
        # Check for @app_commands.command decorator
        if hasattr(node, 'decorator_list'):
            has_command_decorator = any(
                'command' in str(decorator) 
                for decorator in node.decorator_list
            )
            
            if has_command_decorator and not node.docstring:
                violations.append({
                    'code': 'TUX001',
                    'message': 'Discord command missing docstring',
                    'line': node.lineno,
                })
        
        return violations
    
    @staticmethod
    def check_interaction_response(node: Any) -> List[Dict[str, Any]]:
        """Ensure interaction.response is always called."""
        violations = []
        
        # Implementation would check for interaction parameter
        # and ensure response is called
        
        return violations
    
    @staticmethod
    def check_database_transactions(node: Any) -> List[Dict[str, Any]]:
        """Ensure database operations use proper transactions."""
        violations = []
        
        # Implementation would check for database calls
        # without proper transaction context
        
        return violations
```

## 5. IDE Integration

### VS Code Configuration

```json
// .vscode/settings.json
{
    "python.linting.enabled": true,
    "python.linting.banditEnabled": true,
    "python.linting.banditArgs": ["-c", "pyproject.toml"],
    
    "ruff.enable": true,
    "ruff.organizeImports": true,
    "ruff.fixAll": true,
    
    "python.analysis.typeCheckingMode": "strict",
    "python.analysis.autoImportCompletions": true,
    
    "files.associations": {
        "*.toml": "toml",
        "*.yml": "yaml",
        "*.yaml": "yaml"
    },
    
    "editor.codeActionsOnSave": {
        "source.organizeImports": true,
        "source.fixAll.ruff": true
    },
    
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    
    "coverage-gutters.coverageFileNames": [
        "coverage.xml",
        "htmlcov/index.html"
    ]
}
```

### PyCharm Configuration

```xml
<!-- .idea/inspectionProfiles/Project_Default.xml -->
<component name="InspectionProjectProfileManager">
  <profile version="1.0">
    <option name="myName" value="Project Default" />
    <inspection_tool class="PyBanditInspection" enabled="true" level="WARNING" enabled_by_default="true" />
    <inspection_tool class="PyRuffInspection" enabled="true" level="ERROR" enabled_by_default="true" />
    <inspection_tool class="PyComplexityInspection" enabled="true" level="WARNING" enabled_by_default="true">
      <option name="m_limit" value="10" />
    </inspection_tool>
  </profile>
</component>
```

## 6. Continuous Integration Integration

### Enhanced CI Pipeline

```yaml
# .github/workflows/static-analysis.yml
name: Static Analysis

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  static-analysis:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python Environment
      uses: ./.github/actions/setup-python
      with:
        python-version: '3.13'
        install-groups: dev,types
        
    - name: Run Bandit Security Analysis
      run: |
        poetry run bandit -r tux/ -f sarif -o bandit-results.sarif
        poetry run bandit -r tux/ -f json -o bandit-results.json
        
    - name: Run Vulture Dead Code Detection
      run: |
        poetry run vulture tux/ --min-confidence 80 > vulture-results.txt
        
    - name: Run Radon Complexity Analysis
      run: |
        poetry run radon cc tux/ --json > complexity-results.json
        poetry run radon mi tux/ --json > maintainability-results.json
        
    - name: Upload Security Results to GitHub
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: bandit-results.sarif
        
    - name: Upload Analysis Artifacts
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: static-analysis-results
        path: |
          bandit-results.json
          vulture-results.txt
          complexity-results.json
          maintainability-results.json
          
    - name: Comment PR with Results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          
          // Read analysis results
          const banditResults = JSON.parse(fs.readFileSync('bandit-results.json', 'utf8'));
          const vulture = fs.readFileSync('vulture-results.txt', 'utf8');
          
          // Create comment body
          let comment = '## Static Analysis Results\n\n';
          comment += `### Security Analysis (Bandit)\n`;
          comment += `- Issues found: ${banditResults.results.length}\n`;
          comment += `- Confidence: ${banditResults.metrics.confidence}\n\n`;
          
          if (vulture.trim()) {
            comment += `### Dead Code Detection (Vulture)\n`;
            comment += '```\n' + vulture + '\n```\n\n';
          }
          
          // Post comment
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: comment
          });
```

## 7. Monitoring and Reporting

### Quality Metrics Collection

```python
# scripts/quality_metrics.py
"""Collect and report static analysis metrics."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class StaticAnalysisMetrics:
    """Collect metrics from static analysis tools."""
    
    def collect_bandit_metrics(self) -> Dict[str, Any]:
        """Collect Bandit security metrics."""
        result = subprocess.run([
            "bandit", "-r", "tux/", "-f", "json"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "total_issues": len(data.get("results", [])),
                "high_severity": len([r for r in data.get("results", []) if r.get("issue_severity") == "HIGH"]),
                "medium_severity": len([r for r in data.get("results", []) if r.get("issue_severity") == "MEDIUM"]),
                "low_severity": len([r for r in data.get("results", []) if r.get("issue_severity") == "LOW"]),
            }
        return {"error": result.stderr}
    
    def collect_vulture_metrics(self) -> Dict[str, Any]:
        """Collect Vulture dead code metrics."""
        result = subprocess.run([
            "vulture", "tux/", "--min-confidence", "80"
        ], capture_output=True, text=True)
        
        dead_code_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        return {
            "dead_code_items": len(dead_code_lines),
            "details": dead_code_lines
        }
    
    def collect_complexity_metrics(self) -> Dict[str, Any]:
        """Collect complexity metrics."""
        cc_result = subprocess.run([
            "radon", "cc", "tux/", "--json", "--average"
        ], capture_output=True, text=True)
        
        mi_result = subprocess.run([
            "radon", "mi", "tux/", "--json"
        ], capture_output=True, text=True)
        
        cc_data = json.loads(cc_result.stdout) if cc_result.stdout else {}
        mi_data = json.loads(mi_result.stdout) if mi_result.stdout else {}
        
        return {
            "cyclomatic_complexity": cc_data,
            "maintainability_index": mi_data
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive static analysis report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "bandit": self.collect_bandit_metrics(),
            "vulture": self.collect_vulture_metrics(),
            "complexity": self.collect_complexity_metrics(),
        }

if __name__ == "__main__":
    metrics = StaticAnalysisMetrics()
    report = metrics.generate_report()
    
    # Save report
    with open("static-analysis-report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("Static analysis report generated!")
```

This comprehensive static analysis integration provides a robust foundation for maintaining high code quality standards while building on the existing tools and processes in the Tux Discord bot project.
