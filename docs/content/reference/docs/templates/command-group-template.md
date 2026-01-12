---
title: COMMAND_GROUP_NAME
description: COMMAND_GROUP_DESCRIPTION
tags:
  - user-guide
  - commands
  - command-groups
  - COMMAND_GROUP_TAG
---

# {COMMAND_GROUP_NAME}

<!--
INTRODUCTION
Write 1-2 paragraphs that describe what this command group does, its purpose, and how subcommands work.
Merge the introduction and overview into a cohesive opening - don't create a separate "Overview" section.

First paragraph: What the command group provides and its main purpose.
Second paragraph (optional): How subcommands extend the functionality, or important context about the group.

Keep it concise but informative - users should understand what this command group offers at a glance.
-->

{Your introduction paragraphs go here}

## Base Command

<!--
BASE COMMAND SECTION
Document what happens when the base command is invoked without a subcommand.
If the base command doesn't do anything useful without a subcommand, you can skip detailed documentation here.
-->

The base `{COMMAND_GROUP_NAME}` command {describes base functionality}.

**Syntax:**

```text
/{COMMAND_GROUP_NAME}
${COMMAND_GROUP_NAME}
<!-- If aliases exist, add them here -->
${ALIAS1}
${ALIAS2}
```

**Aliases:**

<!-- Remove aliases section if none exist -->

You can also use these aliases instead of `{COMMAND_GROUP_NAME}`:

- `{ALIAS1}` - {Brief description if helpful, otherwise remove this line}
- `{ALIAS2}` - {Brief description if helpful, otherwise remove this line}

When invoked without a subcommand, this command {what happens}.

## Subcommands

<!--
SUBCOMMANDS TABLE
Create a table listing all subcommands in this command group.
The table format is: Subcommand name, Aliases (or — if none), Brief description, Usage example.

Use the format: | `subcommand` | `alias1`, `alias2` (or —) | {Brief description} | `/GROUP_NAME subcommand` |
-->

| Subcommand | Aliases | Description | Usage |
|------------|--------|-------------|-------|
| `{SUBCOMMAND_NAME}` | `{ALIAS1}`, `{ALIAS2}` | {Brief description} | `/{GROUP_NAME} {SUBCOMMAND_NAME} [params]` |
| `{SUBCOMMAND_NAME}` | — | {Brief description} | `/{GROUP_NAME} {SUBCOMMAND_NAME} [params]` |

<!--
SUBCOMMAND CATEGORIES
If subcommands fall into logical categories, organize them by category.
If all subcommands are similar in function, you can list them individually without categories.
Use level 3 headings for categories, level 4 headings for individual subcommands.
-->

### Category: {CATEGORY_NAME}

{Description of this category of subcommands}

#### {SUBCOMMAND_NAME}

{Brief description of what this subcommand does - 2-3 sentences}

**Syntax:**

```text
/{GROUP_NAME} {SUBCOMMAND_NAME} [parameters]
${GROUP_NAME} {SUBCOMMAND_NAME} [parameters]
<!-- If subcommand has aliases, add them here -->
${GROUP_NAME} {ALIAS1} [parameters]
${GROUP_NAME} {ALIAS2} [parameters]
```

**Aliases:**

<!-- Remove aliases section if none exist -->

- `{ALIAS1}` - {Brief description if helpful, otherwise remove this line}
- `{ALIAS2}` - {Brief description if helpful, otherwise remove this line}

**Parameters:**

- `{PARAMETER_NAME}` - {Description}
- `{PARAMETER_NAME}` - {Description}

**Example:**

```text
/{GROUP_NAME} {SUBCOMMAND_NAME} parameter_value
```

## Common Workflows

<!--
COMMON WORKFLOWS
Describe 2-4 typical multi-step workflows using multiple subcommands.
This helps users understand how to accomplish common tasks using the command group.

For each workflow:
- Use a level 3 heading with a descriptive name
- Write 1-2 sentences explaining what this workflow accomplishes
- List steps (numbered list) showing the workflow
- Include an example sequence if helpful
-->

### Workflow Name: {WORKFLOW_DESCRIPTION}

{Description of what this workflow accomplishes - 1-2 sentences}

**Steps:**

1. Use `/{GROUP_NAME} {SUBCOMMAND_NAME}` to {action}
2. Use `/{GROUP_NAME} {SUBCOMMAND_NAME}` to {action}
3. Use `/{GROUP_NAME} {SUBCOMMAND_NAME}` to {action}

**Example:**

```text
/{GROUP_NAME} {SUBCOMMAND_NAME} parameter
/{GROUP_NAME} {SUBCOMMAND_NAME} parameter
/{GROUP_NAME} {SUBCOMMAND_NAME} parameter
```

## Permissions

<!--
PERMISSIONS SECTION
Document permission requirements for the command group.
Note if different subcommands have different permission requirements.
-->

### Bot Permissions

Tux requires the following permissions for this command group:

- **{PERMISSION_NAME}** - {Why it's needed}
- **{PERMISSION_NAME}** - {Why it's needed}

### User Permissions

Users need {PERMISSION_LEVEL} or higher to use commands in this group.

!!! note "Subcommand Permissions"
    {Note if subcommands have different permissions, or if all share the same permissions}

!!! info "Permission System"
    Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Configuration

<!--
CONFIGURATION SECTION
Only include this section if the command group requires configuration or has settings.
If no configuration is needed, remove this entire section.

List the configuration options that users need to set up, with brief descriptions.
Link to the admin configuration guide for detailed instructions.
-->

This command group requires the following configuration:

- **{SETTING_NAME}:** {Description and how to configure}
- **{SETTING_NAME}:** {Description and how to configure}

!!! info "Configuration Guide"
    For detailed configuration instructions, see the [Admin Guide](../../../admin/config/index.md).

## Examples

<!--
EXAMPLES SECTION
Provide practical examples of using the command group.
Include both individual subcommand examples and workflow examples.
-->

### Example 1: {EXAMPLE_SCENARIO}

{Description of the scenario}

```text
/{GROUP_NAME} {SUBCOMMAND_NAME} parameter
```

{What happens when this is executed}

### Example 2: {MULTI_STEP_SCENARIO}

{Description of a multi-step scenario}

```text
/{GROUP_NAME} {SUBCOMMAND_NAME} parameter1
/{GROUP_NAME} {SUBCOMMAND_NAME} parameter2
/{GROUP_NAME} {SUBCOMMAND_NAME} parameter3
```

{What happens after the workflow}

## Dashboard/Interface

<!--
DASHBOARD/INTERFACE SECTION
Only include this section if the command group opens a dashboard or interactive UI.
If no dashboard/UI exists, remove this entire section.

Describe what users see and how to interact with the interface.
-->

When you use `/{GROUP_NAME}` or certain subcommands, Tux opens an interactive {DASHBOARD_TYPE}.

**Features:**

- {Feature 1} - {Description}
- {Feature 2} - {Description}
- {Feature 3} - {Description}

**Navigation:**

- {How to navigate the interface}
- {How to interact with components}
- {How to save/cancel changes}

## Related Documentation

<!--
RELATED DOCUMENTATION
Link to related pages, features, or modules that users might find helpful.
Include links to:
- Related modules (if applicable)
- Configuration guides
- Permission configuration
- Related features
-->

- [Related Module](path/to/module.md)
- [Configuration Guide](../../../admin/config/{RELATED_CONFIG}.md)
- [Permission Configuration](../../../admin/config/commands.md)
