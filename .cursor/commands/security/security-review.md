# Security Audit

## Overview

Comprehensive security review for Discord bot operations, database access, and environment configuration.

## Steps

1. **Dependency Audit**
   - Run `uv run dev all` to check for vulnerabilities
   - Review `uv.lock` for outdated packages
   - Check Renovate PRs for security updates
   - Audit third-party Discord libraries
2. **Bot Security Review**
   - Verify Discord token handling in `.env`
   - Check permission checks in commands
   - Review role-based access control
   - Audit user input validation and sanitization
3. **Database Security**
   - Verify no raw SQL injection vectors
   - Check database credentials in `.env`
   - Audit SQLModel query patterns
   - Review database migration safety
4. **Configuration Security**
   - Ensure no secrets in `config.toml`
   - Verify `.env` not committed
   - Check Sentry DSN exposure
   - Review Docker secrets management

## Error Handling

If security issues found:

- Fix immediately for critical issues
- Document findings
- Update security practices
- Review and update related code

## Security Checklist

- [ ] Dependencies scanned with `uv` security checks
- [ ] No Discord tokens in code or config files
- [ ] Permission checks on all privileged commands
- [ ] Input validation on all user-provided data
- [ ] Database queries use SQLModel ORM (no raw SQL)
- [ ] Database credentials only in `.env`
- [ ] `.env` in `.gitignore` and not committed
- [ ] Sentry integration doesn't expose sensitive data
- [ ] Docker secrets properly mounted

## See Also

- Related rule: @security/patterns.mdc
- Related rule: @security/secrets.mdc
- Related rule: @security/validation.mdc
- Related rule: @security/dependencies.mdc
