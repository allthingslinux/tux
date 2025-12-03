"""
Services layer for Tux bot.

This module contains backend services including database access,
external API wrappers, event handlers, and infrastructure services.
"""

from tux.services.http_client import http_client

__all__ = ["http_client"]
