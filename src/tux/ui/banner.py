"""Banner creation and formatting utilities for Tux."""

from dataclasses import dataclass, field
from typing import NamedTuple

from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

BANNER_ASCII_ART = r"""    .--.
   |o_o |
   |:_/ |
  //   \ \
 (|     | )
/'\_   _/`\
\___)=(___/
"""


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
    owner_id: str | None = None
    guild_count: int = 0
    user_count: int = 0
    prefix: str = "~"
    colors: BannerColors = field(default_factory=BannerColors)


class BannerBuilder:
    """Builder class for creating rich text banners."""

    def __init__(self, config: BannerConfig) -> None:
        """Initialize the banner builder.

        Parameters
        ----------
        config : BannerConfig
            Configuration object containing banner settings and content.
        """
        self.config = config
        self._console = Console()

    def _create_ascii_art(self) -> Text:
        """Create styled ASCII art text.

        Returns
        -------
        Text
            Styled ASCII art as Rich Text object.
        """
        ascii_art = Text()
        style = Style(color=self.config.colors.primary, bold=True)

        for line in BANNER_ASCII_ART.splitlines():
            ascii_art.append(line, style=style)
            ascii_art.append("\n")

        return Text(ascii_art.plain.rstrip(), style=style)

    def _create_banner_table(self) -> Table:
        """Create the complete banner table.

        Returns
        -------
        Table
            Rich Table with ASCII art and bot information.
        """
        # Create a grid-style table with minimal padding
        table = Table.grid(padding=(0, 2))

        # Add columns for ASCII art and info
        table.add_column(width=12)  # ASCII art
        table.add_column(
            justify="left",
            style=f"bold {self.config.colors.primary}",
            width=8,
        )  # Labels
        table.add_column(style=self.config.colors.secondary)  # Values

        # Create ASCII art
        ascii_art = self._create_ascii_art()
        ascii_lines = ascii_art.plain.splitlines()

        # Create info data
        info_data = [
            ("", ""),  # Empty row to shift content down
            ("Bot Name", f"{self.config.bot_name} (Tux)"),
            ("Version", self.config.version),
            ("Bot ID", str(self.config.bot_id or "Unknown")),
            ("Owner ID", str(self.config.owner_id or "Unknown")),
            (
                "Status",
                f"Watching {self.config.guild_count} servers with {self.config.user_count} users",
            ),
            ("Prefix", self.config.prefix),
        ]

        # Add rows, combining ASCII art with info
        for i in range(max(len(ascii_lines), len(info_data))):
            ascii_line = ascii_lines[i] if i < len(ascii_lines) else ""
            label, value = info_data[i] if i < len(info_data) else ("", "")
            table.add_row(Text(ascii_line, style=ascii_art.style), label, value)

        return table

    def build(self) -> Panel:
        """Build the complete banner panel.

        Returns
        -------
        Panel
            Rich Panel containing the complete banner.
        """
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
    owner_id: str | None = None,
    guild_count: int = 0,
    user_count: int = 0,
    prefix: str = "~",
) -> Panel:
    """Create a banner panel with bot information.

    Returns
    -------
    Panel
        Rich Panel with the bot banner.
    """
    config = BannerConfig(
        bot_name=bot_name,
        version=version,
        bot_id=bot_id,
        owner_id=owner_id,
        guild_count=guild_count,
        user_count=user_count,
        prefix=prefix,
    )

    return BannerBuilder(config).build()
