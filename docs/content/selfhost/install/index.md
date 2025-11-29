---
title: Installation
tags:
  - selfhost
  - installation
---

# Installation

Review the below information and pick the installation method that best suits your environment.

## 1. Review Requirements

These are the system requirements needed to install and run Tux.

### Minimum Requirements

- **OS**: Any
- **RAM**: 512MB
- **Storage**: 2GB free space

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

- **Bot Token**: Read [our guide](../config/bot-token.md) on obtaining a bot token.
- **Permissions**: Administrator or specific permissions as needed
- **Server Access**: Bot must be invited to target servers

## 2. Database Setup

Refer to the [Database Installation](database.md) guide to setup the PostgreSQL database before proceeding with the installation.

## 3. Choose Installation Method

Choose one of the following installation methods:

- [Docker Installation](docker.md) - Recommended for most users
- [Systemd Installation](systemd.md) - For non-Docker setups

## 4. First Run

After installation, follow the [First Run Setup](first-run.md) guide to complete the initial configuration and get Tux running.
