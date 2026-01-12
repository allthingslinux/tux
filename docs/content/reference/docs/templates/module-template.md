---
title: MODULE_NAME
description: MODULE_DESCRIPTION
tags:
  - user-guide
  - modules
  - MODULE_TAG
---

# {MODULE_NAME}

<!--
INTRODUCTION
Write 1-2 paragraphs that describe what this module does, its purpose, who uses it, and key features.
Merge the introduction and overview into a cohesive opening - don't create a separate "Overview" section.

First paragraph: What the module provides and its main purpose.
Second paragraph (optional): Additional context, important features, or key benefits.

Keep it concise but informative - users should understand what this module offers at a glance.
-->

{Your introduction paragraphs go here}

## Command Groups

<!--
COMMAND GROUPS SECTION
Only include this section if the module has command groups (hybrid_group commands with subcommands).
If the module has no command groups, remove this entire section.

For each command group:
- Use a level 3 heading with the command group name (e.g., ### Cases)
- Write a brief description of what the command group does
- List the subcommands with brief descriptions and aliases (if any)
-->

This module includes the following command groups:

### {GROUP_NAME}

{Brief description of what this command group does and its purpose}

**Commands:**

- `{COMMAND_NAME}` (aliases: `{ALIAS1}`, `{ALIAS2}`) - {Brief description}
- `{COMMAND_NAME}` - {Brief description}

## Commands

<!--
COMMANDS TABLE
Create a table listing all commands in this module. Each command should link to its individual documentation page.
The table format is: Command name, Aliases (or — if none), Brief one-line description, Link to detailed documentation.

Use the format: | `/command` | `alias1`, `alias2` (or —) | {Brief description} | [Details](command.md) |
-->

| Command | Aliases | Description | Documentation |
|---------|--------|-------------|---------------|
| `/command` | `{ALIAS1}`, `{ALIAS2}` | {Brief one-line description} | [Details](command.md) |
| `/command` | — | {Brief one-line description} | [Details](command.md) |

## Common Use Cases

<!--
COMMON USE CASES
Describe 2-4 typical workflows or scenarios where this module is used.
This helps users understand when and how to use the module.

For each use case:
- Use a level 3 heading with a descriptive name
- Write 1-2 sentences explaining when this use case applies
- List steps (numbered list) showing the workflow
- Include an example command if helpful

Focus on practical, real-world scenarios that users will encounter.
-->

### Use Case Name: {SCENARIO_DESCRIPTION}

{Brief description of when this use case applies - 1-2 sentences}

**Steps:**

1. {Step 1 with example command if helpful}
2. {Step 2 with example command if helpful}
3. {Step 3 with example command if helpful}

**Example:**

```text
/command @user parameter
```

## Configuration

<!--
CONFIGURATION SECTION
Only include this section if the module requires configuration or has settings.
If no configuration is needed, remove this entire section.

List the configuration options that users need to set up, with brief descriptions.
Link to the admin configuration guide for detailed instructions.
-->

This module requires the following configuration:

- **{SETTING_NAME}:** {Description and how to configure}
- **{SETTING_NAME}:** {Description and how to configure}

!!! info "Configuration Guide"
    For detailed configuration instructions, see the [Admin Guide](../../../admin/config/index.md).

## Permissions

<!--
PERMISSIONS SECTION
Document permission requirements for using commands in this module.

Bot Permissions: List the Discord permissions Tux needs, with explanations.
User Permissions: Describe who can use these commands (all users, moderators only, etc.).
Include the permission system tip as shown below.
-->

### Bot Permissions

Tux requires the following permissions for this module:

- **{PERMISSION_NAME}** - {Why it's needed}
- **{PERMISSION_NAME}** - {Why it's needed}

### User Permissions

{Describe user permission requirements - e.g., "Users need Moderator rank (typically rank 3-5) or higher to use commands in this module" or "Commands are available to all users by default"}

!!! tip "Permission System"
    Tux uses a dynamic permission system. Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Related Documentation

<!--
RELATED DOCUMENTATION
Link to related pages, features, or modules that users might find helpful.
Include links to:
- Related features (if applicable)
- Configuration guides
- Permission configuration
- Related modules or command groups
-->

- [Related Feature or Module](path/to/doc.md)
- [Configuration Guide](../../../admin/config/{RELATED_CONFIG}.md)
- [Permission Configuration](../../../admin/config/commands.md)

!!! info "Documentation Templates"
    When documenting individual commands, command groups, or features related to this module, use the appropriate templates from [Documentation Templates](../index.md). These templates ensure consistency and completeness across all documentation.
