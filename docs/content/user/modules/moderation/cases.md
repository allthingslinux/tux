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
```

**Aliases:**

- `case`
- `c`

When invoked without a subcommand or case number, Tux opens an interactive menu displaying all cases in descending order (newest first).

## Subcommands

| Subcommand | Description | Usage |
|------------|-------------|-------|
| `view` | View a specific case by number | `/cases view case_number:123` |
| `search` | Filter cases by user, moderator, or type | `/cases search user:@user` |
| `modify` | Update a case's reason or status | `/cases modify case_number:123 reason:"New reason"` |

### Category: Case Management

#### view

Detailed display of a single moderation incident, including the target, the moderator, the original reason, and any expiration dates.

**Syntax:**

```text
/cases view case_number:NUMBER
$cases view NUMBER
```

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
```

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
```

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

## Response

Subcommands generally result in:

- **`view`:** A detailed embed showing the incident details.
- **`search`/`list`:** An interactive paginated menu with buttons to navigate through case history.
- **`modify`:** A confirmation embed showing the updated case details and a real-time update to the original moderation log entry.

## Error Handling

### Common Errors

#### Error: Case Not Found

**When it occurs:** You provide a case number that does not exist in the database.

**Solution:** Check the case number and try again. You can find case numbers in the `/cases search` list or in the moderation logs.

#### Error: Lacking Permission Rank

**When it occurs:** Your internal Tux permission rank is lower than required to view or modify cases.

**Solution:** Contact a server administrator to check your current rank.

## Related Documentation

- [Moderation Module](index.md)
- [Ban Command](ban.md)
- [Warn Command](warn.md)
