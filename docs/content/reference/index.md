# API Reference

Welcome to the Tux API Reference! This section provides comprehensive auto-generated documentation for the entire codebase.

## Quick Navigation

### 📖 Documentation Types

- **[CLI Reference](cli.md)** - Command-line interface documentation
- **[Configuration Reference](configuration.md)** - Configuration schema and options
- **[Source Code](https://github.com/allthingslinux/tux)** - View source code on GitHub

## API Documentation

The API reference is automatically generated from the codebase using mkdocstrings. It includes:

- **Type hints** for all parameters and return values
- **Docstrings** with detailed explanations
- **Source code links** to view implementations
- **Cross-references** between related components

### Navigation

Use the navigation menu to browse by module:

- **Core** - Core bot functionality (app, bot, cogs, permissions)
- **Database** - Database models, controllers, and services
- **Services** - Service layer (wrappers, handlers, Sentry)
- **Modules** - Command modules (moderation, utility, features)
- **UI** - User interface components (embeds, views, modals)
- **Shared** - Shared utilities (config, exceptions, constants)

Or use the search function to find specific classes, functions, or modules.

## CLI Reference

Command-line tools for development and administration:

**[CLI Reference →](cli.md)**

Includes documentation for:

- `uv run tux` - Bot management
- `uv run db` - Database operations
- `uv run dev` - Development tools
- `uv run tests` - Test runner
- `uv run docker` - Docker management
- `uv run docs` - Documentation tools
- `uv run config` - Config generation

## Configuration Reference

Complete configuration schema with all available options:

**[Configuration Reference →](configuration.md)**

Auto-generated from the pydantic models, includes:

- Environment variable definitions
- Config file options (TOML/YAML/JSON)
- Default values
- Type information
- Descriptions

## For Developers

### Using the API Reference

When developing:

1. **Browse by Module** - Explore related functionality
2. **Search** - Find specific functions or classes
3. **Read Docstrings** - Understand parameters and behavior
4. **Check Source** - Click "Source" links to view implementation
5. **Follow Cross-References** - Navigate to related code

### Documentation Standards

All code should include:

- **Type hints** on all functions and methods
- **Numpy-style docstrings** with descriptions
- **Parameter documentation** with types and descriptions
- **Return value documentation**
- **Exception documentation** (Raises section)
- **Usage examples** (Examples section, where applicable)

**[Documentation Guide →](../developer-guide/contributing/documentation.md)**

## External References

### Python Standard Library

- **[Python 3.13 Documentation](https://docs.python.org/3.13/)**

### Discord.py

- **[discord.py Documentation](https://discordpy.readthedocs.io/en/stable/)**
- **[discord.py API Reference](https://discordpy.readthedocs.io/en/stable/api.html)**

### Database

- **[SQLModel Documentation](https://sqlmodel.tiangolo.com/)**
- **[SQLAlchemy Documentation](https://docs.sqlalchemy.org/)**
- **[Alembic Documentation](https://alembic.sqlalchemy.org/)**

### Other Dependencies

- **[Loguru Documentation](https://loguru.readthedocs.io/)**
- **[Typer Documentation](https://typer.tiangolo.com/)**
- **[Pydantic Documentation](https://docs.pydantic.dev/)**
- **[httpx Documentation](https://www.python-httpx.org/)**

## Need Help?

### Finding What You Need

1. **Use Search** - Press `/` to search the docs
2. **Check Index** - Browse the navigation sidebar
3. **Follow Links** - Cross-references link related code
4. **Read Examples** - Look for Examples sections in docstrings

### Getting Support

- **[Developer Guide](../developer-guide/index.md)** - Development documentation
- **[Discord Server](https://discord.gg/gpmSjcjQxg)** - Ask in #development
- **[GitHub Discussions](https://github.com/allthingslinux/tux/discussions)** - Technical discussions

---

**Note**: This reference is auto-generated from the source code. For conceptual documentation and guides, see the **[Developer Guide](../developer-guide/index.md)**.
