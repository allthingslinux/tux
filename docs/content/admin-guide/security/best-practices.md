# Security Best Practices

Secure your Tux deployment.

## Token Security

- Use strong, unique bot token
- Never commit to version control
- Rotate if compromised
- Store in `.env` with 600 permissions

**[Token Security Guide →](token-security.md)**

## Database Security

- Strong passwords (32+ characters)
- Limit network access (localhost only if possible)
- Regular backups
- Encrypt connections (SSL/TLS)

## System Security

- Keep system updated
- Use firewall (UFW)
- Non-root user for bot
- Secure SSH (key-only)
- Disable unnecessary services

## Application Security

- Keep Tux updated
- Monitor error rates
- Review logs regularly
- Use Sentry for error tracking

## Docker Security

- Don't run as root (already configured)
- Use read-only filesystems where possible
- Limit resources
- Keep images updated

## Checklist

- [ ] Strong database password
- [ ] `.env` permissions set to 600
- [ ] Firewall enabled and configured
- [ ] Bot token not in version control
- [ ] Regular backups configured
- [ ] System packages up to date
- [ ] Monitoring enabled
- [ ] Logs reviewed regularly

## Related

- **[Token Security](token-security.md)**
- **[Firewall](firewall.md)**

---

*Comprehensive security guide in progress.*
