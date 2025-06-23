# Getting started with self-hosting Tux
> [!WARNING]
> This guide is for Docker with Docker Compose. This also assumes you have a working Postgres database. If you don't have one, you can use [Supabase](https://supabase.io/).

## Prerequisites
- Docker and Docker Compose
- A working Postgres database and the URL in the format `postgres://[username]:[password]@host:port/database`. For Supabase users, ensure you use the provided pooler URL in the same format.
- Discord bot token with intents enabled
- Sentry URL for error tracking (optional)

## Steps to Install
1. Clone the repository

    ```bash
    git clone https://github.com/allthingslinux/tux && cd tux
    ```

2. Copy the `.env.example` file to `.env` and fill in the required values.

3. Copy the `config/settings.yml.example` file to `config/settings.yml` and fill in the required values.

4. Start the bot

    ```bash
    docker-compose up -d
    ```

    > [!NOTE]
    > Add `--build` to the command if you want to use your local changes.

5. Check the logs to see if the bot is running

    ```bash
    docker-compose logs
    ```

6. Push the database schema

    ```bash
    docker exec -it tux prisma db push
    ```

    > [!NOTE]
    > If this gets stuck your database URL is most likely incorrect. Please check the URL (port as well, port is usually 5432). You should give the command 30 seconds to run before you assume it's stuck.

7. Run `(prefix)help` in your server to see if the bot is running. If it is, now you can start configuring the bot.
