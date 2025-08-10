"""Database controller module providing access to all model controllers."""

import importlib
from typing import Any, ClassVar, TypeVar

from tux.services.database.controllers.afk import AfkController
from tux.services.database.controllers.case import CaseController
from tux.services.database.controllers.guild import GuildController
from tux.services.database.controllers.guild_config import GuildConfigController
from tux.services.database.controllers.levels import LevelsController
from tux.services.database.controllers.note import NoteController
from tux.services.database.controllers.reminder import ReminderController
from tux.services.database.controllers.snippet import SnippetController
from tux.services.database.controllers.starboard import (
    StarboardController,
    StarboardMessageController,
)

# Note: Avoid importing tracing at module import time to prevent circular imports.
_TRACING_AVAILABLE = True

# Define a TypeVar that can be any BaseController subclass
ControllerType = TypeVar("ControllerType")


class DatabaseController:
    """
    Provides access to all database controllers.

    This class acts as a central point for accessing various table-specific controllers.
    Each controller is lazily instantiated on first access using properties.

    Attributes
    ----------
    _afk : AfkController, optional
        The AFK controller instance.
    _case : CaseController, optional
        The case controller instance.
    _guild : GuildController, optional
        The guild controller instance.
    _guild_config : GuildConfigController, optional
        The guild configuration controller instance.
    _levels : LevelsController, optional
        The levels controller instance.
    _note : NoteController, optional
        The note controller instance.
    _reminder : ReminderController, optional
        The reminder controller instance.
    _snippet : SnippetController, optional
        The snippet controller instance.
    _starboard : StarboardController, optional
        The starboard controller instance.
    _starboard_message : StarboardMessageController, optional
        The starboard message controller instance.
    """

    def __init__(self) -> None:
        """Initializes the DatabaseController without creating any controller instances."""
        # All controllers are lazily instantiated
        self._afk: AfkController | None = None
        self._case: CaseController | None = None
        self._guild: GuildController | None = None
        self._guild_config: GuildConfigController | None = None
        self._levels: LevelsController | None = None
        self._note: NoteController | None = None
        self._reminder: ReminderController | None = None
        self._snippet: SnippetController | None = None
        self._starboard: StarboardController | None = None
        self._starboard_message: StarboardMessageController | None = None

    def _get_controller(self, controller_type: type[ControllerType]) -> ControllerType:
        """
        Helper to instantiate a controller with selective Sentry instrumentation.

        Only instruments meaningful database operations to reduce span noise.

        Parameters
        ----------
        controller_type : type[ControllerType]
            The type of controller to instantiate

        Returns
        -------
        ControllerType
            The instantiated controller with selectively instrumented methods
        """
        instance = controller_type()

        # Exclude internal/utility helpers that create noise
        excluded_methods = {
            "safe_get_attr",
            "connect_or_create_relation",
            "_add_include_arg_if_present",
            "_build_find_args",
            "_build_simple_args",
            "_build_create_args",
            "_build_update_args",
            "_build_delete_args",
            "_build_upsert_args",
            "_execute_query",
            "_set_scope_context",
        }

        # Include common CRUD/meaningful patterns
        include_prefixes = (
            "get_",
            "find_",
            "create_",
            "update_",
            "delete_",
            "count_",
            "increment_",
            "toggle_",
            "lock_",
            "unlock_",
            "bulk_",
        )

        # Lazy import via importlib to avoid circular import during package init
        try:
            _tracing = importlib.import_module("tux.utils.tracing")
            _span = getattr(_tracing, "span", None)
        except Exception:
            _span = None

        # Get public methods that aren't excluded
        method_names = [
            attr
            for attr in dir(instance)
            if callable(getattr(instance, attr)) and not attr.startswith("_") and attr not in excluded_methods
        ]

        # Wrap only methods that match meaningful operation patterns
        for method_name in method_names:
            if method_name.startswith(include_prefixes):
                original_method = getattr(instance, method_name)
                if _span is not None:
                    op = f"db.controller.{method_name}"
                    wrapped = _span(op=op)(original_method)
                    setattr(instance, method_name, wrapped)

        return instance

    _controller_mapping: ClassVar[dict[str, type]] = {
        "afk": AfkController,
        "case": CaseController,
        "guild": GuildController,
        "guild_config": GuildConfigController,
        "levels": LevelsController,
        "note": NoteController,
        "reminder": ReminderController,
        "snippet": SnippetController,
        "starboard": StarboardController,
        "starboard_message": StarboardMessageController,
    }

    def __getattr__(self, name: str) -> Any:
        """
        Dynamic property access for controllers.

        This method automatically handles lazy-loading of controller instances
        when they are first accessed.

        Parameters
        ----------
        name : str
            The name of the controller to access

        Returns
        -------
        Any
            The requested controller instance

        Raises
        ------
        AttributeError
            If the requested controller doesn't exist
        """
        if name in self._controller_mapping:
            # Get the private attribute name
            private_name = f"_{name}"

            # Initialize the controller if it doesn't exist
            if not hasattr(self, private_name) or getattr(self, private_name) is None:
                controller_type = self._controller_mapping[name]
                setattr(self, private_name, self._get_controller(controller_type))

            # Return the initialized controller
            return getattr(self, private_name)

        # If not a controller, raise AttributeError
        msg = f"{self.__class__.__name__} has no attribute '{name}'"

        raise AttributeError(msg)
