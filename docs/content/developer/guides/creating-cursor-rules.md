---
title: Creating Cursor Rules
tags:
  - cursor
  - rules
  - development
  - guide
---

<!-- markdownlint-disable MD024 -->

# Guide: Creating Cursor Rules

Step-by-step guide for creating new Cursor rules for the Tux project.

## Quick Start

1. **Choose Domain** - Select appropriate domain directory
2. **Copy Template** - Use `.cursor/templates/rule-template.mdc`
3. **Fill Content** - Add project-specific patterns
4. **Validate** - Ensure file meets standards
5. **Test** - Verify rule applies correctly

## Detailed Steps

### Step 1: Choose Domain

Select the domain that best fits your rule:

- **`core/`** - Core project rules (tech stack, dependencies)
- **`database/`** - Database patterns (models, migrations, controllers)
- **`modules/`** - Discord bot modules (cogs, commands, events)
- **`testing/`** - Testing patterns (pytest, fixtures, markers)
- **`docs/`** - Documentation rules (Zensical, writing standards)
- **`security/`** - Security patterns (secrets, validation)
- **`error-handling/`** - Error handling (logging, Sentry)
- **`ui/`** - UI components (Discord Components V2)
- **`meta/`** - System documentation (specifications)

### Step 2: Create File

1. Navigate to appropriate domain directory
2. Create new `.mdc` file with kebab-case name
3. Example: `database/models.mdc`

### Step 3: Add Metadata

Copy and customize frontmatter:

```yaml
---
description: Brief description (60-120 chars) with domain keywords
globs: src/tux/database/**/*.py  # Optional, comma-separated for file-scoped
alwaysApply: false  # true for always-apply rules
---
```

**Metadata Guidelines:**

- **description**: Include domain keywords, be specific
- **globs**: Use comma-separated file patterns for file-scoped rules (no quotes, no brackets)
- **alwaysApply**: Only true for project-wide standards

### Step 4: Write Content

Follow this structure:

1. **Title (H1)** - Clear, descriptive
2. **Overview** - Purpose and scope
3. **Patterns** - ✅ GOOD / ❌ BAD examples
4. **Best Practices** - Key guidelines
5. **Anti-Patterns** - What to avoid
6. **Examples** - Detailed examples (optional)
7. **See Also** - Cross-references

### Step 5: Add Examples

Include working code examples:

```python
# ✅ GOOD: Show correct pattern
from tux.database.models import BaseModel

class MyModel(BaseModel, table=True):
    """Model description."""
    id: int = Field(primary_key=True)
```

```python
# ❌ BAD: Show anti-pattern
class MyModel:  # Missing BaseModel
    id: int  # Missing Field definition
```

### Step 6: Add Cross-References

Link to related rules:

```markdown
## See Also

- @database/migrations.mdc - Migration patterns
- @database/controllers.mdc - Controller patterns
- @AGENTS.md - General coding standards
```

### Step 7: Validate

Check:

- [ ] File under 500 lines
- [ ] Includes code examples
- [ ] Includes anti-patterns
- [ ] Has proper metadata
- [ ] Cross-references complete
- [ ] Project-specific (not generic)

## Example: Creating a Database Rule

1. **Domain**: `database/`
2. **File**: `database/models.mdc`
3. **Metadata**:

   ```yaml
   description: SQLModel database model patterns for Tux
   globs: src/tux/database/models/**/*.py
   alwaysApply: false
   ```

4. **Content**: Add patterns, examples, anti-patterns
5. **Cross-references**: Link to migrations, controllers rules

## Common Patterns

### File-Scoped Rule

```yaml
---
description: Patterns for specific file type
globs: src/tux/modules/**/*.py
alwaysApply: false
---
```

### Always-Apply Rule

```yaml
---
description: Project-wide standard
alwaysApply: true
---
```

### Intelligent Rule

```yaml
---
description: Domain-specific patterns with keywords
alwaysApply: false
---
```

## Best Practices

1. **Be Specific** - Tailor to Tux project, not generic
2. **Include Examples** - Show working code
3. **Show Anti-Patterns** - What NOT to do
4. **Cross-Reference** - Link to related rules
5. **Keep Focused** - One domain/concern per rule
6. **Stay Current** - Update when patterns change

## Templates

### Complete Rule Template

```markdown
---
description: Brief description (60-120 chars) with domain keywords
globs: optional/file/pattern, another/pattern
alwaysApply: false
---

# Rule Title

## Overview

Brief description of the rule's purpose and scope.

## Patterns

✅ **GOOD:** Example of correct pattern
```python
# Code example
```

❌ **BAD:** Example of anti-pattern

```python
# Code example
```

## Best Practices

1. Practice 1
2. Practice 2

## Anti-Patterns

1. ❌ Anti-pattern 1
2. ❌ Anti-pattern 2

## See Also

- @related-rule.mdc
- @AGENTS.md

## Standards

### Naming

- **Rules**: kebab-case, descriptive (e.g., `database-models.mdc`)
- **Location**: `.cursor/rules/{domain}/`
- **Format**: `.mdc` files with YAML frontmatter

### Content Requirements

- **Project-specific**: Tailored to Tux, not generic
- **Examples**: Include working code examples
- **Anti-patterns**: Show what NOT to do
- **Cross-references**: Link to related rules/commands

### Quality Standards

- Clear, actionable content
- Consistent formatting
- File under 500 lines
- Proper metadata format

## Validation

Run validation before committing:

```bash
uv run ai validate-rules
```

This checks:

- Frontmatter format
- Description length (60-120 chars)
- Content requirements (examples, anti-patterns)
- Globs format (comma-separated, no quotes/brackets)
- File structure

## Maintenance

### Updating Rules

- Keep content current with code changes
- Update examples when patterns change
- Add new anti-patterns as discovered
- Update cross-references when structure changes

### Review Process

- Review rules during code reviews
- Update when project patterns change
- Remove obsolete rules
- Consolidate duplicate content

## See Also

- [Rule Template](../../../../.cursor/templates/rule-template.mdc)
- [Creating Cursor Commands](creating-cursor-commands.md) - Guide for creating commands
- @meta/cursor-rules.mdc - Rules specification
