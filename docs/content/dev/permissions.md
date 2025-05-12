# Permissions Management

Tux employs a level-based permissions system to control command execution.

Each command is associated with a specific permission level, ensuring that only users with the necessary clearance can execute it.

## Initial Setup

When setting up Tux for a new server, the server owner can assign one or multiple roles to each permission level. Users then inherit the highest permission level from their assigned roles.

For instance, if a user has one role with a permission level of 2 and another with a level of 3, their effective permission level will be 3.

## Advantages

The level-based system allows Tux to manage command execution efficiently across different servers.

It offers a more flexible solution than just relying on Discord's built-in permissions, avoiding the need to hardcode permissions into the bot.

This flexibility makes it easier to modify permissions without changing the bot’s underlying code, accommodating servers with custom role names seamlessly.

## Available Permission Levels

Below is the hierarchy of permission levels available in Tux:

- **0: Member**
- **1: Support**
- **2: Junior Moderator**
- **3: Moderator**
- **4: Senior Moderator**
- **5: Administrator**
- **6: Head Administrator**
- **7: Server Owner** (Not the actual discord assigned server owner)
- **8: Sys Admin** (User ID list in `config/settings.yml`)
- **9: Bot Owner** (User ID in `config/settings.yml`)

By leveraging these permission levels, Tux provides a robust and adaptable way to manage who can execute specific commands, making it suitable for various server environments.
