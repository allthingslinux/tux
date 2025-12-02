---
title: Environment Variables
hide:
  - toc
tags:
  - env
  - configuration
  - settings
  - environment
  - pydantic-settings
  - dotenv
  - env-variables
---
<!-- region:config -->
# Environment Variables

## Config

Main Tux configuration using Pydantic Settings with multi-format support.

Configuration is loaded from multiple sources in priority order:

1. Environment variables (highest priority)
2. .env file
3. config.toml file
4. config.yaml file
5. config.json file
6. Default values (lowest priority)

| Name                   | Type      | Default                             | Description                                                           | Example                                                     |
|------------------------|-----------|-------------------------------------|-----------------------------------------------------------------------|-------------------------------------------------------------|
| `DEBUG`                | `boolean` | `false`                             | Enable debug mode                                                     | `false`, `true`                                             |
| `LOG_LEVEL`            | `string`  | `"INFO"`                            | Logging level (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL) | `"INFO"`, `"DEBUG"`, `"WARNING"`, `"ERROR"`                 |
| `BOT_TOKEN`            | `string`  | `""`                                | Discord bot token                                                     | `"FakeDiscordBotTokenBecauseGitHubSecurityIsAnnoying"`      |
| `POSTGRES_HOST`        | `string`  | `"localhost"`                       | PostgreSQL host                                                       | `"localhost"`, `"tux-postgres"`, `"db.example.com"`         |
| `POSTGRES_PORT`        | `integer` | `5432`                              | PostgreSQL port                                                       | `5432`, `5433`                                              |
| `POSTGRES_DB`          | `string`  | `"tuxdb"`                           | PostgreSQL database name                                              | `"tuxdb"`, `"tux_production"`                               |
| `POSTGRES_USER`        | `string`  | `"tuxuser"`                         | PostgreSQL username                                                   | `"tuxuser"`, `"tux_admin"`                                  |
| `POSTGRES_PASSWORD`    | `string`  | `"ChangeThisToAStrongPassword123!"` | PostgreSQL password                                                   | `"ChangeThisToAStrongPassword123!"`, `"SecurePassword456!"` |
| `DATABASE_URL`         | `string`  | `""`                                | Custom database URL override                                          | `"postgresql://user:password@localhost:5432/tuxdb"`         |
| `ALLOW_SYSADMINS_EVAL` | `boolean` | `false`                             | Allow sysadmins to use eval                                           | `false`, `true`                                             |

### BotInfo

Bot information configuration.

**Environment Prefix**: `BOT_INFO__`

| Name                       | Type      | Default | Description         | Example                                                                                                                               |
|----------------------------|-----------|---------|---------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| `BOT_INFO__BOT_NAME`       | `string`  | `"Tux"` | Name of the bot     | `"Tux"`, `"MyBot"`                                                                                                                    |
| `BOT_INFO__ACTIVITIES`     | `string`  | `"[]"`  | Bot activities      | `"[{\"type\": 0, \"name\": \"with Linux\"}]"`, `"[{\"type\": 2, \"name\": \"to commands\", \"url\": \"https://twitch.tv/example\"}]"` |
| `BOT_INFO__HIDE_BOT_OWNER` | `boolean` | `false` | Hide bot owner info | `false`, `true`                                                                                                                       |
| `BOT_INFO__PREFIX`         | `string`  | `"$"`   | Command prefix      | `"$"`, `"!"`, `"tux."`, `"?"`                                                                                                         |

### UserIds

User ID configuration.

**Environment Prefix**: `USER_IDS__`

| Name                     | Type      | Default | Description           | Example                                   |
|--------------------------|-----------|---------|-----------------------|-------------------------------------------|
| `USER_IDS__BOT_OWNER_ID` | `integer` | `0`     | Bot owner user ID     | `123456789012345678`                      |
| `USER_IDS__SYSADMINS`    | `array`   | `[]`    | System admin user IDs | `[123456789012345678,987654321098765432]` |

### StatusRoles

Status roles configuration.

**Environment Prefix**: `STATUS_ROLES__`

| Name                     | Type    | Default | Description             | Example                                                 |
|--------------------------|---------|---------|-------------------------|---------------------------------------------------------|
| `STATUS_ROLES__MAPPINGS` | `array` | `[]`    | Status to role mappings | `[{"status":".gg/linux","role_id":123456789012345678}]` |

### TempVC

Temporary voice channel configuration.

**Environment Prefix**: `TEMPVC__`

| Name                         | Type                   | Default | Description              | Example                |
|------------------------------|------------------------|---------|--------------------------|------------------------|
| `TEMPVC__TEMPVC_CHANNEL_ID`  | `string` \| `NoneType` | `null`  | Temporary VC channel ID  | `"123456789012345678"` |
| `TEMPVC__TEMPVC_CATEGORY_ID` | `string` \| `NoneType` | `null`  | Temporary VC category ID | `"123456789012345678"` |

### GifLimiter

GIF limiter configuration.

**Environment Prefix**: `GIF_LIMITER__`

| Name                              | Type      | Default | Description          | Example                      |
|-----------------------------------|-----------|---------|----------------------|------------------------------|
| `GIF_LIMITER__RECENT_GIF_AGE`     | `integer` | `60`    | Recent GIF age limit | `60`, `120`, `300`           |
| `GIF_LIMITER__GIF_LIMITS_USER`    | `object`  | `{}`    | User GIF limits      | `{'123456789012345678': 5}`  |
| `GIF_LIMITER__GIF_LIMITS_CHANNEL` | `object`  | `{}`    | Channel GIF limits   | `{'123456789012345678': 10}` |
| `GIF_LIMITER__GIF_LIMIT_EXCLUDE`  | `array`   | `[]`    | Excluded channels    | `[123456789012345678]`       |

### XP

XP system configuration.

**Environment Prefix**: `XP_CONFIG__`

| Name                               | Type      | Default | Description            | Example                                               |
|------------------------------------|-----------|---------|------------------------|-------------------------------------------------------|
| `XP_CONFIG__XP_BLACKLIST_CHANNELS` | `array`   | `[]`    | XP blacklist channels  | `[123456789012345678]`                                |
| `XP_CONFIG__XP_ROLES`              | `array`   | `[]`    | XP roles               | `[{"role_id":123456789012345678,"xp_required":1000}]` |
| `XP_CONFIG__XP_MULTIPLIERS`        | `array`   | `[]`    | XP multipliers         | `[{"role_id":123456789012345678,"multiplier":1.5}]`   |
| `XP_CONFIG__XP_COOLDOWN`           | `integer` | `1`     | XP cooldown in seconds | `1`, `5`, `10`                                        |
| `XP_CONFIG__LEVELS_EXPONENT`       | `integer` | `2`     | Levels exponent        | `2`, `3`, `1.5`                                       |
| `XP_CONFIG__SHOW_XP_PROGRESS`      | `boolean` | `true`  | Show XP progress       | `true`, `false`                                       |
| `XP_CONFIG__ENABLE_XP_CAP`         | `boolean` | `false` | Enable XP cap          | `false`, `true`                                       |

### Snippets

Snippets configuration.

**Environment Prefix**: `SNIPPETS__`

| Name                          | Type      | Default | Description                      | Example                                   |
|-------------------------------|-----------|---------|----------------------------------|-------------------------------------------|
| `SNIPPETS__LIMIT_TO_ROLE_IDS` | `boolean` | `false` | Limit snippets to specific roles | `false`, `true`                           |
| `SNIPPETS__ACCESS_ROLE_IDS`   | `array`   | `[]`    | Snippet access role IDs          | `[123456789012345678,987654321098765432]` |

### IRC

IRC bridge configuration.

**Environment Prefix**: `IRC_CONFIG__`

| Name                             | Type    | Default | Description            | Example                |
|----------------------------------|---------|---------|------------------------|------------------------|
| `IRC_CONFIG__BRIDGE_WEBHOOK_IDS` | `array` | `[]`    | IRC bridge webhook IDs | `[123456789012345678]` |

### ExternalServices

External services configuration.

**Environment Prefix**: `EXTERNAL_SERVICES__`

| Name                                        | Type     | Default | Description             | Example                                                |
|---------------------------------------------|----------|---------|-------------------------|--------------------------------------------------------|
| `EXTERNAL_SERVICES__SENTRY_DSN`             | `string` | `""`    | Sentry DSN              | `"https://key@o123456.ingest.sentry.io/123456"`        |
| `EXTERNAL_SERVICES__GITHUB_APP_ID`          | `string` | `""`    | GitHub app ID           | `"123456"`                                             |
| `EXTERNAL_SERVICES__GITHUB_INSTALLATION_ID` | `string` | `""`    | GitHub installation ID  | `"12345678"`                                           |
| `EXTERNAL_SERVICES__GITHUB_PRIVATE_KEY`     | `string` | `""`    | GitHub private key      | `"-----BEGIN RSA PRIVATE KEY-----\n..."`               |
| `EXTERNAL_SERVICES__GITHUB_CLIENT_ID`       | `string` | `""`    | GitHub client ID        | `"Iv1.1234567890abcdef"`                               |
| `EXTERNAL_SERVICES__GITHUB_CLIENT_SECRET`   | `string` | `""`    | GitHub client secret    | `"1234567890abcdef1234567890abcdef12345678"`           |
| `EXTERNAL_SERVICES__GITHUB_REPO_URL`        | `string` | `""`    | GitHub repository URL   | `"https://github.com/owner/repo"`                      |
| `EXTERNAL_SERVICES__GITHUB_REPO_OWNER`      | `string` | `""`    | GitHub repository owner | `"owner"`                                              |
| `EXTERNAL_SERVICES__GITHUB_REPO`            | `string` | `""`    | GitHub repository name  | `"repo"`                                               |
| `EXTERNAL_SERVICES__MAILCOW_API_KEY`        | `string` | `""`    | Mailcow API key         | `"abc123def456ghi789"`                                 |
| `EXTERNAL_SERVICES__MAILCOW_API_URL`        | `string` | `""`    | Mailcow API URL         | `"https://mail.example.com/api/v1"`                    |
| `EXTERNAL_SERVICES__WOLFRAM_APP_ID`         | `string` | `""`    | Wolfram Alpha app ID    | `"ABC123-DEF456GHI789"`                                |
| `EXTERNAL_SERVICES__INFLUXDB_TOKEN`         | `string` | `""`    | InfluxDB token          | `"abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"` |
| `EXTERNAL_SERVICES__INFLUXDB_URL`           | `string` | `""`    | InfluxDB URL            | `"https://us-east-1-1.aws.cloud2.influxdata.com"`      |
| `EXTERNAL_SERVICES__INFLUXDB_ORG`           | `string` | `""`    | InfluxDB organization   | `"my-org"`                                             |
<!-- endregion:config -->
