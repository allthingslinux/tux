# Advanced Configuration

Optional integrations and advanced features.

## Sentry Integration

Error tracking and performance monitoring.

**Setup:**

1. Create project at [sentry.io](https://sentry.io)
2. Get DSN from project settings
3. Add to `.env`:

```bash
EXTERNAL_SERVICES__SENTRY_DSN=https://xxx@sentry.io/123
```

**Features:**

- Error tracking
- Performance tracing
- Release tracking
- User feedback

**See:** [Sentry Integration Guide](../../developer-guide/core-systems/sentry-integration.md)

## InfluxDB Metrics

Time-series metrics collection.

**Setup:**

```bash
EXTERNAL_SERVICES__INFLUXDB_URL=http://influxdb:8086
EXTERNAL_SERVICES__INFLUXDB_TOKEN=your_token
EXTERNAL_SERVICES__INFLUXDB_ORG=your_org
```

**Metrics Collected:**

- Guild count
- User count
- Message count
- Command usage
- Performance metrics

## GitHub Integration

For GitHub-related features (ATL-specific).

```bash
EXTERNAL_SERVICES__GITHUB_APP_ID=123456
EXTERNAL_SERVICES__GITHUB_INSTALLATION_ID=789012
EXTERNAL_SERVICES__GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n..."
EXTERNAL_SERVICES__GITHUB_REPO_OWNER=org
EXTERNAL_SERVICES__GITHUB_REPO=repo
```

## Wolfram Alpha

For `/wolfram` command:

```bash
EXTERNAL_SERVICES__WOLFRAM_APP_ID=YOUR-APP-ID
```

Get App ID: [developer.wolframalpha.com](https://developer.wolframalpha.com/)

## Plugin System

Custom plugins in `src/tux/plugins/`.

**ATL Plugins** (All Things Linux specific):

- deepfry - Image effects
- fact - Random facts
- flagremover - Auto-moderation
- git - GitHub integration
- harmfulcommands - Fun commands
- mail - Mail system integration
- mock - Text transformation
- rolecount - Role statistics
- supportnotifier - Support notifications
- tty_roles - TTY role management

**Custom Plugins:**

Create in `src/tux/plugins/your_plugin/` and follow plugin structure.

**See:** Plugin README at `src/tux/plugins/README.md`

## IRC Bridge

```bash
IRC_CONFIG__BRIDGE_WEBHOOK_IDS=[webhook_id1, webhook_id2]
```

## Related

- **[Plugin System](../../developer-guide/core-systems/plugin-system.md)**
- **[Configuration Reference](../../reference/configuration.md)**

---

*Full advanced configuration documentation in progress.*
