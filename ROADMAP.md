# Roadmap

This roadmap is a living document that will be updated as the project evolves. It is not a commitment to deliver any specific features or changes, but rather a guide for the project's direction. For more detailed information and updates, please refer to the [CHANGELOG](CHANGELOG.md).

## v0.1.0 - First Major Release

**Status**: Feature complete, final testing phase

- [x] Asynchronous architecture with hybrid commands (slash + prefix)
- [x] Cog loading with hot reload, branded embeds, comprehensive error handling
- [x] Activity rotation, custom help command, dynamic permission system
- [x] Multi-format configuration (TOML/YAML/JSON), emoji management
- [x] Complete moderation suite (ban, kick, warn, timeout, tempban, jail, purge, slowmode)
- [x] Case management with viewing, searching, modification, and thread-safe numbering
- [x] XP/leveling, AFK, reminders, snippets, starboard, status roles
- [x] Bookmarks, temp voice channels, GIF limiting, InfluxDB logging
- [x] Documentation (MkDocs), Docker, CLI (Typer), testing (pytest + Codecov)
- [x] Pre-commit hooks, CI/CD, multi-platform Docker builds
- [x] Database migration (Prisma → SQLModel), package manager (Poetry → uv)
- [x] CLI framework (Click → Typer), type checker (pyright → basedpyright)
- [x] Project layout (flat → src), Alembic migrations
- [x] Plugin system: Deepfry, Flag Remover, Support Notifier, Harmful Commands, Fact, Role Count, TTY Roles, Git, Mail, Mock
- [ ] Final bug fixes, performance optimization, documentation review, release notes

---

## Backlog

> **Note**: The following items are under consideration for future releases. The roadmap will be redesigned after v0.1.0 release.

### Configuration & Multi-Guild

- Interactive configuration wizard, guild-specific feature toggles
- Configuration import/export, validation, migration tools
- Enhanced multi-guild optimization, per-guild feature flags and prefixes
- Cross-guild statistics and analytics

### Moderation Enhancements

- Multi-user moderation commands, bulk operations, templates
- Enhanced case search and filtering
- Improved error messages, command analytics

### Performance & Caching

- Redis integration for distributed caching
- Command cooldowns with Redis backend
- Permission, guild config, and user data caching with TTL
- Database query optimization, connection pooling improvements
- Async operation optimization, memory profiling
- Automated slowmode based on activity
- Auto-moderation triggers, scheduled tasks system

### Statistics & Tracking

- User activity and command usage statistics
- Server growth metrics, feature usage tracking
- Invite tracking with credit system
- Nickname and role change history
- Message edit/delete logging
- Statistical reports, visualizations, export functionality

### Auto-Moderation

- Regex-based content filtering, spam detection
- Heat system (escalating warnings), rate limiting
- Link filtering with whitelist, mention spam protection
- Raid protection, alt account detection
- Suspicious activity monitoring, automated restrictions

### External Integrations

- RSS subscription service with filtering and formatting
- Repology API integration for package search and updates
- GitHub webhooks, custom webhook support
- API endpoints for external services

### Economy & Engagement

- Virtual currency, wallets, transactions
- Shop system with purchasable items
- Daily rewards, streaks, achievements, badges
- Leaderboards, contests, giveaways, custom rewards

### Support & Ticketing

- Ticket creation, management, transcripts
- Category-based routing, staff assignment
- Ticket statistics and analytics
- FAQ system, auto-responses, priority levels

### Web Dashboard

- Authentication, guild management, real-time statistics
- Configuration management UI, moderation case viewer
- User management, log viewer, analytics
- Plugin management, RESTful API, WebSocket support

### Stable Release (v1.0.0)

- Comprehensive code review, security audit
- Performance benchmarking, load testing
- Documentation completeness, migration guides
- Discord verification, bot list submissions
- Public announcement, community server

### Future Considerations

- Voice features, AI/ML moderation, mobile app
- Multi-language support, advanced analytics
- Custom command builder, integration marketplace
