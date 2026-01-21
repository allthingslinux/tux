"""
Command: config generate.

Generates configuration example files and schema from the Config model.
Produces config.json.example, config.schema.json, .env.example, and env.md.
"""

import json
from pathlib import Path
from typing import Any

from pydantic_settings import PydanticBaseSettingsSource, SettingsConfigDict
from rich.panel import Panel
from typer import Exit, Option

from scripts.core import create_app
from scripts.ui import console
from tux.shared.config.settings import Config

app = create_app()

# Paths for generated files
CONFIG_JSON_EXAMPLE = Path("config/config.json.example")
CONFIG_SCHEMA_JSON = Path("config/config.schema.json")
ENV_EXAMPLE = Path(".env.example")
ENV_MARKDOWN = Path("docs/content/reference/env.md")

# Keys to exclude from example dumps (computed fields, etc.)
EXCLUDE_FROM_EXAMPLES = {"database_url"}


def _get_example_config_class() -> type:
    """Build ExampleConfig that uses only defaults (no file or env loading)."""

    class _ExampleConfig(Config):
        model_config = SettingsConfigDict(
            env_prefix="",
            env_nested_delimiter="__",
            case_sensitive=False,
            extra="ignore",
            env_file=None,
            json_file=None,
            json_file_encoding=None,  # Suppress "unused" warning when JsonConfigSettingsSource not in sources
            secrets_dir=None,
        )

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type,
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            # Use only init/deficional defaults so generated output is deterministic
            return (init_settings,)

    return _ExampleConfig


def _get_schema_example(
    schema: dict[str, Any],
    defs: dict[str, Any],
    path: list[str],
) -> Any | None:
    """Resolve path (e.g. ['STATUS_ROLES','MAPPINGS']) to the first Field examples entry."""
    if not path:
        return None
    first = path[0]
    props = schema.get("properties") or {}
    prop = props.get(first)
    if not prop:
        return None
    if len(path) == 1:
        exs = prop.get("examples")
        return exs[0] if exs else None
    ref = prop.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/$defs/"):
        sub = defs.get(ref.replace("#/$defs/", "")) or {}
        return _get_schema_example(sub, defs, path[1:])
    return None


def _make_example_value(  # noqa: PLR0911
    key: str,
    value: Any,
    path: list[str],
    schema: dict[str, Any],
    defs: dict[str, Any],
) -> Any:
    """Replace sensitive/long values with placeholders; use schema examples for empty []/{}."""
    # Empty list -> use first schema example if available, then run through placeholders
    if isinstance(value, list) and not value:
        ex = _get_schema_example(schema, defs, path)
        if ex is not None:
            return _make_example_value(key, ex, path, schema, defs)
        return []

    # Empty dict -> use first schema example if available
    if isinstance(value, dict) and not value:
        ex = _get_schema_example(schema, defs, path)
        if ex is not None:
            return _make_example_value(key, ex, path, schema, defs)
        return {}

    if isinstance(value, list):
        return [
            _make_example_value(f"{key}_item", item, [*path, "<item>"], schema, defs)
            for item in value[:2]
        ]
    if isinstance(value, dict):
        return {
            k: _make_example_value(f"{key}_{k}", v, [*path, k], schema, defs)
            for k, v in value.items()
        }
    if isinstance(value, str):
        key_lower = key.lower()
        if "token" in key_lower or "password" in key_lower:
            return f"YOUR_{key.upper()}_HERE"
        if "url" in key_lower and value.startswith(("http", "postgres")):
            return f"YOUR_{key.upper()}_HERE"
        if value and len(value) > 10:
            return f"YOUR_{key.upper()}_HERE"
    return value


def generate_json_example() -> None:
    """Write config/config.json.example (Postgres, ExternalServices, BOT_TOKEN, DATABASE_URL → .env)."""
    example_config_cls = _get_example_config_class()
    raw = example_config_cls().model_dump(exclude=EXCLUDE_FROM_EXAMPLES)
    schema = Config.model_json_schema(mode="validation")
    defs = schema.get("$defs") or {}
    example_dict = {
        k: _make_example_value(k, v, [k], schema, defs) for k, v in raw.items()
    }
    example_dict = _drop_env_keys(example_dict)
    CONFIG_JSON_EXAMPLE.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_JSON_EXAMPLE.open("w", encoding="utf-8") as f:
        json.dump(example_dict, f, indent=2, ensure_ascii=False)


def generate_schema() -> None:
    """Write config/config.schema.json (Postgres, ExternalServices, BOT_TOKEN, DATABASE_URL → .env)."""
    schema = Config.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    _drop_env_keys_from_schema(schema)
    CONFIG_SCHEMA_JSON.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_SCHEMA_JSON.open("w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)


def _is_env_key(ek: str) -> bool:
    """Return True if this key belongs in .env (Postgres, ExternalServices, BOT_TOKEN, DATABASE_URL, DEBUG, LOG_LEVEL, MAINTENANCE_MODE)."""
    e = ek.upper()
    if e in {
        "BOT_TOKEN",
        "DATABASE_URL",
        "EXTERNAL_SERVICES",
        "DEBUG",
        "LOG_LEVEL",
        "MAINTENANCE_MODE",
    }:
        return True
    if e.startswith("POSTGRES_"):
        return True
    return e.startswith("EXTERNAL_SERVICES__")


def _drop_env_keys(obj: Any) -> Any:
    """Recursively remove .env-only keys (Postgres, ExternalServices, BOT_TOKEN, DATABASE_URL, DEBUG, LOG_LEVEL, MAINTENANCE_MODE)."""
    if isinstance(obj, dict):
        return {k: _drop_env_keys(v) for k, v in obj.items() if not _is_env_key(k)}
    if isinstance(obj, list):
        return [_drop_env_keys(x) for x in obj]
    return obj


def _drop_env_keys_from_schema(schema: dict[str, Any]) -> None:
    """Remove .env-only keys from JSON schema; drop ExternalServices $def when removed."""

    def strip_props(properties: dict[str, Any], required: list[str] | None) -> None:
        for k in list(properties.keys()):
            if _is_env_key(k):
                del properties[k]
        if isinstance(required, list):
            required[:] = [x for x in required if x in properties]

    props = schema.get("properties")
    if isinstance(props, dict):
        strip_props(props, schema.get("required"))

    defs = schema.get("$defs")
    if isinstance(defs, dict):
        defs.pop("ExternalServices", None)


def _flatten_for_env(prefix: str, obj: Any) -> dict[str, str]:
    """Flatten nested dict into KEY=value, keys UPPER_CASE, nested with __."""
    out: dict[str, str] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            env_key = (prefix + k).upper()
            if isinstance(v, dict):
                if not v:
                    out[env_key] = "{}"
                elif any(isinstance(x, (dict, list)) for x in v.values()):
                    out.update(_flatten_for_env(prefix + k + "__", v))
                else:
                    out[env_key] = json.dumps(v)
            elif isinstance(v, list):
                out[env_key] = json.dumps(v)
            elif isinstance(v, bool):
                out[env_key] = "true" if v else "false"
            elif v is None:
                out[env_key] = ""
            else:
                out[env_key] = str(v)
    return out


def _env_placeholder(key: str, value: str) -> str:
    """Use YOUR_*_HERE for secrets and long URLs in .env.example."""
    key_lower = key.lower()
    if "token" in key_lower or "password" in key_lower:
        return f"YOUR_{key}_HERE"
    if "url" in key_lower and value.startswith(("http", "postgres")):
        return f"YOUR_{key}_HERE"
    if value and len(value) > 20:
        return f"YOUR_{key}_HERE"
    return value


def generate_env_example() -> None:
    """Write .env.example (Postgres, ExternalServices, BOT_TOKEN, DATABASE_URL; rest → config.json)."""
    example_config_cls = _get_example_config_class()
    raw = example_config_cls().model_dump(exclude=EXCLUDE_FROM_EXAMPLES)
    flat: dict[str, str] = {}
    for k, v in raw.items():
        if isinstance(v, dict):
            flat.update(_flatten_for_env(f"{k.upper()}__", v))
        elif isinstance(v, list):
            flat[k.upper()] = json.dumps(v)
        elif isinstance(v, bool):
            flat[k.upper()] = "true" if v else "false"
        elif v is None:
            flat[k.upper()] = ""
        else:
            flat[k.upper()] = str(v)
    # Keep only .env keys: Postgres, ExternalServices, BOT_TOKEN, DATABASE_URL
    flat = {ek: ev for ek, ev in flat.items() if _is_env_key(ek)}
    lines = [
        "# Postgres, ExternalServices, BOT_TOKEN, DATABASE_URL, DEBUG, LOG_LEVEL, MAINTENANCE_MODE.",
        "# Used by Tux and Docker Compose. Other settings → config/config.json (config.json.example).",
        "",
    ]
    for ek, ev in flat.items():
        val = _env_placeholder(ek, ev)
        lines.append(f"{ek}={val}")
    with ENV_EXAMPLE.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")


def _schema_type_str(sch: dict[str, Any]) -> str:
    """Derive a short type string from a JSON schema fragment."""
    if "anyOf" in sch:
        parts = []
        for s in sch["anyOf"]:
            if isinstance(s, dict):
                if s.get("type") == "null":
                    continue
                parts.append(_schema_type_str(s))
            else:
                parts.append(str(s))
        base = " | ".join(parts) if parts else "string"
        return f"{base} | null"
    if "type" in sch:
        t = sch["type"]
        if isinstance(t, list):
            return " | ".join(str(x) for x in t)
        return str(t)
    if "$ref" in sch:
        return "object"
    return "any"


def generate_env_markdown() -> None:  # noqa: PLR0912, PLR0915
    """Write docs/content/reference/env.md from Config schema and defaults."""
    example_config_cls = _get_example_config_class()
    schema = Config.model_json_schema(mode="validation")
    defs = schema.get("$defs") or {}
    props = schema.get("properties") or {}
    defaults = example_config_cls().model_dump(
        mode="json",
        exclude=EXCLUDE_FROM_EXAMPLES,
    )

    def esc(s: str) -> str:
        return s.replace("|", "\\|")

    lines = [
        "---",
        "title: Environment Variables",
        "hide:",
        "  - toc",
        "tags:",
        "  - env",
        "  - configuration",
        "  - settings",
        "  - environment",
        "  - pydantic-settings",
        "  - dotenv",
        "  - env-variables",
        "---",
        "<!-- region:config -->",
        "# Environment Variables",
        "",
        "## Config",
        "",
        "Main Tux configuration using Pydantic Settings (JSON-only file support).",
        "",
        "Use **.env** for BOT_TOKEN, Postgres (POSTGRES_*), DATABASE_URL, EXTERNAL_SERVICES, DEBUG, LOG_LEVEL, MAINTENANCE_MODE; put all other settings in **config.json**.",
        "",
        "Configuration is loaded from multiple sources in priority order:",
        "1. Environment variables (highest priority)",
        "2. .env file",
        "3. config/config.json or config.json file",
        "4. Default values (lowest priority)",
        "5. Secrets (file_secret_settings, e.g. /run/secrets)",
        "",
        "| Name | Type | Default | Description | Example |",
        "|------|------|---------|-------------|---------|",
    ]

    # Top-level: scalars and non-$ref; skip nested models (they go in ### blocks)
    for name, prop in props.items():
        if name in EXCLUDE_FROM_EXAMPLES:
            continue
        ref = (prop or {}).get("$ref")
        if ref:
            continue
        desc = (prop or {}).get("description") or ""
        typ = _schema_type_str(prop or {})
        default_val = defaults.get(name)
        if default_val is None:
            default_str = "`null`"
        elif isinstance(default_val, bool):
            default_str = "`true`" if default_val else "`false`"
        elif isinstance(default_val, (list, dict)):
            default_str = f"`{json.dumps(default_val)}`"
        else:
            default_str = f"`{json.dumps(default_val)}`"
        ex = (prop or {}).get("examples")
        ex_str = ", ".join(f"`{json.dumps(x)}`" for x in (ex or [])[:3]) if ex else "-"
        lines.append(
            f"| `{esc(name)}` | `{esc(typ)}` | {default_str} | {esc(desc)} | {ex_str} |",
        )

    # Nested sections from $refs
    ref_to_def: dict[str, str] = {}
    for pname, prop in props.items():
        ref = (prop or {}).get("$ref")
        if ref and isinstance(ref, str) and ref.startswith("#/$defs/"):
            ref_to_def[pname] = ref.replace("#/$defs/", "")

    for top_key, def_name in ref_to_def.items():
        d = defs.get(def_name) or {}
        desc = d.get("description") or ""
        title = def_name  # e.g. BotInfo, UserIds
        prefix = f"{top_key}__"
        lines.extend(
            [
                "",
                f"### {title}",
                "",
                desc,
                "",
                f"**Environment Prefix**: `{prefix}`",
                "",
                "| Name | Type | Default | Description | Example |",
                "|------|------|---------|-------------|---------|",
            ],
        )
        nested_props = d.get("properties") or {}
        nd_raw = defaults.get(top_key)
        nested_defaults = nd_raw if isinstance(nd_raw, dict) else {}
        for nname, nprop in nested_props.items():
            ndesc = (nprop or {}).get("description") or ""
            ntyp = _schema_type_str(nprop or {})
            nd = nested_defaults.get(nname)
            if nd is None:
                nd_str = "`null`"
            elif isinstance(nd, bool):
                nd_str = "`true`" if nd else "`false`"
            elif isinstance(nd, (list, dict)):
                nd_str = f"`{json.dumps(nd)}`"
            else:
                nd_str = f"`{json.dumps(nd)}`"
            nex = (nprop or {}).get("examples")
            nex_str = (
                ", ".join(f"`{json.dumps(x)}`" for x in (nex or [])[:3]) if nex else "-"
            )
            env_name = f"{prefix}{nname}"
            lines.append(
                f"| `{esc(env_name)}` | `{esc(ntyp)}` | {nd_str} | {esc(ndesc)} | {nex_str} |",
            )

    lines.extend(["", "<!-- endregion:config -->", ""])
    ENV_MARKDOWN.parent.mkdir(parents=True, exist_ok=True)
    with ENV_MARKDOWN.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))


_FORMAT_TO_FN = {
    "json": generate_json_example,
    "schema": generate_schema,
    "env": generate_env_example,
    "markdown": generate_env_markdown,
}


@app.command(name="generate")
def generate(
    format_: str = Option(
        "all",
        "--format",
        "-f",
        help="Format to generate: json, schema, env, markdown, all",
    ),
) -> None:
    """Generate configuration example files and schema from Config."""
    console.print(Panel.fit("Configuration Generator", style="bold blue"))

    formats: tuple[str, ...]
    if format_ == "all":
        formats = ("json", "schema", "env", "markdown")
    elif format_ in _FORMAT_TO_FN:
        formats = (format_,)
    else:
        console.print(
            f"Unknown format: {format_}. Use: json, schema, env, markdown, all",
            style="red",
        )
        raise Exit(code=1)

    for fmt in formats:
        console.print(f"Generating: {fmt}", style="green")
        try:
            _FORMAT_TO_FN[fmt]()
        except Exception as e:
            console.print(f"Error generating {fmt}: {e}", style="red")
            raise Exit(code=1) from e

    console.print("\nConfiguration files generated successfully!", style="bold green")


if __name__ == "__main__":
    app()
