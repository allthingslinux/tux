"""
Command: config generate.

Generates configuration example files.
"""

from pathlib import Path
from typing import Annotated, Literal

from rich.panel import Panel
from typer import Exit, Option

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import console

app = create_app()


@app.command(name="generate")
def generate(
    format_: Annotated[
        Literal["env", "toml", "yaml", "json", "markdown", "all"],
        Option(
            "--format",
            "-f",
            help="Format to generate (env, toml, yaml, json, markdown, all)",
        ),
    ] = "all",
) -> None:
    """Generate configuration example files in various formats."""
    console.print(Panel.fit("Configuration Generator", style="bold blue"))

    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        console.print("pyproject.toml not found in current directory", style="red")
        raise Exit(code=1)

    base_cmd = [
        "uv",
        "run",
        "pydantic-settings-export",
        "--config-file",
        str(pyproject_path),
    ]

    format_map = {
        "env": ["dotenv"],
        "markdown": ["markdown"],
        "toml": ["toml"],
        "yaml": ["tux.shared.config.generators:YamlGenerator"],
        "json": ["tux.shared.config.generators:JsonGenerator"],
        "all": [
            "dotenv",
            "markdown",
            "toml",
            "tux.shared.config.generators:YamlGenerator",
            "tux.shared.config.generators:JsonGenerator",
        ],
    }

    formats_to_generate = format_map.get(format_)
    if formats_to_generate is None:
        console.print(f"Unknown format: {format_}", style="red")
        raise Exit(code=1)

    for generator in formats_to_generate:
        console.print(f"Running generator: {generator}", style="green")
        cmd = [*base_cmd, "--generator", generator]

        try:
            # Using run_command for consistent error handling and auditing
            run_command(cmd, capture_output=True)
        except Exception as e:
            console.print(f"Error running {generator}: {e}", style="red")
            raise Exit(code=1) from e

    console.print("\nConfiguration files generated successfully!", style="bold green")


if __name__ == "__main__":
    app()
