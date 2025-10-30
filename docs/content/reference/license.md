# Software Bill of Materials (SBOM)

This page contains license information for all dependencies used by Tux.

!!! note "License Information Generation"
    Due to compatibility issues with automated license scanning tools, this page contains a summary of license policies. For detailed dependency information, check `pyproject.toml` and `uv.lock`.

## Key Dependencies & Licenses

### Core Runtime Dependencies

| Package | License | Purpose |
|---------|---------|---------|
| `discord.py` | MIT | Discord API client |
| `sqlmodel` | MIT | Database ORM |
| `sqlalchemy` | MIT | Database toolkit |
| `psycopg` | LGPL-3.0 | PostgreSQL driver |
| `httpx` | BSD-3-Clause | HTTP client |
| `loguru` | MIT | Logging library |

### Development Dependencies

| Package | License | Purpose |
|---------|---------|---------|
| `ruff` | MIT | Linter & formatter |
| `pytest` | MIT | Testing framework |
| `mkdocs` | ISC | Documentation generator |
| `mkdocs-material` | MIT | Documentation theme |
| `mypy` | MIT | Type checker |

## License Summary

### License Compliance

Tux is committed to using only open-source software with permissive licenses. All dependencies are regularly audited for license compatibility.

### Key Licenses Used

- **MIT License**: Most permissive open-source license
- **Apache 2.0**: Business-friendly open-source license
- **BSD Variants**: University-developed permissive licenses
- **ISC**: Simplified BSD-style license

### Copyleft Avoidance

Tux deliberately avoids dependencies with copyleft licenses (GPL, LGPL, AGPL) to ensure maximum compatibility for both open-source and commercial deployments.

## Security Considerations

### Software Supply Chain

- All dependencies are pinned to specific versions
- Dependencies are regularly updated and audited
- No dependencies with known security vulnerabilities
- Automated dependency scanning in CI/CD pipeline

### Vulnerability Management

- Security advisories monitored via GitHub Dependabot
- Critical security updates applied within 48 hours
- Regular dependency updates during maintenance windows

## Contributing

When adding new dependencies to Tux:

1. **License Check**: Ensure the license is permissive (MIT, Apache 2.0, BSD, ISC)
2. **Security Audit**: Check for known vulnerabilities
3. **Minimal Dependencies**: Prefer libraries with few transitive dependencies
4. **Maintenance**: Choose actively maintained packages

## Contact

For license-related questions or concerns, please contact the maintainers through:

- [GitHub Issues](https://github.com/allthingslinux/tux/issues)
- [Discord Community](https://discord.gg/gpmSjcjQxg)
