# Token Security

Protect your Discord bot token and other sensitive credentials.

## Bot Token

### Secure Storage

✅ **Do:**

- Store in `.env` file (git-ignored)
- File permissions: `chmod 600 .env`
- Use environment variables
- Different tokens per environment

❌ **Don't:**

- Commit to Git
- Share publicly
- Hardcode in source
- Reuse across environments

### If Token is Leaked

1. **Immediately** reset in Discord Developer Portal
2. Update `.env` with new token
3. Restart bot
4. Review recent activity
5. Check for unauthorized actions

## Database Credentials

### Strong Passwords

```bash
# Generate secure password
openssl rand -base64 32
```

Use for `POSTGRES_PASSWORD`.

### Password Management

- Unique per environment
- Never use defaults in production
- Store securely
- Rotate periodically

## API Keys

For external services (Sentry, Wolfram, etc.):

- Store in `.env`
- Never commit
- Rotate if compromised
- Monitor usage

## Secrets Management

### Development

`.env` file with secure permissions.

### Production

Consider:

- Docker secrets
- Kubernetes secrets
- Vault/secrets manager
- Cloud platform secrets

## File Permissions

```bash
# Secure .env
chmod 600 .env

# Verify
ls -la .env
# Should show: -rw------- (600)
```

## Related

- **[Best Practices](best-practices.md)**
- **[Environment Variables](../setup/environment-variables.md)**

---

*Never share secrets! Always use secure storage.*
