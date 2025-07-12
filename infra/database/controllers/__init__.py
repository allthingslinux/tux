"""Database controller module providing access to all model controllers."""

import functools
import inspect
from typing import Any, ClassVar, TypeVar

import sentry_sdk
from database.controllers.afk import AfkController
from database.controllers.case import CaseController
from database.controllers.guild import GuildController
from database.controllers.guild_config import GuildConfigController
from database.controllers.levels import LevelsController
from database.controllers.note import NoteController
from database.controllers.reminder import ReminderController
from database.controllers.snippet import SnippetController
from database.controllers.starboard import StarboardController, StarboardMessageController

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
        Helper method to instantiate a controller with proper Sentry instrumentation.

        Parameters
        ----------
        controller_type : type[ControllerType]
            The type of controller to instantiate

        Returns
        -------
        ControllerType
            The instantiated controller
        """
        instance = controller_type()
        if sentry_sdk.is_initialized():
            # Get all public methods to wrap
            methods = [attr for attr in dir(instance) if callable(getattr(instance, attr)) and not attr.startswith("_")]

            # Wrap each public method with Sentry transaction
            for method_name in methods:
                original_method = getattr(instance, method_name)
                # Use a factory function to capture loop variables
                self._create_wrapped_method(instance, method_name, original_method)

        return instance

    def _create_wrapped_method(self, instance: Any, method_name: str, original_method: Any) -> None:
        """
        Create a wrapped method with proper sentry instrumentation.

        Parameters
        ----------
        instance : Any
            The controller instance
        method_name : str
            The name of the method to wrap
        original_method : Any
            The original method to wrap
        """

        # Check if the original method is async
        is_async = inspect.iscoroutinefunction(original_method)

        if is_async:

            @functools.wraps(original_method)
            async def async_wrapped_method(*args: Any, **kwargs: Any) -> Any:
                controller_name = instance.__class__.__name__
                with sentry_sdk.start_span(
                    op=f"db.controller.{method_name}",
                    description=f"{controller_name}.{method_name}",
                ) as span:
                    span.set_tag("db.controller", controller_name)
                    span.set_tag("db.operation", method_name)
                    try:
                        result = await original_method(*args, **kwargs)
                    except Exception as e:
                        span.set_status("internal_error")
                        span.set_data("error", str(e))
                        raise
                    else:
                        span.set_status("ok")
                        return result

            setattr(instance, method_name, async_wrapped_method)

        else:

            @functools.wraps(original_method)
            def sync_wrapped_method(*args: Any, **kwargs: Any) -> Any:
                controller_name = instance.__class__.__name__
                with sentry_sdk.start_span(
                    op=f"db.controller.{method_name}",
                    description=f"{controller_name}.{method_name}",
                ) as span:
                    span.set_tag("db.controller", controller_name)
                    span.set_tag("db.operation", method_name)
                    try:
                        result = original_method(*args, **kwargs)
                    except Exception as e:
                        span.set_status("internal_error")
                        span.set_data("error", str(e))
                        raise
                    else:
                        span.set_status("ok")
                        return result

            setattr(instance, method_name, sync_wrapped_method)

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
