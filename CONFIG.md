# Configuration

This document contains the configuration options for Tux.

<!-- CONFIGURATION START -->
## `DEBUG`

*Optional*, default value: `False`

Enable debug mode

## `BOT_TOKEN`

*Optional*, default value: ``

Discord bot token

## `POSTGRES_HOST`

*Optional*, default value: `localhost`

PostgreSQL host

## `POSTGRES_PORT`

*Optional*, default value: `5432`

PostgreSQL port

## `POSTGRES_DB`

*Optional*, default value: `tuxdb`

PostgreSQL database name

## `POSTGRES_USER`

*Optional*, default value: `tuxuser`

PostgreSQL username

## `POSTGRES_PASSWORD`

*Optional*, default value: `tuxpass`

PostgreSQL password

## `DATABASE_URL`

*Optional*, default value: ``

Custom database URL override

## `BOT_INFO__BOT_NAME`

*Optional*, default value: `Tux`

Name of the bot

## `BOT_INFO__BOT_VERSION`

*Optional*, default value: `0.0.0`

Bot version

## `BOT_INFO__ACTIVITIES`

*Optional*, default value: `[]`

Bot activities

## `BOT_INFO__HIDE_BOT_OWNER`

*Optional*, default value: `False`

Hide bot owner info

## `BOT_INFO__PREFIX`

*Optional*, default value: `$`

Command prefix

## `USER_IDS__BOT_OWNER_ID`

*Optional*, default value: `0`

Bot owner user ID

## `USER_IDS__SYSADMINS`

*Optional*

System admin user IDs

## `ALLOW_SYSADMINS_EVAL`

*Optional*, default value: `False`

Allow sysadmins to use eval

## `STATUS_ROLES__MAPPINGS`

*Optional*

Status to role mappings

## `TEMPVC__TEMPVC_CHANNEL_ID`

*Optional*, default value: `None`

Temporary VC channel ID

## `TEMPVC__TEMPVC_CATEGORY_ID`

*Optional*, default value: `None`

Temporary VC category ID

## `GIF_LIMITER__RECENT_GIF_AGE`

*Optional*, default value: `60`

Recent GIF age limit

## `GIF_LIMITER__GIF_LIMITS_USER`

*Optional*

User GIF limits

## `GIF_LIMITER__GIF_LIMITS_CHANNEL`

*Optional*

Channel GIF limits

## `GIF_LIMITER__GIF_LIMIT_EXCLUDE`

*Optional*

Excluded channels

## `XP_CONFIG__XP_BLACKLIST_CHANNELS`

*Optional*

XP blacklist channels

## `XP_CONFIG__XP_ROLES`

*Optional*

XP roles

## `XP_CONFIG__XP_MULTIPLIERS`

*Optional*

XP multipliers

## `XP_CONFIG__XP_COOLDOWN`

*Optional*, default value: `1`

XP cooldown in seconds

## `XP_CONFIG__LEVELS_EXPONENT`

*Optional*, default value: `2`

Levels exponent

## `XP_CONFIG__SHOW_XP_PROGRESS`

*Optional*, default value: `True`

Show XP progress

## `XP_CONFIG__ENABLE_XP_CAP`

*Optional*, default value: `False`

Enable XP cap

## `SNIPPETS__LIMIT_TO_ROLE_IDS`

*Optional*, default value: `False`

Limit snippets to specific roles

## `SNIPPETS__ACCESS_ROLE_IDS`

*Optional*

Snippet access role IDs

## `IRC_CONFIG__BRIDGE_WEBHOOK_IDS`

*Optional*

IRC bridge webhook IDs

## `EXTERNAL_SERVICES__SENTRY_DSN`

*Optional*, default value: ``

Sentry DSN

## `EXTERNAL_SERVICES__GITHUB_APP_ID`

*Optional*, default value: ``

GitHub app ID

## `EXTERNAL_SERVICES__GITHUB_INSTALLATION_ID`

*Optional*, default value: ``

GitHub installation ID

## `EXTERNAL_SERVICES__GITHUB_PRIVATE_KEY`

*Optional*, default value: ``

GitHub private key

## `EXTERNAL_SERVICES__GITHUB_CLIENT_ID`

*Optional*, default value: ``

GitHub client ID

## `EXTERNAL_SERVICES__GITHUB_CLIENT_SECRET`

*Optional*, default value: ``

GitHub client secret

## `EXTERNAL_SERVICES__GITHUB_REPO_URL`

*Optional*, default value: ``

GitHub repository URL

## `EXTERNAL_SERVICES__GITHUB_REPO_OWNER`

*Optional*, default value: ``

GitHub repository owner

## `EXTERNAL_SERVICES__GITHUB_REPO`

*Optional*, default value: ``

GitHub repository name

## `EXTERNAL_SERVICES__MAILCOW_API_KEY`

*Optional*, default value: ``

Mailcow API key

## `EXTERNAL_SERVICES__MAILCOW_API_URL`

*Optional*, default value: ``

Mailcow API URL

## `EXTERNAL_SERVICES__WOLFRAM_APP_ID`

*Optional*, default value: ``

Wolfram Alpha app ID

## `EXTERNAL_SERVICES__INFLUXDB_TOKEN`

*Optional*, default value: ``

InfluxDB token

## `EXTERNAL_SERVICES__INFLUXDB_URL`

*Optional*, default value: ``

InfluxDB URL

## `EXTERNAL_SERVICES__INFLUXDB_ORG`

*Optional*, default value: ``

InfluxDB organization
<!-- CONFIGURATION END -->
