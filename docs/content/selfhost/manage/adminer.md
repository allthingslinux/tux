# Adminer Web UI

Web-based database administration interface.

## Accessing Adminer

**Docker Compose users:**

Adminer is included and runs on port 8080:

```text
http://localhost:8080
```

**Auto-login** is enabled by default for development.

## Features

- Browse tables and data
- Run SQL queries
- Export/import data
- View table structure
- Edit records directly
- User-friendly interface
- Dracula theme

## Manual Login

If auto-login is disabled:

- **System:** PostgreSQL
- **Server:** tux-postgres
- **Username:** tuxuser
- **Password:** (from your .env)
- **Database:** tuxdb

## Common Tasks

### Browse Data

1. Click database name (tuxdb)
2. Click table name
3. View/edit data

### Run SQL Query

1. Click "SQL command"
2. Enter your query
3. Click "Execute"

### Export Database

1. Click "Export"
2. Choose format (SQL, CSV)
3. Click "Export"

## Security

!!! danger "Production Warning"
    **Disable auto-login in production!**

  In `.env`:

  ```bash
  ADMINER_AUTO_LOGIN=false
  ```

!!! warning "Don't Expose Publicly"
    Adminer should only be accessible locally or via VPN/SSH tunnel.

### SSH Tunnel

For remote access:

```bash
ssh -L 8080:localhost:8080 user@your-server
```

Then access `http://localhost:8080` on your local machine.

## Configuration

### Change Port

In `.env`:

```bash
ADMINER_PORT=9090
```

Then access at `http://localhost:9090`

### Disable Adminer

Comment out in `compose.yaml` or:

```bash
docker compose stop tux-adminer
```

## Related

- **[Database Setup](../setup/database.md)**
- **[Docker Compose Deployment](../deployment/docker-compose.md)**

---

*Adminer is development/debugging tool. Use with caution in production.*
