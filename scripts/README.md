# Branch Splitting Workflow

A comprehensive toolkit for splitting large commits into focused, reviewable branches with dependency management and validation.

## 🎯 Overview

This workflow helps you take a large commit with many file changes and split it into multiple focused branches that can be reviewed and merged independently. It includes dependency analysis, conflict detection, and validation to ensure each branch works correctly.

## 📋 Scripts

### 1. `analyze_branch_split.py` - Analysis & Grouping

Analyzes file changes and dependencies to suggest logical groupings.

**Features:**

- Parses git diff statistics to show change impact
- Analyzes Python import dependencies between changed files
- Suggests logical groupings based on file paths and dependencies
- Interactive grouping with dependency conflict warnings
- Saves grouping decisions to `branch_groups.json`

**Usage:**

```bash
python scripts/analyze_branch_split.py
```

### 2. `create_split_branches.py` - Branch Creation

Creates focused branches from the analyzed groups.

**Features:**

- Creates backup of original branch
- Resets original branch and selectively commits files by group
- Generates descriptive commit messages for each branch
- Validates completeness across all branches
- Generates PR preparation commands and templates

**Usage:**

```bash
python scripts/create_split_branches.py
```

### 3. `validate_split_branches.py` - Branch Validation

Validates that each split branch can build and test independently.

**Features:**

- Tests build process (poetry install, module imports)
- Runs test suite for each branch
- Performs code quality checks (linting)
- Generates comprehensive validation report
- Saves results to `branch_validation_report.json`

**Usage:**

```bash
python scripts/validate_split_branches.py
```

## 🚀 Complete Workflow

### Step 1: Analyze and Group Files

```bash
# Make sure you're on the branch with the large commit
git checkout misc/kaizen

# Run the analysis script
python scripts/analyze_branch_split.py
```

The script will:

1. Show all changed files with statistics
2. Analyze dependencies between files
3. Suggest logical groupings
4. Let you choose grouping strategy (dependency-first recommended)
5. Save groups to `branch_groups.json`

### Step 2: Create Split Branches

```bash
# Create focused branches from the groups
python scripts/create_split_branches.py
```

The script will:

1. Create a backup branch (`misc/kaizen-backup-TIMESTAMP`)
2. Reset the original branch to before the large commit
3. Create separate branches for each group with focused commits
4. Generate PR templates in `pr_templates/` directory
5. Show push commands and merge order

### Step 3: Validate Split Branches

```bash
# Validate that each branch works independently
python scripts/validate_split_branches.py
```

The script will:

1. Check out each split branch
2. Test build process (dependencies, imports)
3. Run test suite
4. Check code quality
5. Generate validation report

### Step 4: Push and Create PRs

```bash
# Push all branches (commands provided by create script)
git push origin 01-core-foundation-split
git push origin 02-error-handling-split
git push origin 03-services-split
git push origin 04-other-cogs-split
git push origin 05-dependencies-and-cli-split
```

Use the generated PR templates in `pr_templates/` for creating Pull Requests.

## 📁 Generated Files

- `branch_groups.json` - File grouping decisions
- `branch_validation_report.json` - Validation results
- `pr_templates/*.md` - PR templates for each branch
- `misc/kaizen-backup-*` - Backup branch

## 🔧 Configuration

### Grouping Strategies

1. **Dependency-First (Recommended)**: Groups files to minimize cross-dependencies
2. **Feature-Based**: Groups by functionality (may have dependency conflicts)
3. **Custom**: Manual file assignment

### Branch Naming Convention

Branches are named: `{group-name}-split`

- `01-core-foundation-split`
- `02-error-handling-split`
- `03-services-split`
- `04-other-cogs-split`
- `05-dependencies-and-cli-split`

### Merge Order

For dependency management:

1. **01-core-foundation** (contains shared dependencies)
2. **02-error-handling** (depends on core)
3. **03-services, 04-other-cogs, 05-dependencies-and-cli** (independent)

## 🧪 Validation Checks

Each branch is validated for:

- **Build Success**: Dependencies install, modules import correctly
- **Test Success**: All tests pass
- **Code Quality**: Linting passes (warnings allowed)

## 📝 PR Templates

Generated templates include:

- Comprehensive change descriptions
- Dependency information
- Testing checklists
- Merge instructions
- File change lists

## 🔍 Troubleshooting

### Common Issues

**"No split branches found"**

- Run `create_split_branches.py` first

**"Failed to checkout branch"**

- Ensure branches exist: `git branch --list "*-split"`
- Check for uncommitted changes

**"Build validation failed"**

- Check if dependencies are missing in the branch
- May need to merge dependency branches first

**"Dependency conflicts detected"**

- Use dependency-first grouping strategy
- Or plan merge order carefully

### Recovery

If something goes wrong:

```bash
# Return to backup branch
git checkout misc/kaizen-backup-TIMESTAMP

# Or restore original branch
git branch -D misc/kaizen
git checkout -b misc/kaizen misc/kaizen-backup-TIMESTAMP
```

## 🎯 Best Practices

1. **Always create backups** before running the workflow
2. **Use dependency-first grouping** to minimize conflicts
3. **Validate branches** before creating PRs
4. **Follow merge order** for dependent branches
5. **Review PR templates** and customize as needed
6. **Test locally** before pushing branches

## 📊 Example Output

```
🎉 BRANCH SPLITTING COMPLETE!
================================================================================

📋 CREATED BRANCHES (5):
  1. 01-core-foundation-split
     feat: implement core bot infrastructure and monitoring system
  2. 02-error-handling-split
     refactor: modernize error handling and sentry integration
  ...

🚀 NEXT STEPS:
  1. Push branches to remote:
     git push origin 01-core-foundation-split
     git push origin 02-error-handling-split
     ...

  2. Create Pull Requests in this order:
     1. 01-core-foundation-split → main
     2. 02-error-handling-split → main
     ...

✅ All files accounted for - safe to push branches!
```

This workflow ensures that large commits are split into manageable, reviewable pieces while maintaining code integrity and dependency relationships.
