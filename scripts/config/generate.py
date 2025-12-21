"""
Command: config generate.

Generates configuration example files.
"""

import subprocess
from pathlib import Path
from typing import Annotated, Literal

from rich.panel import Panel
from typer import Exit, Option

from scripts.core import create_app
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
    output: Annotated[
        Path | None,
        Option(
            "--output",
            "-o",
            help="Output file path (not supported with CLI approach - uses pyproject.toml paths)",
        ),
    ] = None,
) -> None:
    """Generate configuration example files in various formats."""
    console.print(Panel.fit("Configuration Generator", style="bold blue"))

    if output is not None:
        console.print(
            "Custom output paths are not supported when using CLI approach",
            style="red",
        )
        console.print(
            "Use pyproject.toml configuration to specify custom paths",
            style="yellow",
        )
        raise Exit(code=1)

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

    formats_to_generate = format_map.get(format_, [])

    for generator in formats_to_generate:
        console.print(f"Running generator: {generator}", style="green")
        cmd = [*base_cmd, "--generator", generator]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if result.stdout:
                console.print(f"Output: {result.stdout.strip()}", style="dim")
        except subprocess.CalledProcessError as e:
            console.print(f"Error running {generator}: {e}", style="red")
            if e.stdout:
                console.print(f"Stdout: {e.stdout}", style="dim")
            if e.stderr:
                console.print(f"Stderr: {e.stderr}", style="red")
            raise Exit(code=1) from e

    console.print("\nConfiguration files generated successfully!", style="bold green")


if __name__ == "__main__":
    app()
