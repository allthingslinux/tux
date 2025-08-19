from __future__ import annotations

from . import content as _content  # noqa: F401

# Centralized model registry warm-up: importing modules ensures SQLModel/SQLAlchemy
# see all mapped classes and relationships during application start.
# This is a conventional pattern for ORMs to avoid scattered side-effect imports.
from . import guild as _guild  # noqa: F401
from . import moderation as _moderation  # noqa: F401
from . import permissions as _permissions  # noqa: F401
from . import social as _social  # noqa: F401
from . import starboard as _starboard  # noqa: F401
