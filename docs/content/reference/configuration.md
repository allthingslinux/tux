# Configuration

Here you can find all available configuration options using ENV variables.

## Config

Main Tux configuration using Pydantic Settings with multi-format support.

Configuration is loaded from multiple sources in priority order:
1. Environment variables (highest priority)
2. .env file
3. config.toml file
4. config.yaml file
5. config.json file
6. Default values (lowest priority)

| Name                   | Type      | Default                             | Description                                                           | Example                             |
|------------------------|-----------|-------------------------------------|-----------------------------------------------------------------------|-------------------------------------|
| `DEBUG`                | `boolean` | `false`                             | Enable debug mode                                                     | `false`                             |
| `LOG_LEVEL`            | `string`  | `"INFO"`                            | Logging level (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL) | `"INFO"`                            |
| `BOT_TOKEN`            | `string`  | `""`                                | Discord bot token                                                     | `""`                                |
| `POSTGRES_HOST`        | `string`  | `"localhost"`                       | PostgreSQL host                                                       | `"localhost"`                       |
| `POSTGRES_PORT`        | `integer` | `5432`                              | PostgreSQL port                                                       | `5432`                              |
| `POSTGRES_DB`          | `string`  | `"tuxdb"`                           | PostgreSQL database name                                              | `"tuxdb"`                           |
| `POSTGRES_USER`        | `string`  | `"tuxuser"`                         | PostgreSQL username                                                   | `"tuxuser"`                         |
| `POSTGRES_PASSWORD`    | `string`  | `"ChangeThisToAStrongPassword123!"` | PostgreSQL password                                                   | `"ChangeThisToAStrongPassword123!"` |
| `DATABASE_URL`         | `string`  | `""`                                | Custom database URL override                                          | `""`                                |
| `ALLOW_SYSADMINS_EVAL` | `boolean` | `false`                             | Allow sysadmins to use eval                                           | `false`                             |

### BotInfo

Bot information configuration.

**Environment Prefix**: `BOT_INFO__`

| Name                       | Type      | Default | Description         | Example |
|----------------------------|-----------|---------|---------------------|---------|
| `BOT_INFO__BOT_NAME`       | `string`  | `"Tux"` | Name of the bot     | `"Tux"` |
| `BOT_INFO__ACTIVITIES`     | `string`  | `"[]"`  | Bot activities      | `"[]"`  |
| `BOT_INFO__HIDE_BOT_OWNER` | `boolean` | `false` | Hide bot owner info | `false` |
| `BOT_INFO__PREFIX`         | `string`  | `"$"`   | Command prefix      | `"$"`   |

### UserIds

User ID configuration.

**Environment Prefix**: `USER_IDS__`

| Name                     | Type      | Default | Description           | Example |
|--------------------------|-----------|---------|-----------------------|---------|
| `USER_IDS__BOT_OWNER_ID` | `integer` | `0`     | Bot owner user ID     | `0`     |
| `USER_IDS__SYSADMINS`    | `array`   | `[]`    | System admin user IDs | `[]`    |

### StatusRoles

Status roles configuration.

**Environment Prefix**: `STATUS_ROLES__`

| Name                     | Type    | Default | Description             | Example |
|--------------------------|---------|---------|-------------------------|---------|
| `STATUS_ROLES__MAPPINGS` | `array` | `[]`    | Status to role mappings | `[]`    |

### TempVC

Temporary voice channel configuration.

**Environment Prefix**: `TEMPVC__`

| Name                         | Type                   | Default | Description              | Example |
|------------------------------|------------------------|---------|--------------------------|---------|
| `TEMPVC__TEMPVC_CHANNEL_ID`  | `string` \| `NoneType` | `null`  | Temporary VC channel ID  | `null`  |
| `TEMPVC__TEMPVC_CATEGORY_ID` | `string` \| `NoneType` | `null`  | Temporary VC category ID | `null`  |

### GifLimiter

GIF limiter configuration.

**Environment Prefix**: `GIF_LIMITER__`

| Name                              | Type      | Default | Description          | Example |
|-----------------------------------|-----------|---------|----------------------|---------|
| `GIF_LIMITER__RECENT_GIF_AGE`     | `integer` | `60`    | Recent GIF age limit | `60`    |
| `GIF_LIMITER__GIF_LIMITS_USER`    | `object`  | `{}`    | User GIF limits      | `{}`    |
| `GIF_LIMITER__GIF_LIMITS_CHANNEL` | `object`  | `{}`    | Channel GIF limits   | `{}`    |
| `GIF_LIMITER__GIF_LIMIT_EXCLUDE`  | `array`   | `[]`    | Excluded channels    | `[]`    |

### XP

XP system configuration.

**Environment Prefix**: `XP_CONFIG__`

| Name                               | Type      | Default | Description            | Example |
|------------------------------------|-----------|---------|------------------------|---------|
| `XP_CONFIG__XP_BLACKLIST_CHANNELS` | `array`   | `[]`    | XP blacklist channels  | `[]`    |
| `XP_CONFIG__XP_ROLES`              | `array`   | `[]`    | XP roles               | `[]`    |
| `XP_CONFIG__XP_MULTIPLIERS`        | `array`   | `[]`    | XP multipliers         | `[]`    |
| `XP_CONFIG__XP_COOLDOWN`           | `integer` | `1`     | XP cooldown in seconds | `1`     |
| `XP_CONFIG__LEVELS_EXPONENT`       | `integer` | `2`     | Levels exponent        | `2`     |
| `XP_CONFIG__SHOW_XP_PROGRESS`      | `boolean` | `true`  | Show XP progress       | `true`  |
| `XP_CONFIG__ENABLE_XP_CAP`         | `boolean` | `false` | Enable XP cap          | `false` |

### Snippets

Snippets configuration.

**Environment Prefix**: `SNIPPETS__`

| Name                          | Type      | Default | Description                      | Example |
|-------------------------------|-----------|---------|----------------------------------|---------|
| `SNIPPETS__LIMIT_TO_ROLE_IDS` | `boolean` | `false` | Limit snippets to specific roles | `false` |
| `SNIPPETS__ACCESS_ROLE_IDS`   | `array`   | `[]`    | Snippet access role IDs          | `[]`    |

### IRC

IRC bridge configuration.

**Environment Prefix**: `IRC_CONFIG__`

| Name                             | Type    | Default | Description            | Example |
|----------------------------------|---------|---------|------------------------|---------|
| `IRC_CONFIG__BRIDGE_WEBHOOK_IDS` | `array` | `[]`    | IRC bridge webhook IDs | `[]`    |

### ExternalServices

External services configuration.

**Environment Prefix**: `EXTERNAL_SERVICES__`

| Name                                        | Type     | Default | Description             | Example |
|---------------------------------------------|----------|---------|-------------------------|---------|
| `EXTERNAL_SERVICES__SENTRY_DSN`             | `string` | `""`    | Sentry DSN              | `""`    |
| `EXTERNAL_SERVICES__GITHUB_APP_ID`          | `string` | `""`    | GitHub app ID           | `""`    |
| `EXTERNAL_SERVICES__GITHUB_INSTALLATION_ID` | `string` | `""`    | GitHub installation ID  | `""`    |
| `EXTERNAL_SERVICES__GITHUB_PRIVATE_KEY`     | `string` | `""`    | GitHub private key      | `""`    |
| `EXTERNAL_SERVICES__GITHUB_CLIENT_ID`       | `string` | `""`    | GitHub client ID        | `""`    |
| `EXTERNAL_SERVICES__GITHUB_CLIENT_SECRET`   | `string` | `""`    | GitHub client secret    | `""`    |
| `EXTERNAL_SERVICES__GITHUB_REPO_URL`        | `string` | `""`    | GitHub repository URL   | `""`    |
| `EXTERNAL_SERVICES__GITHUB_REPO_OWNER`      | `string` | `""`    | GitHub repository owner | `""`    |
| `EXTERNAL_SERVICES__GITHUB_REPO`            | `string` | `""`    | GitHub repository name  | `""`    |
| `EXTERNAL_SERVICES__MAILCOW_API_KEY`        | `string` | `""`    | Mailcow API key         | `""`    |
| `EXTERNAL_SERVICES__MAILCOW_API_URL`        | `string` | `""`    | Mailcow API URL         | `""`    |
| `EXTERNAL_SERVICES__WOLFRAM_APP_ID`         | `string` | `""`    | Wolfram Alpha app ID    | `""`    |
| `EXTERNAL_SERVICES__INFLUXDB_TOKEN`         | `string` | `""`    | InfluxDB token          | `""`    |
| `EXTERNAL_SERVICES__INFLUXDB_URL`           | `string` | `""`    | InfluxDB URL            | `""`    |
| `EXTERNAL_SERVICES__INFLUXDB_ORG`           | `string` | `""`    | InfluxDB organization   | `""`    |
