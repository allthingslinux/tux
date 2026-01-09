---
title: Documentation Templates
description: Templates and guides for creating consistent documentation
tags:
  - documentation
  - templates
  - developer
---

# Documentation Templates

This directory contains templates for documenting Tux's modules, commands, command groups, and features. These templates provide structured outlines to ensure consistency across all documentation.

## Available Templates

### Module Template

**File:** [`module-template.md`](module-template.md)

Use this template for documenting a collection of related commands (modules).

**Examples:**

- Moderation module (ban, kick, warn, etc.)
- Utility module (ping, poll, remindme, etc.)
- Fun module (random, xkcd, etc.)

**When to use:**

- Documenting a module containing multiple related commands
- Creating overview documentation for a command category
- Organizing commands by functional area

### Command Template

**File:** [`command-template.md`](command-template.md)

Use this template for documenting individual commands.

**Examples:**

- `/ban` command
- `/ping` command
- `/level` command
- `/kick` command

**When to use:**

- Documenting a single command with detailed information
- Creating command reference pages
- Providing comprehensive command documentation

### Command Group Template

**File:** [`command-group-template.md`](command-group-template.md)

Use this template for documenting command groups with subcommands.

**Examples:**

- `/config` command group (config ranks, config roles, etc.)
- `/levels` command group (levels set, levels reset, etc.)
- `/cases` command group (cases view, cases edit, etc.)

**When to use:**

- Documenting a base command with multiple subcommands
- Creating documentation for hierarchical command structures
- Organizing related subcommands under a parent command

### Feature Template

**File:** [`feature-template.md`](feature-template.md)

Use this template for documenting automated features and systems.

**Examples:**

- Leveling/XP system
- Starboard feature
- Bookmarks feature
- Status roles feature
- Temporary voice channels

**When to use:**

- Documenting automated/background features
- Creating documentation for systems that work without direct command invocation
- Documenting features with configuration and event-driven behavior

## How to Use Templates

1. **Choose the appropriate template** based on what you're documenting
2. **Copy the template** to your target location in `docs/content/`
3. **Replace placeholders** marked with `{PLACEHOLDER_NAME}` or `UPPER_CASE`
4. **Fill in all sections** with actual content
5. **Remove optional sections** that don't apply to your documentation
6. **Add or expand sections** as needed for your specific use case
7. **Follow documentation style guidelines** from `.cursor/rules/docs/style.mdc`

## Template Structure

All templates include:

- **Frontmatter** - YAML metadata (title, description, tags)
- **Introduction** - Clear explanation of purpose (merged intro/overview)
- **Core Content** - Detailed sections specific to the template type
- **Examples** - Practical usage examples
- **Configuration** - Setup and configuration (if applicable)
- **Permissions** - Permission requirements
- **Related Documentation** - Links to related pages

## Template Guidelines

### Placeholders

Templates use two placeholder formats:

- **UPPER_CASE** - Used in frontmatter (YAML doesn't support curly braces)
- **{curly_braces}** - Used in content sections for placeholders

Replace all placeholders with actual values. For example:

- `MODULE_NAME` → `Moderation`
- `{COMMAND_NAME}` → `ban`
- `{DESCRIPTION}` → `Ban members from your Discord server`

### Optional Sections

Many templates include optional sections marked with HTML comments like:

```html
<!--
CONFIGURATION SECTION
Only include this section if the module requires configuration.
If no configuration is needed, remove this entire section.
-->
```

Remove these sections entirely if they don't apply to your documentation.

### HTML Comments

Templates use HTML comments to provide guidance to contributors. These comments explain:

- What to write in each section
- When to include or remove sections
- Formatting requirements
- Best practices

Leave these comments in place until you've filled out the section, then remove them as you complete each part.

## Documentation Standards

When using these templates, ensure you:

- ✅ Use second person ("you") throughout
- ✅ Write in present simple tense
- ✅ Use active voice
- ✅ Provide working code examples
- ✅ Include both slash (`/command`) and prefix (`$command`) syntax
- ✅ Document permissions clearly (bot and user)
- ✅ Link to related documentation
- ✅ Follow the Diátaxis framework (tutorial, how-to, reference, explanation)
- ✅ Use appropriate admonitions (tip, warning, info, danger)
- ✅ Keep content scannable with clear headings

## Example Workflow

1. **Identify what you're documenting**

   | What are you documenting?      | Template to use              |
   |-------------------------------|------------------------------|
   | Module                        | Module template              |
   | Command                       | Command template             |
   | Command group                 | Command group template       |
   | Feature                       | Feature template             |

2. **Copy the template** to the appropriate location

   - Modules: `docs/content/user/modules/{module-name}/index.md`
   - Commands: `docs/content/user/modules/{module-name}/{command-name}.md`
   - Command groups: `docs/content/user/modules/{module-name}/index.md` (if it's a module subdirectory)
   - Features: `docs/content/user/features/{feature-name}.md`

3. **Replace placeholders** with actual values

   - [ ] Fill in frontmatter first (title, description, tags)
   - [ ] Replace all `{PLACEHOLDER}` and `PLACEHOLDER` values

4. **Write content** following the HTML comment guidance

   - [ ] Read the comments for each section
   - [ ] Write clear, helpful documentation
   - [ ] Remove comments as you complete each section

5. **Review and polish**

   - [ ] Verify all links work
   - [ ] Check code examples are accurate
   - [ ] Ensure consistency with existing documentation
   - [ ] Remove any remaining placeholder text

## Getting Help

For questions about:

- **Documentation style:** See [Documentation Writing Style](../../../.cursor/rules/docs/style.mdc)
- **Documentation patterns:** See [Documentation Patterns](../../../.cursor/rules/docs/patterns.mdc)
- **Documentation structure:** See [Documentation Structure](../../../.cursor/rules/docs/structure.mdc)
- **Zensical syntax:** See [Zensical Syntax](../../../.cursor/rules/docs/syntax.mdc)

!!! tip "Template Flexibility"
    Templates are designed to be comprehensive but flexible. Remove sections that don't apply, and add sections specific to your documentation needs. The templates serve as guides, not strict requirements.
