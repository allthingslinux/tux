---
title: Software Bill of Materials (SBOM)
hide:
  - toc
tags:
  - reference
  - sbom
  - dependencies
---
---

# Software Bill of Materials (SBOM)

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

This page provides a comprehensive list of all dependencies used in Tux, including their licenses and versions. This information is essential for software supply chain security and legal compliance.

## Dependencies

::sbom
    base_indent: 2
    groups: dev, test, docs, types

## License Information

The license information above is automatically generated from the project's dependencies defined in `pyproject.toml`. Each package entry includes:

- **Package Name** - The name of the dependency
- **License** - The license(s) under which the package is distributed
- **Version** - The version checked during documentation build
- **Author** - The package author/maintainer

## License Compliance

Tux is licensed under the **GPL-3.0-or-later** license. All dependencies listed above are compatible with this license. If you notice any license compatibility issues, please [report them](https://github.com/allthingslinux/tux/issues).

## Security

For security concerns related to dependencies:

- Review [GitHub Security Advisories](https://github.com/allthingslinux/tux/security/advisories)
- Report security issues via [GitHub Security](https://github.com/allthingslinux/tux/security)

## Updating Dependencies

Dependencies are managed using `uv` and locked in `uv.lock`. To update dependencies:

    ```bash
    # Update all dependencies
    uv sync --upgrade

    # Update a specific dependency
    uv sync --upgrade-package <package-name>
    ```

**Automated Updates**: Tux uses [Renovate](./renovate.md) to automatically create pull requests for dependency updates. This helps keep dependencies up-to-date and secure with minimal manual intervention.

## Related Documentation

- **[Renovate](./renovate.md)** - Automated dependency updates and Renovate configuration
- **[Configuration Reference](./env.md)** - Configuration options
- **[CLI Reference](./cli.md)** - Command-line tools
