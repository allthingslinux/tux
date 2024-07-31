# Services

## Overview

Services within the context of this bot are background tasks that run continuously and provide various functionalities to the server. They are typically not directly interacted with by users, but rather provide additional features to the server that are not covered by commands.

## Available Services

- **TTY Roles**: Assigns roles to users based on the member count of the server to act as a vanity metric for how long a user has been a member of the server.
- **Harmful Message Detection**: Detects harmful CLI commands in messages and warns users about them.
- **Temp Voice Channels**: Automatically creates temporary voice channels for users to use and deletes them when they are empty.

## Planned Services

- **Auto Welcome**: Sends a welcome message to new members when they join the server.
- **Auto Role**: Assigns a role to new members when they join the server.
- **Auto Mod**: Automatically moderates the server by enforcing rules and restrictions
- **Auto Unban**: Automatically unbans users after a specified duration