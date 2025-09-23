# type: ignore

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from re import Match
from typing import Any

from mkdocs.config import Config as MkDocsConfig
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page


@dataclass
class CommandInfo:
    name: str
    aliases: list[str]
    description: str
    parameters: list[dict[str, Any]]
    permission_level: str
    command_type: str
    category: str
    usage: str


class TuxPluginConfig(config_options.Config):
    modules_path = config_options.Type(str, default="src/tux/modules")
    enable_commands = config_options.Type(bool, default=True)


class TuxPlugin(BasePlugin[TuxPluginConfig]):
    """MkDocs plugin for Tux bot documentation using AST parsing."""

    def __init__(self):
        super().__init__()
        self.commands_cache: dict[str, list[CommandInfo]] = {}

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        src_path = Path(config["docs_dir"]).parent.parent / "src"  # type: ignore[index]
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        return config

    def on_page_markdown(self, markdown: str, page: Page, config: MkDocsConfig, files: Files) -> str:
        if self.config["enable_commands"]:
            markdown = self._process_commands_blocks(markdown, config)
        return markdown

    def _process_commands_blocks(self, markdown: str, config: MkDocsConfig) -> str:
        pattern = r"::: tux-commands\s*\n((?:\s*:[\w-]+:\s*.+\s*\n)*)"

        def replace_block(match: Match[str]) -> str:
            params: dict[str, str] = {}
            param_lines = match.group(1).strip().split("\n")
            for line in param_lines:
                if ":" in line and line.strip().startswith(":"):
                    key, value = line.strip().split(":", 2)[1:]
                    params[key.strip()] = value.strip()
            return self._generate_command_docs(params, config)

        return re.sub(pattern, replace_block, markdown, flags=re.MULTILINE)

    def _generate_command_docs(self, params: dict[str, str], config: MkDocsConfig) -> str:
        project_root = Path(config["docs_dir"]).parent.parent  # type: ignore[index].parent
        modules_path = project_root / self.config["modules_path"]
        category = params.get("category", "all")

        if category not in self.commands_cache:
            self.commands_cache[category] = self._scan_category(category, modules_path)

        commands = self.commands_cache[category]
        if not commands:
            return f"<!-- No commands found for category: {category} -->\n"

        md = [self._format_command(cmd) for cmd in sorted(commands, key=lambda x: x.name)]

        return "\n\n".join(md)

    def _scan_category(self, category: str, modules_path: Path) -> list[CommandInfo]:
        category_path = modules_path / category
        if not category_path.exists():
            return []

        commands = []
        for py_file in category_path.glob("*.py"):
            if not py_file.name.startswith("_"):
                commands.extend(self._extract_commands_from_file(py_file, category))

        return commands

    def _extract_commands_from_file(self, file_path: Path, category: str) -> list[CommandInfo]:
        try:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            commands = [
                cmd_info
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                and (cmd_info := self._parse_command_function(node, category))
            ]
        except Exception:
            return []

        return commands

    def _parse_command_function(  # noqa: PLR0912
        self,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        category: str,
    ) -> CommandInfo | None:  # sourcery skip: low-code-quality
        command_type = None
        name = str(func_node.name)
        aliases = []

        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                attr_name = decorator.func.attr
                if (
                    isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "commands"
                    and attr_name in ["hybrid_command", "command", "slash_command"]
                ):
                    command_type = attr_name

                    for keyword in decorator.keywords:
                        if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                            name = str(keyword.value.value)
                        elif keyword.arg == "aliases" and isinstance(keyword.value, ast.List):
                            aliases = [str(elt.value) for elt in keyword.value.elts if isinstance(elt, ast.Constant)]

        if not command_type:
            return None

        description = ""
        if (
            func_node.body
            and isinstance(func_node.body[0], ast.Expr)
            and isinstance(func_node.body[0].value, ast.Constant)
        ):
            docstring = func_node.body[0].value.value
            if isinstance(docstring, str):
                description = docstring.split("\n")[0].strip()

        parameters: list[dict[str, Any]] = []
        for arg in func_node.args.args[2:]:  # Skip self, ctx
            param_type = "Any"
            if arg.annotation:
                try:
                    param_type = ast.unparse(arg.annotation)
                except Exception:
                    param_type = "Any"

            parameters.append({"name": arg.arg, "type": param_type, "required": True})

        permission_level = self._extract_permission_level(func_node)

        usage = f"${name}"
        if parameters:
            param_str = " ".join(f"<{p['name']}>" for p in parameters)
            usage += f" {param_str}"

        return CommandInfo(
            name=name,
            aliases=aliases,
            description=description,
            parameters=parameters,
            permission_level=permission_level,
            command_type=command_type,
            category=category,
            usage=usage,
        )

    def _extract_permission_level(self, func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                func_name = decorator.func.id
                if func_name.startswith("require_"):
                    return func_name.replace("require_", "").replace("_", " ").title()
        return "Everyone"

    def _format_command(self, cmd: CommandInfo) -> str:
        md: list[str] = []

        # Command header with admonition
        if cmd.command_type == "hybrid_command":
            md.append(f'!!! info "/{cmd.name} or ${cmd.name}"')
        elif cmd.command_type == "slash_command":
            md.append(f'!!! info "/{cmd.name} (Slash Only)"')
        else:
            md.append(f'!!! info "${cmd.name}"')

        md.extend(
            (
                "",
                '    <div class="grid cards" markdown>',
                "",
                "    -   :material-folder: **Category**",
                "",
                f"        {cmd.category.title()}",
                "",
                "    -   :material-shield-account: **Permission**",
                "",
                f"        {cmd.permission_level}",
                "",
                "    </div>",
                "",
            ),
        )
        if cmd.command_type == "hybrid_command":
            md.extend(
                (
                    '=== "Slash Command"',
                    "",
                    "```",
                    f"{cmd.usage.replace('$', '/')}",
                    "```",
                    "",
                    '=== "Prefix Command"',
                    "",
                    "```",
                    f"{cmd.usage}",
                ),
            )
        else:
            md.extend(("**Usage:**", "", "```", cmd.usage))
        md.extend(("```", ""))
        # Description
        if cmd.description:
            md.extend(('!!! quote "Description"', "", f"    {cmd.description}", ""))
        # Aliases
        if cmd.aliases:
            aliases_str = ", ".join(f"`{alias}`" for alias in cmd.aliases)
            md.extend(('!!! tip "Aliases"', "", f"    {aliases_str}", ""))
        # Parameters
        if cmd.parameters:
            md.extend(('!!! abstract "Parameters"', ""))
            for param in cmd.parameters:
                required = ":material-check: Required" if param["required"] else ":material-minus: Optional"
                md.append(f"    - **`{param['name']}`** ({param['type']}) - {required}")
            md.append("")

        return "\n".join(md)
