# Tux Architecture: Modular, Scalable, and Minimal

**Issue:** [#924 Architectural Refactor for Project Structure](https://github.com/allthingslinux/tux/issues/924)

---

## Introduction & Goals

Tux is designed for clarity, extensibility, and ease of contribution. The architecture separates core logic, infrastructure, features, and user add-ons, while keeping the root directory minimal and clean.

---

## Finalized Directory Structure

```plaintext
tux/
├── core/
│   ├── __init__.py
│   ├── app.py
│   ├── bot.py
│   ├── cog_loader.py
│   ├── config.py
│   ├── env.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── embeds.py
│   │   ├── buttons.py
│   │   ├── help_components.py
│   │   ├── views/
│   │   └── modals/
│   └── utils/
│       ├── __init__.py
│       ├── functions.py
│       ├── constants.py
│       ├── exceptions.py
│       ├── ascii.py
│       ├── regex.py
│       ├── emoji.py
│       ├── converters.py
│       ├── checks.py
│       ├── flags.py
│       ├── help_utils.py
│       └── banner.py
├── infra/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── controllers/
│   ├── logger.py
│   ├── sentry.py
│   ├── wrappers/
│   │   ├── __init__.py
│   │   ├── godbolt.py
│   │   ├── wandbox.py
│   │   ├── github.py
│   │   ├── xkcd.py
│   │   └── tldr.py
│   ├── hot_reload.py
│   └── handlers/
│       ├── __init__.py
│       ├── error.py
│       ├── sentry.py
│       ├── event.py
│       └── activity.py
├── modules/
│   ├── __init__.py
│   ├── moderation/
│   ├── fun/
│   ├── info/
│   ├── admin/
│   ├── snippets/
│   ├── levels/
│   ├── guild/
│   ├── services/
│   ├── tools/
│   ├── utility/
│   └── ...
├── custom_modules/
│   └── ...
├── cli/
│   ├── __init__.py
│   └── ...
├── assets/
│   ├── emojis/
│   ├── branding/
│   ├── embeds/
│   └── ...
├── main.py
└── tests/
    ├── core/
    ├── infra/
    ├── modules/
    ├── cli/
    └── ...
```

---

## Rationale for the Structure

- **Minimal root-level clutter:** Only essential directories at the top level.
- **Clear separation:**
  - `core/`: Orchestration, startup, shared UI, helpers.
  - `infra/`: Infrastructure (DB, logging, wrappers, hot reload, infra handlers).
  - `modules/`: All official, loadable feature modules/cogs/extensions.
  - `custom_modules/`: For self-hosters' add-ons (local or as submodules).
  - `cli/`: CLI tools, dev commands.
  - `assets/`: Static files, images, emojis, etc.
  - `main.py`: Entrypoint.
  - `tests/`: Mirrors the main structure for clarity and maintainability.
- **Extensible:** Easy to add new features, infra, or custom modules.
- **Contributor-friendly:** Logical, discoverable, and ready for growth.

---

## Proposals Reviewed

As Tux has grown, the need for a more intentional, scalable, and contributor-friendly project structure has become clear. Multiple proposals were presented, ranging from simple splits to modular plugin architectures.

This document summarizes the discussion and feedback from contributors and presents a final, consensus-driven proposal.

---

## Extensibility Model: Modules & Custom Modules

Tux supports two types of extensions:

### 1. **Modules** (Official/Core Features)

- **Location:** `modules/`
- **Maintained by:** Tux team (public, tracked in git)
- **Loaded by default:** Yes
- **Purpose:** Core features, public bot functionality, main way to extend Tux
- **How to contribute:** Add a new folder in `modules/` and submit a PR

### 2. **Custom Modules** (User/Server-Specific Add-ons)

- **Location:** `custom_modules/` (at project root, `.gitignored`)
- **Maintained by:** Self-hoster/forker (private, not tracked in git)
- **Loaded by default:** Only if present
- **Purpose:** Server-specific, private, or experimental features; allows self-hosters to add features without touching the main codebase
- **How to use:** Drop a `.py` file or package in `custom_modules/` and restart the bot
- **Submodules:** You can add custom modules as git submodules for versioned, shared, or organization-managed add-ons.

---

## How Modules Work (Official Features)

- Each module is a Python package (folder with `__init__.py`) in `modules/`.
- Modules are implemented as [discord.py extensions](https://discordpy.readthedocs.io/en/stable/ext/commands/extensions.html) and typically register one or more cogs.
- Modules are always loaded by the bot at startup.
- **Example module layout:**

```plaintext
modules/
  moderation/
    __init__.py
    commands.py
    services.py
    tasks.py
    models.py
    README.md
```

---

## How Custom Modules Work (Self-Hoster Add-ons)

- Place `.py` files or extension packages in `custom_modules/`.
- These are loaded automatically if present, but are not tracked in git (unless you use a submodule).
- **Submodules:** You can add a custom module repo as a submodule in `custom_modules/` for versioned, shared, or private extensions.
- **.gitignore:** `custom_modules/` is .gitignored by default, so your local or submodule code is never committed to the main repo.

**Loader Logic Example:**

```python
import os
import glob
from discord.ext import commands

bot = commands.Bot(command_prefix="!")

# Load official modules
for mod in ["modules.moderation", "modules.fun", "modules.starboard"]:
    bot.load_extension(mod)

# Load all custom modules (if any)
if os.path.isdir("custom_modules"):
    # Load .py files
    for file in glob.glob("custom_modules/*.py"):
        modname = f"custom_modules.{os.path.splitext(os.path.basename(file))[0]}"
        bot.load_extension(modname)
    # Load packages (folders with __init__.py)
    for folder in os.listdir("custom_modules"):
        folder_path = os.path.join("custom_modules", folder)
        if os.path.isdir(folder_path) and os.path.isfile(os.path.join(folder_path, "__init__.py")):
            modname = f"custom_modules.{folder}"
            bot.load_extension(modname)

# IMPORTANT: Also load all cogs/extensions in infra/handlers/ just like modules and custom_modules
if os.path.isdir("infra/handlers"):
    for file in glob.glob("infra/handlers/*.py"):
        modname = f"infra.handlers.{os.path.splitext(os.path.basename(file))[0]}"
        bot.load_extension(modname)
    for folder in os.listdir("infra/handlers"):
        folder_path = os.path.join("infra/handlers", folder)
        if os.path.isdir(folder_path) and os.path.isfile(os.path.join(folder_path, "__init__.py")):
            modname = f"infra.handlers.{folder}"
            bot.load_extension(modname)
```

**How to add a custom module as a submodule:**

```sh
git submodule add https://github.com/yourorg/tux-my-cool-module custom_modules/my_cool_module
git submodule update --init --recursive
```

After updating or cloning, run:

```sh
git submodule update --init --recursive
```

---

## Unified Summary Table

| Feature         | modules/ (Module) | custom_modules/ (Custom Module) | custom_modules/ (Submodule) | infra/handlers/ (Infra Cog) |
|-----------------|-------------------|---------------------------------|-----------------------------|-----------------------------|
| Public/Official | ✅                | ❌                              | ❌                          | ✅                          |
| Always loaded   | ✅                | ❌ (only if present)            | ❌ (only if present)        | ✅ (if present)              |
| Git-tracked     | ✅                | ❌ (.gitignored)                | ✅ (as submodule ref)       | ✅                          |
| For self-hosters| ❌                | ✅                              | ✅                          | ❌ (unless forked)           |
| For PRs         | ✅                | ❌                              | ❌                          | ✅                          |
| Versioned       | Main repo         | Local only                      | Separate repo               | Main repo                   |

---

## Handlers and Cog Loader

- **Cog-based infra handlers** (e.g., error, event, sentry, activity) live in `infra/handlers/` and are dynamically loaded by the cog loader (`core/cog_loader.py`), **just like modules and custom_modules**. This is a key part of the architecture: `infra/handlers/` is treated as a source of loadable cogs/extensions.
- **Feature modules** live in `modules/` and are also loaded by the cog loader.
- **Custom modules** in `custom_modules/` are supported for self-hosters and loaded the same way.

---

## Database Considerations

- **Core-only:** Most modules and custom modules should use the core's database API/models for common needs.
- **Advanced:** Advanced users can define models in their modules or custom modules. The bot can be designed to discover and register these models at startup, but migrations require careful management.
- **Isolated:** For small, isolated data, modules can use local files (e.g., SQLite, JSON).

---

## Tests

- All tests live in `tests/`, mirroring the main structure for discoverability and maintainability.
- Example: `tests/core/`, `tests/infra/`, `tests/modules/`, etc.

---

## Conclusion

This structure provides a clean, scalable, and contributor-friendly foundation for Tux, supporting both official features and self-hosted extensions, with clear separation of concerns and minimal root-level clutter.

---

**References:**

- [Issue #924: Architectural Refactor for Project Structure](https://github.com/allthingslinux/tux/issues/924)
- [discord.py Cogs and Extensions](https://discordpy.readthedocs.io/en/stable/ext/commands/extensions.html)
- [Jishaku: Drop-in Extension Example](https://github.com/scarletcafe/jishaku)
- [discord.py-ext-prometheus: Drop-in Monitoring Example](https://github.com/Apollo-Roboto/discord.py-ext-prometheus)
