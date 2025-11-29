---
title: Namespace Best Practices
tags:
  - developer-guide
  - best-practices
  - namespace
---

# Namespace Best Practices

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

This guide explains namespace packages and the `__all__` declaration in Python, with specific examples from the Tux codebase and best practices for maintaining clean APIs.

## What Are Namespace Packages?

Namespace packages are a Python packaging feature that allows you to split a single logical package across multiple directories on the filesystem. Unlike regular packages, namespace packages don't contain an `__init__.py` file in every directory level.

### Key Characteristics

- **No `__init__.py` required**: Directories can be namespace packages without an `__init__.py` file
- **Multiple locations**: The same namespace can exist in multiple physical locations
- **Lazy loading**: Submodules are only loaded when accessed
- **Flexible structure**: Allows for extensible plugin architectures

## Regular Packages vs Namespace Packages

### Regular Package

```text
mypackage/
├── __init__.py          # Required - defines the package
├── module1.py
└── submodule/
    ├── __init__.py      # Required - defines the submodule
    └── module2.py
```

### Namespace Package

```text
namespace/
├── part1/
│   ├── __init__.py      # Optional - if present, marks as regular package
│   └── feature.py
└── part2/
    └── another.py       # Can be imported as namespace.part2.another
```

## The `__all__` Declaration

`__all__` is a special list that explicitly defines what should be considered the public API of a module. When `__all__` is defined, only the names listed in it will be imported when using `from module import *`.

### Why `__all__` Matters

1. **API Clarity**: Clearly defines what consumers should use
2. **Import Safety**: Prevents accidental import of internal implementation details
3. **Documentation**: Serves as living documentation of the module's interface
4. **Refactoring Safety**: Changes to internal code don't break star imports

## Best Practices

### 1. Always Define `__all__` for Public Modules

```python
# ✅ Good - Explicit public API
__all__ = [
    "PublicClass",
    "public_function",
    "CONSTANT",
]

# ❌ Bad - Implicit public API
# No __all__ defined - everything is implicitly public
```

### 2. Use Descriptive Grouping in `__all__`

```python
__all__ = [
    # Core classes
    "BaseController",
    "DatabaseService",

    # Utility functions
    "generate_usage",
    "convert_bool",

    # Constants
    "DEFAULT_TIMEOUT",
    "MAX_RETRIES",
]
```

### 3. Namespace Packages Should Have Empty `__all__`

```python
"""
This is a namespace package - individual modules are imported directly
from their submodules rather than through this package.
"""

# Namespace package - no direct exports
__all__ = []
```

### 4. Keep `__all__` Alphabetically Sorted

```python
__all__ = [
    "Apple",
    "Banana",
    "Cherry",  # ✅ Alphabetically sorted
    "Date",
]
```

### 5. Update `__all__` When Adding/Removing Public APIs

When you add a new public function or class, always update `__all__`:

```python
# New function added
def new_public_function():
    """A new public API function."""
    pass

# Update __all__ to include it
__all__ = [
    "existing_function",
    "new_public_function",  # ✅ Added to __all__
]
```

## Examples from Tux Codebase

### Database Controllers (Regular Package with Full API)

```python
# src/tux/database/controllers/__init__.py
__all__ = [
    "AfkController",
    "BaseController",
    "CaseController",
    "DatabaseCoordinator",
    "GuildConfigController",
    "GuildController",
    "LevelsController",
    "PermissionAssignmentController",
    "PermissionCommandController",
    "PermissionRankController",
    "ReminderController",
    "SnippetController",
    "StarboardController",
    "StarboardMessageController",
]
```

### Modules (Namespace Package)

```python
# src/tux/modules/__init__.py
"""
Tux bot modules package.

This package contains all the feature modules for the Tux Discord bot.
Each module is a self-contained package that provides specific functionality.

This is a namespace package - individual modules are imported directly
(e.g., from tux.modules.moderation import cases) rather than through this package.
"""

# Namespace package - no direct exports
__all__ = []
```

### UI Components (Comprehensive Public API)

```python
# src/tux/ui/__init__.py
__all__ = [
    # Embeds
    "EmbedCreator",
    "EmbedType",
    # Buttons
    "GithubButton",
    "XkcdButtons",
    # Views
    "BaseConfirmationView",
    "ConfirmationDanger",
    "ConfirmationNormal",
    "TldrPaginatorView",
    # Modals
    "ReportModal",
]
```

### Core Utilities (Focused API)

```python
# src/tux/core/flags.py
__all__ = [
    # Base converter
    "TuxFlagConverter",
    # Moderation flags
    "BanFlags",
    "TempBanFlags",
    "UnbanFlags",
    "KickFlags",
    "WarnFlags",
    "TimeoutFlags",
    "UntimeoutFlags",
    "JailFlags",
    "UnjailFlags",
    # Case management flags
    "CasesViewFlags",
    "CaseModifyFlags",
    # Snippet flags
    "SnippetBanFlags",
    "SnippetUnbanFlags",
    # Poll flags
    "PollBanFlags",
    "PollUnbanFlags",
    # Utility flags
    "TldrFlags",
]
```

## Common Patterns & Anti-Patterns

### ✅ Good Patterns

**Consistent Grouping:**

```python
__all__ = [
    # Classes
    "MyClass",
    "HelperClass",
    # Functions
    "process_data",
    "validate_input",
    # Constants
    "DEFAULT_VALUE",
]
```

**Namespace Package Documentation:**

```python
"""
This is a namespace package for extensibility.

Import specific implementations:
    from mypackage.auth import login
    from mypackage.cache import get_cache
"""

__all__ = []
```

### ❌ Anti-Patterns

**Importing Private Functions with Aliases:**

```python
# ❌ Bad - Confusing alias for public function
from public_module import public_function as _private_alias

# ✅ Good - Use public name directly
from public_module import public_function
```

**Missing `__all__` in Public Modules:**

```python
# ❌ Bad - Everything implicitly public
def _private_function(): pass
def public_function(): pass

# ✅ Good - Explicit public API
__all__ = ["public_function"]

def _private_function(): pass
def public_function(): pass
```

**Over-Exporting:**

```python
# ❌ Bad - Too many exports, unclear API boundary
__all__ = ["Class1", "Class2", "Class3", "_private", "utility_func", "helper"]

# ✅ Good - Focused, clear API
__all__ = ["Class1", "Class2"]  # Only the main public classes
```

## Tools & Validation

### Type Checking

Use `basedpyright` or `mypy` to validate `__all__` declarations:

```bash
uv run basedpyright
```

### Testing Imports

Test that star imports work correctly:

```python
# Test star import behavior
from mymodule import *  # Should only import __all__ items

# Verify expected items are available
assert "PublicClass" in dir()
assert "_PrivateClass" not in dir()  # Should not be imported
```

### Linting

Configure linters to check for:

- Missing `__all__` in public modules
- Unsorted `__all__` lists
- Inconsistent `__all__` formatting

## Migration Guide

### Converting Regular Package to Namespace Package

1. **Remove `__init__.py`** from namespace directories
2. **Add documentation** explaining the namespace concept
3. **Set `__all__ = []`** to indicate no direct exports
4. **Update imports** throughout codebase

### Adding `__all__` to Existing Module

1. **Identify public API** by analyzing imports across codebase
2. **Create comprehensive list** of all public symbols
3. **Sort alphabetically** within logical groups
4. **Add documentation comments** for clarity
5. **Test star imports** to ensure nothing breaks

## When to Use Each Approach

### Use Regular Packages When

- You have a fixed, well-defined API
- All functionality is contained within the package
- You want to provide convenience imports through `__init__.py`
- The package has a single, clear purpose

### Use Namespace Packages When

- You want extensible plugin architecture
- Different parts of the package may be installed separately
- You want to allow third-party extensions
- The package serves as a collection point for related modules

## Related Concepts

- **Plugin Architecture**: Namespace packages enable clean plugin systems
- **API Design**: `__all__` is part of good API design practices
- **Import Patterns**: Understanding when to use explicit vs implicit imports
- **Package Structure**: How to organize large Python projects

## Further Reading

- [Python Packaging Guide: Namespace Packages](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/)
- [PEP 420: Implicit Namespace Packages](https://peps.python.org/pep-0420/)
- [The `__all__` Special Variable](https://docs.python.org/3/tutorial/modules.html#importing-from-a-package)
