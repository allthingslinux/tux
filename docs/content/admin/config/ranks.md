---
title: Ranks Configuration
tags:
  - admin-guide
  - configuration
  - ranks
---

# Ranks Configuration

Permission ranks form the foundation of Tux's access control system. This guide covers how to set up and manage permission ranks for your Discord server.

## Overview

Permission ranks create a hierarchy from 0 (lowest) to 10 (highest). Higher ranks automatically inherit access to everything lower ranks can do.

## Setting Up Default Ranks

### Using the Dashboard (Recommended)

1. Run `/config ranks` to open the ranks configuration dashboard
2. If no ranks exist, you'll see an "🚀 Init Default Ranks" button
3. Click the button to create the standard 8 ranks (0-7)
4. The dashboard will show all created ranks with their names and descriptions

### Using the Command

Alternatively, use `/config ranks init` in any text channel to create default ranks via command.

## Default Ranks

When you initialize ranks, these 8 default ranks are created:

- **Rank 0: Member** - Regular community member with standard access
- **Rank 1: Trusted** - Trusted community member
- **Rank 2: Junior Moderator** - Entry-level moderation role
- **Rank 3: Moderator** - Standard moderation permissions
- **Rank 4: Senior Moderator** - Experienced moderators with additional oversight
- **Rank 5: Administrator** - Administrative permissions
- **Rank 6: Head Administrator** - High-level administrators
- **Rank 7: Server Owner** - Server owner (highest default rank)

## Managing Custom Ranks

After setting up default ranks, you can create custom ranks (8-10) for specialized roles:

1. In the ranks dashboard, click "+ Create Rank"
2. Choose a rank number between 8-10
3. Enter a name and description
4. The rank will appear in the dashboard

## Best Practices

- **Start with defaults**: Use the initialization feature to get started quickly
- **Customize as needed**: Modify rank names and descriptions to fit your community
- **Plan your hierarchy**: Think about your server's structure before creating custom ranks
- **Document changes**: Keep track of what each rank is used for

## Troubleshooting

### Ranks Don't Appear

If ranks don't show up after initialization:

- Check that you're a server administrator
- Try refreshing the dashboard
- Verify the bot has proper permissions

### Can't Create Custom Ranks

If you can't create ranks 8-10:

- Ensure ranks 0-7 exist first
- Check that the rank number isn't already taken
- Verify you have administrator permissions

## Related Configuration

- **[Role Assignments](./roles.md)** - Map Discord roles to permission ranks
- **[Command Permissions](./commands.md)** - Set rank requirements for commands
- **[Permission System](../../developer/concepts/core/permission-system.md)** - Technical details
