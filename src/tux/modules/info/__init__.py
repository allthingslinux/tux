"""Info cog group for Tux Bot."""

from tux.modules.info.info import Info
from tux.modules.info.utils import send_error, send_view
from tux.modules.info.views import InfoPaginatorView

__all__ = [
    "Info",
    "InfoPaginatorView",
    "send_error",
    "send_view",
]
