---
title: Report
description: Anonymously report a user or incident to server moderators
icon: lucide/square-slash
tags:
  - user-guide
  - commands
  - moderation
---

# Report

The `report` command provides a safe and anonymous way for community members to alert server moderators to potential rule violations, harassment, or other issues.

Unlike public reports, this command opens a private interface that only the reporter sees, and the final report is sent to a private moderation channel.

## Syntax

The `report` command is available **only as a Slash Command** to ensure user privacy and support the interactive modal interface.

**Slash Command:**

```text
/report
```

## How It Works

When you run `/report`, Tux will open a pop-up window (modal) with several fields for you to fill out:

1. **Subject:** A brief title for your report.
2. **User(s) Involved:** The name or ID of the user(s) you are reporting.
3. **Details:** A thorough description of the incident or behavior.
4. **Evidence:** Links to message IDs, screenshots (uploaded elsewhere), or other proof.

Once you submit the modal, Tux will:

- Validate that all required information is present.
- Format your report into an embed.
- Post the report into the server's designated **Mod Log** or **Report Channel**.
- Send you a private confirmation that your report was received.

## Permissions

### Bot Permissions

Tux requires the following permissions:

- **Send Messages** - In the designated report/log channel.
- **Embed Links** - To format the report for moderators.

### User Permissions

This command is typically available to **all server members** by default.

!!! info "Permission System"
    Server administrators can restrict who can use the report command via Tux's dynamic permission system. Configure via `/config commands`.

## Usage Examples

### Starting a Report

```text
/report
```

*This will immediately open the report interface on your screen.*

## Response Format

Upon successful submission, you will receive an ephemeral message:
> "Thank you for the report! It has been sent to the moderation team."

Your name is included in the report sent to moderators, but it is **not** visible to the user you are reporting or anyone else in the public channels.

The report is formatted as an embed in the designated moderation log channel, containing all the information you provided in the modal (subject, users involved, details, and evidence).

## Error Handling

### Common Errors

#### Modal Failed to Open

**When it occurs:** You run the command but nothing happens, or an error says the interaction failed.

**What happens:** The modal interface doesn't appear, or an error message is shown.

**Solutions:**

- Ensure you are using a modern Discord client that supports modals
- Try restarting your Discord app or running the command again
- Check your internet connection and Discord's service status
- Verify you have permission to use the report command

#### Report Channel Not Found

**When it occurs:** The bot attempts to post the report but the server's designated report/log channel has not been configured.

**What happens:** The bot sends an error message indicating the report channel is not configured.

**Solutions:**

- Contact a server administrator to ensure the moderation log channel is set correctly in Tux's configuration
- The report is still saved, but moderators won't receive it until the channel is configured
- See the [Configuration Guide](../../../admin/config/index.md) for setup instructions

## Related Documentation

- [Moderation Module](index.md)
- [Configuration Guide](../../../admin/config/index.md) - Learn how to set up the report channel.
