---
title: Jail Configuration
tags:
  - admin-guide
  - configuration
  - jail
---

# Jail

Configure the jail channel and jail role required for the `/jail` and `/unjail` moderation commands.

## Prerequisites

- **Manage Roles** – The bot needs this to assign and remove the jail role.

## Configuration

### Using the dashboard

1. Run `/config jail` or open the [Admin Configuration](index.md) and use **Jail** → **Open**.
2. **Jail channel** – Choose the text channel where jailed members can talk. This is the only channel they can access while jailed.
3. **Jail role** – Choose the role applied to jailed members. It should have *View* (and usually *Send messages*) denied on all channels except the jail channel.

To clear a setting, open the dropdown and deselect the current value (or choose nothing).

### Channel and role setup

1. Create a **jail** text channel (e.g. `#jail`).
2. Create a **Jail** role. Place it below the bot’s top role so the bot can assign it.
3. On **every other channel**: channel settings → Permissions → add the Jail role → deny *View channel* (and *Send messages* if you prefer).
4. On the jail channel: ensure the Jail role has *View channel* and *Send messages* (and any other permissions you want jailed users to have).
5. Use `/config jail` to set the **Jail channel** and **Jail role** to those.

!!! tip "New channels"
    When a new channel is created, Tux automatically denies the jail role access to it. You only need to manually allow the jail role on the jail channel.

## See also

- [Jail command](../../user/modules/moderation/jail.md) – Restrict a member to the jail channel
- [Unjail command](../../user/modules/moderation/unjail.md) – Release a member from jail
