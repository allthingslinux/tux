---
title: Self-Hoster Guide
tags:
  - selfhost
icon: material/server-outline
---

# Self-Hoster Guide

Welcome to the Tux self-hosting guide. Follow the steps below to set up and manage your own instance of Tux.

## 1. Review Requirements

These are the system requirements needed to install and run Tux.

### Minimum Requirements

- **OS**: Any
- **RAM**: 512MB
- **Storage**: 4GB free space

### Recommended Requirements

- **OS**: Linux
- **RAM**: 2GB+
- **Storage**: 5GB+ free space

### Software Dependencies

#### Required

- **Python**: 3.13+
- **uv**: Project management tool
- **Git**: For cloning the repository
- **Docker or Podman**: For containerized deployment (optional)

!!! note "Note"
    If you use Docker or Podman, also install Docker Compose V2 or Podman Compose.

#### Database

- **PostgreSQL**: 17+ (required)

!!! tip "Tip"
    If you don't want to manage the database yourself, consider using a managed PostgreSQL service such as [Supabase](https://supabase.com/).

### Discord Bot Requirements

- **Bot Token**: Read [our guide](./config/bot-token.md) on obtaining a bot token.
- **Permissions**: Administrator or specific permissions as needed
- **Server Access**: Bot must be invited to target servers

## 2. Choose Installation Method

Choose the installation method that best suits your environment:

- [Docker Installation](./install/docker.md) - **Recommended.** Uses Docker Compose to manage the bot and database.
- [Bare Metal Installation](./install/baremetal.md) - Manual installation using systemd and a local PostgreSQL instance.

## 3. First Run

After installation, follow the [First Run Setup](./install/first-run.md) guide to complete the initial configuration and get Tux running.

## Next Steps

- [Configuration Guide](./config/index.md) - Customize Tux to your needs.
- [Management Guide](./manage/index.md) - Essential information for ongoing maintenance and operations.
