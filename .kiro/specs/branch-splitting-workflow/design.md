# Design Document

## Overview

The branch-splitting-workflow feature provides an interactive command-line tool that helps developers systematically break up large, unfocused branches with single large commits into multiple focused pull requests. The tool analyzes file changes within a commit, provides intelligent grouping suggestions based on file patterns, and automates the creation of clean feature branches with focused commits while preserving all original changes.

## Architecture

The system follows a modular architecture with clear separation of concerns:

```
Branch Splitting Workflow
├── Analysis Engine (git history parsing)
├── Grouping Interface (interactive CLI)
├── Branch Creation Engine (git operations)
├── Validation System (build/test checks)
└── PR Template Generator (documentation)
```

The workflow operates in distinct phases:

1. **Analysis Phase**: Parse git history and identify changes
2. **Planning Phase**: Interactive grouping of changes
3. **Execution Phase**: Create branches and apply changes
4. **Validation Phase**: Verify branch integrity
5. **Documentation Phase**: Generate PR templates

## Components and Interfaces

### GitAnalyzer Component

**Purpose**: Analyzes the current branch to understand all changes and their relationships.

**Key Methods**:

- `analyze_branch(branch_name: str) -> BranchAnalysis`
- `get_modified_files() -> List[FileChange]`
- `get_commit_history() -> List[CommitInfo]`
- `suggest_groupings() -> List[GroupSuggestion]`

**Data Structures**:

```python
@dataclass
class FileChange:
    path: str
    change_type: str  # 'modified', 'added', 'deleted'
    lines_added: int
    lines_removed: int
    commits: List[str]

@dataclass
class CommitInfo:
    hash: str
    message: str
    files: List[str]
    timestamp: datetime

@dataclass
class BranchAnalysis:
    base_branch: str
    current_branch: str
    total_commits: int
    modified_files: List[FileChange]
    commit_history: List[CommitInfo]
    suggested_groups: List[GroupSuggestion]
```

### InteractiveGrouper Component

**Purpose**: Provides an interactive CLI interface for users to organize changes into logical groups.

**Key Methods**:

- `display_analysis(analysis: BranchAnalysis) -> None`
- `create_group(name: str) -> Group`
- `assign_changes_to_group(group: Group, changes: List[Union[FileChange, CommitInfo]]) -> None`
- `validate_groupings(groups: List[Group]) -> ValidationResult`

**Features**:

- Rich terminal UI with color-coded file listings
- Expandable/collapsible sections for large change sets
- Drag-and-drop style assignment of files/commits to groups
- Real-time validation of group completeness

### BranchCreator Component

**Purpose**: Handles the git operations to create clean feature branches from the defined groups, specifically designed for splitting single large commits.

**Key Methods**:

- `create_backup_branch() -> str`
- `create_feature_branch(group: Group) -> str`
- `apply_partial_changes(branch: str, files: List[FileChange]) -> None`
- `create_focused_commit(branch: str, group: Group) -> str`
- `handle_conflicts() -> ConflictResolution`

**Git Strategy for Single Large Commits**:

- Creates backup branch: `{original-branch}-backup-{timestamp}`
- Creates feature branches: `{group-name}-split-{timestamp}`
- Uses `git checkout` from base branch + selective `git add` for partial file application
- Creates new focused commits with descriptive messages based on group content
- Implements conflict resolution workflow with user guidance

### ValidationSystem Component

**Purpose**: Ensures that split branches are ready for PR creation.

**Key Methods**:

- `validate_branch(branch_name: str) -> ValidationResult`
- `run_build_check(branch_name: str) -> bool`
- `run_test_suite(branch_name: str) -> TestResult`
- `verify_completeness(original_branch: str, split_branches: List[str]) -> bool`

**Validation Checks**:

- Build system compatibility (Poetry, dependencies)
- Test suite execution
- Code quality checks (linting, type checking)
- Change completeness verification

### PRTemplateGenerator Component

**Purpose**: Generates PR titles, descriptions, and templates for each split branch.

**Key Methods**:

- `generate_pr_title(group: Group) -> str`
- `generate_pr_description(group: Group, analysis: BranchAnalysis) -> str`
- `create_pr_checklist(group: Group) -> List[str]`
- `generate_github_commands(branches: List[str]) -> List[str]`

## Data Models

### Core Models

```python
@dataclass
class Group:
    name: str
    description: str
    files: List[FileChange]
    commits: List[CommitInfo]
    branch_name: Optional[str] = None
    
@dataclass
class GroupSuggestion:
    name: str
    rationale: str
    files: List[str]
    confidence: float  # 0.0 to 1.0

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
@dataclass
class ConflictResolution:
    conflicted_files: List[str]
    resolution_strategy: str
    manual_intervention_required: bool
```

### Configuration Model

```python
@dataclass
class WorkflowConfig:
    base_branch: str = "main"
    backup_branch_prefix: str = "backup"
    feature_branch_prefix: str = "split"
    max_files_per_group: int = 20
    enable_auto_suggestions: bool = True
    validation_checks: List[str] = field(default_factory=lambda: ["build", "test", "lint"])
```

## Error Handling

### Git Operation Errors

- **Merge Conflicts**: Pause workflow, provide conflict resolution guidance, allow manual resolution
- **Cherry-pick Failures**: Offer alternative strategies (patch application, manual recreation)
- **Branch Creation Failures**: Validate branch names, handle existing branch conflicts

### Validation Errors

- **Build Failures**: Report specific errors, suggest fixes, allow user to continue or abort
- **Test Failures**: Show test results, allow selective branch creation
- **Missing Changes**: Alert user to incomplete groupings, prevent branch creation

### User Input Errors

- **Invalid Groupings**: Validate group names, prevent duplicate assignments
- **Empty Groups**: Warn about empty groups, require confirmation
- **Unassigned Changes**: Block workflow completion until all changes are assigned

## Testing Strategy

### Unit Tests

- **GitAnalyzer**: Mock git commands, test parsing logic with various commit histories
- **InteractiveGrouper**: Test CLI interactions with automated input simulation
- **BranchCreator**: Test git operations in isolated test repositories
- **ValidationSystem**: Mock build/test systems, test validation logic

### Integration Tests

- **End-to-End Workflow**: Create test repositories with complex histories, run full workflow
- **Conflict Resolution**: Test various conflict scenarios and resolution strategies
- **Multi-Branch Validation**: Verify that split branches contain all original changes

### Test Data

- **Sample Repositories**: Create repositories with various branching patterns
- **Complex Histories**: Test with merge commits, rebased branches, file renames
- **Edge Cases**: Empty commits, binary files, large files, permission changes

## Implementation Phases

### Phase 1: Core Analysis

- Implement GitAnalyzer component
- Basic file and commit parsing
- Simple grouping suggestions based on file paths

### Phase 2: Interactive Interface

- Build InteractiveGrouper with rich CLI
- Implement group creation and assignment
- Add validation for complete groupings

### Phase 3: Branch Operations

- Implement BranchCreator with git operations
- Add backup branch creation
- Implement cherry-pick workflow with conflict handling

### Phase 4: Validation & Templates

- Build ValidationSystem with configurable checks
- Implement PRTemplateGenerator
- Add GitHub integration commands

### Phase 5: Polish & Documentation

- Add comprehensive error handling
- Create user documentation and examples
- Implement configuration system
