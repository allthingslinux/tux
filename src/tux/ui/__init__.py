"""UI components for the Tux Discord bot.

This module contains all user interface components including:
- Embeds and embed creators
- Buttons and interactive components
- Views for complex interactions
- Modals for user input
- Help system components
"""

from tux.ui.buttons import GithubButton, XkcdButtons
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.ui.modals import ReportModal
from tux.ui.views import (
    BaseConfirmationView,
    ConfirmationDanger,
    ConfirmationNormal,
    TldrPaginatorView,
)

__all__ = [
    # Embeds
    "EmbedCreator",
    "EmbedType",
    # Buttons
    "GithubButton",
    "XkcdButtons",
    # Views
    "BaseConfirmationView",
    "ConfirmationDanger",
    "ConfirmationNormal",
    "TldrPaginatorView",
    # Modals
    "ReportModal",
]
