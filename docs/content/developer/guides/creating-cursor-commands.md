---
title: Creating Cursor Commands
tags:
  - cursor
  - commands
  - development
  - guide
---

# Guide: Creating Cursor Commands

Step-by-step guide for creating new Cursor commands for the Tux project.

## Quick Start

1. **Choose Category** - Select appropriate category directory
2. **Copy Template** - Use `.cursor/templates/command-template.md`
3. **Fill Content** - Add project-specific workflow
4. **Validate** - Ensure command meets standards
5. **Test** - Verify command works correctly

## Detailed Steps

### Step 1: Choose Category

Select the category that best fits your command:

- **`code-quality/`** - Code quality workflows
- **`testing/`** - Testing workflows
- **`database/`** - Database workflows
- **`discord/`** - Discord bot workflows
- **`security/`** - Security workflows
- **`debugging/`** - Debugging workflows
- **`error-handling/`** - Error handling workflows
- **`documentation/`** - Documentation workflows
- **`development/`** - Development workflows

### Step 2: Create File

1. Navigate to appropriate category directory
2. Create new `.md` file with kebab-case name
3. Example: `database/migration.md`

### Step 3: Write Title

Use clear, action-oriented title:

```markdown
# Database Migration
```

### Step 4: Write Overview

Brief description of what the command does:

```markdown
## Overview

Create and apply Alembic database migrations for schema changes.
```

### Step 5: Write Steps

Numbered steps with sub-steps:

```markdown
## Steps

1. **Create Migration**
   - Run `uv run db migrate-dev "description"`
   - Review generated migration file
   - Verify upgrade and downgrade functions

2. **Review Migration**
   - Ensure both functions implemented
   - Check for proper constraints
   - Validate enum handling
```

### Step 6: Add Error Handling

Include troubleshooting:

```markdown
## Error Handling

If migration fails:
- Check migration file syntax
- Verify database connection
- Review error messages
```

### Step 7: Add Checklist

Verifiable checklist items:

```markdown
## Checklist

- [ ] Migration file created
- [ ] Both upgrade and downgrade implemented
- [ ] Migration tested
- [ ] Applied to development database
```

### Step 8: Add Cross-References

Link to related commands and rules:

```markdown
## See Also

- Related command: `/database-health`
- Related rule: @database/migrations.mdc
```

## Example: Creating a Database Command

1. **Category**: `database/`
2. **File**: `database/migration.md`
3. **Title**: `# Database Migration`
4. **Overview**: Brief description
5. **Steps**: Numbered workflow steps
6. **Error Handling**: Troubleshooting guide
7. **Checklist**: Verifiable items
8. **See Also**: Cross-references

## Common Patterns

### Simple Command

```markdown
# Command Title

## Overview
Brief description.

## Steps
1. Step one
2. Step two

## Checklist
- [ ] Item one
- [ ] Item two
```

### Complex Command

```markdown
# Command Title

## Overview
Detailed description.

## Steps
1. **Step Title**
   - Sub-step
   - Detail
2. **Step Title**
   - Sub-step

## Error Handling
Troubleshooting steps.

## Checklist
- [ ] Item one
- [ ] Item two

## See Also
- Related command: `/other`
- Related rule: @rule.mdc
```

## Best Practices

1. **Be Action-Oriented** - Use verbs in title
2. **Clear Steps** - Numbered, with sub-steps
3. **Complete Checklist** - Verifiable items
4. **Error Handling** - Include troubleshooting
5. **Cross-Reference** - Link to related commands/rules
6. **Project-Specific** - Reference Tux tools and patterns

## Templates

### Complete Command Template

```markdown
# Command Title

## Overview

Brief description of command purpose and expected outcome.

## Steps

1. **Step Title**
   - Sub-step or detail
   - Additional context
2. **Step Title**
   - Sub-step or detail

## Error Handling

If operation fails:
- Troubleshooting step 1
- Troubleshooting step 2

## Checklist

- [ ] Item one
- [ ] Item two
- [ ] Item three

## See Also

- Related command: `/other-command`
- Related rule: @rule-name.mdc
```

## Standards

### Naming

- **Commands**: kebab-case, action-oriented (e.g., `database-migration.md`)
- **Location**: `.cursor/commands/{category}/`
- **Format**: `.md` files (plain markdown)

### Content Requirements

- **Project-specific**: Tailored to Tux, not generic
- **Examples**: Include working code examples
- **Error handling**: Show how to handle failures
- **Cross-references**: Link to related commands/rules

### Quality Standards

- Clear, actionable content
- Consistent formatting
- Complete checklists
- Proper error handling

## Validation

Run validation before committing:

```bash
uv run ai validate-rules
```

This checks:

- File structure
- Content requirements (steps, checklist)
- Error handling included
- Cross-references complete

## Maintenance

### Updating Commands

- Update steps when workflows change
- Keep checklists current
- Update error handling as needed
- Verify all commands still work

### Review Process

- Review commands during code reviews
- Update when project patterns change
- Remove obsolete commands
- Consolidate duplicate content

## See Also

- [Command Template](../../../../.cursor/templates/command-template.md)
- [Creating Cursor Rules](creating-cursor-rules.md) - Guide for creating rules
- @meta/cursor-commands.mdc - Commands specification
