"""Banner creation and formatting utilities for Tux."""

from dataclasses import dataclass, field
from typing import NamedTuple

from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text
from utils.ascii import TUX


class BannerColors(NamedTuple):
    """Color scheme for banner elements."""

    primary: str = "cyan"
    secondary: str = "white"
    success: str = "green"
    warning: str = "red"


@dataclass
class BannerConfig:
    """Configuration for banner content and styling."""

    bot_name: str
    version: str
    bot_id: str | None = None
    guild_count: int = 0
    user_count: int = 0
    prefix: str = "~"
    dev_mode: bool = False
    colors: BannerColors = field(default_factory=BannerColors)


class BannerBuilder:
    """Builder class for creating rich text banners."""

    def __init__(self, config: BannerConfig) -> None:
        self.config = config
        self._console = Console()

    def _create_ascii_art(self) -> Text:
        """Create styled ASCII art text."""
        ascii_art = Text()
        style = Style(color=self.config.colors.primary, bold=True)

        for line in TUX.splitlines():
            ascii_art.append(line, style=style)
            ascii_art.append("\n")

        return Text(ascii_art.plain.rstrip(), style=style)

    def _create_banner_table(self) -> Table:
        """Create the complete banner table."""
        # Create a grid-style table with minimal padding
        table = Table.grid(padding=(0, 2))

        # Add columns for ASCII art and info
        table.add_column(width=12)  # ASCII art
        table.add_column(justify="left", style=f"bold {self.config.colors.primary}", width=8)  # Labels
        table.add_column(style=self.config.colors.secondary)  # Values

        # Create ASCII art
        ascii_art = self._create_ascii_art()
        ascii_lines = ascii_art.plain.splitlines()

        # Create info data
        mode_style = self.config.colors.warning if self.config.dev_mode else self.config.colors.success
        mode_text = "Development" if self.config.dev_mode else "Production"

        info_data = [
            ("", ""),  # Empty row to shift content down
            ("Bot Name", f"{self.config.bot_name} (Tux)"),
            ("Version", self.config.version),
            ("Bot ID", str(self.config.bot_id or "Unknown")),
            ("Status", f"Watching {self.config.guild_count} servers with {self.config.user_count} users"),
            ("Prefix", self.config.prefix),
            ("Mode", Text(mode_text, style=mode_style)),
        ]

        # Add rows, combining ASCII art with info
        for i in range(max(len(ascii_lines), len(info_data))):
            ascii_line = ascii_lines[i] if i < len(ascii_lines) else ""
            label, value = info_data[i] if i < len(info_data) else ("", "")
            table.add_row(Text(ascii_line, style=ascii_art.style), label, value)

        return table

    def build(self) -> Panel:
        """Build the complete banner panel."""
        content = self._create_banner_table()

        return Panel(
            content,
            title=f"[bold {self.config.colors.primary}]Tux[/]",
            border_style=self.config.colors.primary,
            padding=(0, 1),
        )


def create_banner(
    bot_name: str,
    version: str,
    bot_id: str | None = None,
    guild_count: int = 0,
    user_count: int = 0,
    prefix: str = "~",
    dev_mode: bool = False,
) -> Panel:
    """Create a banner panel with bot information."""
    config = BannerConfig(
        bot_name=bot_name,
        version=version,
        bot_id=bot_id,
        guild_count=guild_count,
        user_count=user_count,
        prefix=prefix,
        dev_mode=dev_mode,
    )

    return BannerBuilder(config).build()
