# Tux

<div class="hero">
  <div class="hero-content">
    <h1 class="hero-title">All-in-One Discord Bot for Linux Communities</h1>
    <p class="hero-description">
      Tux is a powerful, feature-rich Discord bot built with Python 3.13+ and designed for the All Things Linux community.
      Choose your path below to get started.
    </p>
  </div>
</div>

## Choose Your Path

<div class="audience-grid">
  <div class="audience-card">
    <div class="audience-icon">👥</div>
    <h3>For Users</h3>
    <p>Learn how to use Tux commands and features in your Discord server.</p>
    <a href="getting-started/for-users/" class="btn btn-primary">User Guide</a>
  </div>
  
  <div class="audience-card">
    <div class="audience-icon">🚀</div>
    <h3>For Self-Hosters</h3>
    <p>Deploy and manage your own Tux instance.</p>
    <a href="getting-started/for-self-hosters/" class="btn btn-primary">Admin Guide</a>
  </div>
  
  <div class="audience-card">
    <div class="audience-icon">💻</div>
    <h3>For Developers</h3>
    <p>Contribute to Tux development and build new features.</p>
    <a href="getting-started/for-developers/" class="btn btn-primary">Developer Guide</a>
  </div>
</div>

## Quick Links

### 📚 Documentation

- **[User Guide](user-guide/)** - Commands, features, and permissions
- **[Admin Guide](admin-guide/)** - Deployment, configuration, and operations
- **[Developer Guide](developer-guide/)** - Architecture, patterns, and contributing
- **[API Reference](reference/api/)** - Complete code documentation
- **[CLI Reference](reference/cli/)** - Command-line tools

### 🎯 Popular Topics

- [Getting Started](getting-started/) - Choose your path
- [Command Reference](user-guide/commands/moderation/) - All available commands
- [Docker Deployment](admin-guide/deployment/docker-compose/) - Recommended deployment method
- [Development Setup](developer-guide/getting-started/development-setup/) - Set up your dev environment
- [Permission System](user-guide/permissions/) - Understanding Tux permissions

### 🤝 Community

- **[Discord Server](https://discord.gg/gpmSjcjQxg)** - Get support and discuss features
- **[GitHub Repository](https://github.com/allthingslinux/tux)** - Source code and issues
- **[Contributing Guide](community/contributing/)** - How to contribute

## Features

<div class="feature-grid">
  <div class="feature-card">
    <div class="feature-icon">🛡️</div>
    <h3>Advanced Moderation</h3>
    <p>Comprehensive tools including ban, kick, timeout, jail system, and case management.</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">⚡</div>
    <h3>High Performance</h3>
    <p>Built with async Python, optimized for large servers with hot-reload for development.</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🎮</div>
    <h3>XP & Leveling</h3>
    <p>Engaging XP system with ranks, leaderboards, and customizable role rewards.</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔧</div>
    <h3>Highly Configurable</h3>
    <p>Flexible configuration with env/TOML/YAML/JSON support and interactive setup wizard.</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">📊</div>
    <h3>Rich Analytics</h3>
    <p>Detailed logging with Loguru, Sentry integration, and optional InfluxDB metrics.</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔌</div>
    <h3>Plugin System</h3>
    <p>Extensible architecture with custom plugins for server-specific features.</p>
  </div>
</div>

## Tech Stack

Tux is built with modern technologies and best practices:

- **Python 3.13+** with `discord.py` for Discord API integration
- **UV** for fast, reliable dependency management
- **SQLModel + SQLAlchemy** for type-safe database operations with PostgreSQL
- **Alembic** for database migrations
- **Docker Compose** for easy deployment with Adminer web UI
- **Typer** for powerful CLI tools
- **Ruff** for linting and formatting
- **Basedpyright** for strict type checking
- **Loguru** for structured logging
- **Sentry** for error tracking and performance monitoring

## About This Documentation

This documentation is organized by audience:

- **User Guide**: For Discord server admins and users learning Tux commands
- **Admin Guide**: For self-hosters deploying and operating Tux instances
- **Developer Guide**: For contributors building features and fixing bugs
- **Reference**: Auto-generated API and CLI documentation

Choose your path above to get started, or explore the navigation menu.

---

**Current Version**: See [VERSIONING.md](https://github.com/allthingslinux/tux/blob/main/VERSIONING.md) for version information.

**License**: GNU General Public License v3.0 - See [LICENSE](https://github.com/allthingslinux/tux/blob/main/LICENSE)

*Tux is open source and maintained by the All Things Linux community. Contributions welcome!*
