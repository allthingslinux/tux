---
title: COMMAND_NAME
description: COMMAND_DESCRIPTION
tags:
  - user-guide
  - commands
  - COMMAND_TAG
---

# {COMMAND_NAME}

<!--
INTRODUCTION
Write 1-2 paragraphs that describe what this command does, its purpose, and when to use it.
Merge the introduction and overview into a cohesive opening - don't create a separate "Overview" section.

First paragraph: What the command does and its main purpose.
Second paragraph (optional): Important context, key features, or use cases.

Keep it concise but informative - users should understand what this command offers at a glance.
-->

{Your introduction paragraphs go here}

## Syntax

<!--
SYNTAX SECTION
Show both slash command and prefix command formats.
Include aliases if applicable.
-->

The `{COMMAND_NAME}` command can be used in two ways:

**Slash Command:**

```text
/{COMMAND_NAME} [parameters]
```

**Prefix Command:**

```text
${COMMAND_NAME} [parameters]
```

**Aliases:**

<!-- Remove aliases section if none exist -->

- `{ALIAS1}`
- `{ALIAS2}`

## Parameters

<!--
PARAMETERS SECTION
Create a table listing all parameters/arguments for the command.
Then provide detailed descriptions for each parameter if needed.

Use the format: | `PARAMETER_NAME` | {TYPE} | {Yes/No} | {Description} |

IMPORTANT: Parameters vs Flags
- Parameters: Core arguments like `member`, `reason`, `duration` that are part of the command's primary function
  - In prefix commands: Can be positional (e.g., `$ban @user reason`) or named flags (e.g., `$ban @user -duration 1d`)
  - In slash commands: Always named parameters (e.g., `/ban member:@user reason:"..."`)
  - For optional parameters like `reason`, note: "In prefix commands, this is a positional argument. In slash commands, it is a named parameter."
- Flags: Optional named options that modify behavior (e.g., `-silent`, `-purge`, `-quiet`)
  - Always use flag syntax with dashes (e.g., `-silent`, `--flag-name`)
  - Document aliases if they exist (e.g., `-s`, `-quiet` for `-silent`)
-->

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `{PARAMETER_NAME}` | {TYPE} | {Yes/No} | {Description} |
| `reason` | String | No | The reason for the action. In prefix commands, this is a positional argument. In slash commands, it is a named parameter. Defaults to "No reason provided". |

<!--
DETAILED PARAMETER DESCRIPTIONS
Expand on each parameter with examples and constraints if the command has complex parameters.
If parameters are straightforward, you can skip this section.
-->

### {PARAMETER_NAME}

{Detailed description of the parameter}

- **Type:** {TYPE}
- **Required:** {Yes/No}
- **Constraints:** {Any limits, format requirements, etc.}
- **Examples:** {Valid values or formats}

## Flags

<!--
FLAGS SECTION
Only include this section if the command uses flags (flag converter).
If no flags exist, remove this entire section.

IMPORTANT: Flags are optional named options that modify command behavior.
They are NOT core parameters like `member` or `reason` - those belong in Parameters.
Flags use flag syntax: `-silent`, `-purge`, `-duration`, etc.

Create a table listing all flags, then provide detailed descriptions for each.
-->

This command supports the following flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `-{FLAG_NAME}` | {TYPE} | {DEFAULT} | {Description} |
| `-silent` | Boolean | False | If true, Tux will not attempt to DM the user. |

### --{FLAG_NAME}

{Detailed description of the flag}

- **Type:** {TYPE}
- **Default:** {DEFAULT_VALUE}
- **Usage:** {How to use this flag}
- **Examples:**

  ```text
  /command @user --{FLAG_NAME} value
  $command @user --{FLAG_NAME} value
  ```

## Permissions

<!--
PERMISSIONS SECTION
Document both bot permissions and user permissions required.
Be specific about permission levels or ranks if applicable.
-->

### Bot Permissions

Tux requires the following permissions to execute this command:

- **{PERMISSION_NAME}** - {Why it's needed}
- **{PERMISSION_NAME}** - {Why it's needed}

### User Permissions

Users need {PERMISSION_LEVEL} or higher to use this command.

!!! info "Permission System"
    Command permissions are configured per-guild using Tux's dynamic permission system. Configure via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Usage Examples

<!--
USAGE EXAMPLES SECTION
Provide 2-4 practical examples showing different use cases.
Include both simple and complex examples.
Show basic usage, usage with parameters, usage with flags, and advanced usage if applicable.
-->

### Basic Usage

{Simple, most common use case}

```text
/{COMMAND_NAME} @user
```

{What happens when this is executed}

### With Parameters

{Example with additional parameters}

```text
/{COMMAND_NAME} @user parameter value
```

{What happens when this is executed}

### With Flags

<!-- Remove this subsection if no flags exist -->

{Example using flags}

```text
/{COMMAND_NAME} @user --{FLAG_NAME} value
```

{What happens when this is executed}

### Advanced Usage

{Complex example showing multiple parameters/flags}

```text
/{COMMAND_NAME} @user parameter --{FLAG_NAME} value --{FLAG_NAME2} value
```

{What happens when this is executed}

## Response

<!--
RESPONSE SECTION
Describe what users see when the command executes successfully.
Include examples of embeds, messages, or other output if applicable.
-->

When executed successfully, this command {description of response}.

{Example of what the response looks like - embed, message, action taken, etc.}

## Error Handling

<!--
ERROR HANDLING SECTION
Document common errors users might encounter.
Include error messages and how to resolve them.
If errors are straightforward or uncommon, you can simplify this section.
-->

### Common Errors

#### Error: {ERROR_NAME}

**When it occurs:** {Circumstances that trigger this error}

**Error message:**

```text
{Actual or example error message}
```

**Solution:** {How to fix it}

## Behavior Notes

<!--
BEHAVIOR NOTES SECTION
Only include this section if the command has important behavioral notes.
Document cooldowns, rate limits, special behaviors, or edge cases.
If not applicable, remove this section.
-->

- **{BEHAVIOR_NOTE}:** {Description}
- **{BEHAVIOR_NOTE}:** {Description}

!!! tip "Tip"
    {Helpful tip about using this command effectively}

!!! warning "Warning"
    {Important warning about using this command}

## Configuration

<!--
CONFIGURATION SECTION
Only include this section if the command behavior can be configured.
If no configuration options exist, remove this entire section.

Document configuration options that affect this command's behavior.
Link to configuration guides if applicable.
-->

This command's behavior can be configured via {CONFIGURATION_METHOD}:

- **{SETTING_NAME}:** {Description and effect on command behavior}
- **{SETTING_NAME}:** {Description and effect on command behavior}

!!! info "Configuration Guide"
    See the [Configuration Guide](../../../admin/config/{RELATED_CONFIG}.md) for detailed setup instructions.

## Related Commands

<!--
RELATED COMMANDS SECTION
Link to related commands that users might also need.
Help users discover related functionality.
-->

- [`{RELATED_COMMAND}`](path/to/command.md) - {Brief description}
- [`{RELATED_COMMAND}`](path/to/command.md) - {Brief description}
