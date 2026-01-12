---
title: Cases
description: View and manage server moderation cases
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - command-groups
  - moderation
---

# Cases

The `cases` command group is the central hub for Tux's moderation tracking system. Every moderation action taken by Tux (bans, warns, timeouts, etc.) is recorded as a "case" in the database.

This command group allows moderators to review history, search for specific incidents, and update case information as situations evolve.

By maintaining a rigorous record of all actions, `cases` ensures accountability and helps moderators track repeat offenders across long periods of time.

## Base Command

The base `cases` command provides a paginated overview of all moderation cases in the server, or can be used to quickly view a single case by number.

**Syntax:**

```text
/cases [case_number]
$cases [case_number]
$case [case_number]
$c [case_number]
```

**Aliases:**

You can also use these aliases instead of `cases`:

- `case`
- `c`

When invoked without a subcommand or case number, Tux opens an interactive menu displaying all cases in descending order (newest first).

## Subcommands

| Subcommand | Aliases | Description | Usage |
|------------|--------|-------------|-------|
| `view` | `v`, `show`, `get`, `list` | View a specific case by number | `/cases view case_number:123` |
| `search` | `filter`, `find` | Filter cases by user, moderator, or type | `/cases search user:@user` |
| `modify` | `m`, `edit`, `update` | Update a case's reason or status | `/cases modify case_number:123 reason:"New reason"` |

### Category: Case Management

#### view

Detailed display of a single moderation incident, including the target, the moderator, the original reason, and any expiration dates.

**Syntax:**

```text
/cases view case_number:NUMBER
$cases view NUMBER
$cases v NUMBER
$cases show NUMBER
$cases get NUMBER
$cases list NUMBER
```

**Aliases:**

- `v`, `show`, `get`, `list`

**Parameters:**

- `case_number` - The unique integer identifying the case.

**Example:**

```text
/cases view case_number:42
```

#### search

Find specific cases based on filtering criteria. You can combine multiple flags to narrow down your search.

**Syntax:**

```text
/cases search [user:@user] [mod:@moderator] [type:TYPE]
$cases search [-user @user] [-mod @moderator] [-type TYPE]
$cases filter [-user @user] [-mod @moderator] [-type TYPE]
$cases find [-user @user] [-mod @moderator] [-type TYPE]
```

**Aliases:**

- `filter`, `find`

**Parameters (Flags):**

- `-user` - Filter by the user who received the action.
- `-mod` - Filter by the moderator who took the action.
- `-type` - Filter by the action type (e.g., `ban`, `warn`).

**Example:**

```text
/cases search user:@ProblemUser type:warn
```

#### modify

Allows moderators to update existing cases. This is commonly used to add more detail to a reason after an investigation or to change the status of a case.

**Syntax:**

```text
/cases modify case_number:NUMBER reason:STRING [status:active/inactive]
$cases modify NUMBER [-reason "New reason"] [-status active/inactive]
$cases m NUMBER [-reason "New reason"] [-status active/inactive]
$cases edit NUMBER [-reason "New reason"] [-status active/inactive]
$cases update NUMBER [-reason "New reason"] [-status active/inactive]
```

**Aliases:**

- `m`, `edit`, `update`

**Parameters (Flags):**

- `-reason` - Update the reason text.
- `-status` - Manually set the status (active/inactive).

**Example:**

```text
/cases modify case_number:123 reason:"Updated: User appealed and was unbanned early"
```

## Common Workflows

### Workflow: Reviewing User History

Checking if a user has a history of similar violations before taking action.

**Steps:**

1. Use `/cases search user:@user` to view their full history.
2. Use `/cases view case_number:NUMBER` to read the details of specific past warnings.
3. Determine if the new violation warrants a more severe action based on their patterns.

## Permissions

### Bot Permissions

Tux requires the following permissions:

- **Send Messages** - To display case information.
- **Embed Links** - To format cases into readable embeds.

### User Permissions

Users need Moderator rank or higher to use commands in this group.

!!! info "Permission System"
    Configure command permissions via `/config commands` or see the [Permission Configuration](../../../admin/config/commands.md) guide.

## Response Format

Subcommands generally result in:

- **`view`** - A detailed embed showing the incident details, including case number, target user, moderator, reason, timestamp, and case type
- **`search`/base command** - An interactive paginated menu with buttons to navigate through case history, showing multiple cases per page
- **`modify`** - A confirmation embed showing the updated case details and a real-time update to the original moderation log entry

The base command (without subcommand) opens an interactive dashboard showing all cases in descending order (newest first) with pagination controls.

## Error Handling

### Common Errors

#### Case Not Found

**When it occurs:** You provide a case number that does not exist in the database.

**What happens:** The bot sends an error message indicating the case number is invalid.

**Solutions:**

- Check the case number and try again
- Use `/cases search` to find valid case numbers
- Check the moderation logs for the correct case number
- Verify you're searching in the correct server (cases are server-specific)

#### Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than required to view or modify cases.

**What happens:** The bot sends an error message indicating you don't have permission to use this command.

**Solutions:**

- Contact a server administrator to check your current rank
- Adjust the command configurations via `/config commands` if you have admin access

## Related Documentation

- [Moderation Module](index.md)
- [Ban Command](ban.md)
- [Warn Command](warn.md)
- [Timeout Command](timeout.md)
