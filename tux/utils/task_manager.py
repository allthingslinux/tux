"""
Asynchronous Task Management Utility.

This module provides the `TaskManager` class, which encapsulates the logic for
monitoring, categorizing, and managing the lifecycle of asyncio tasks within the
bot. By abstracting this functionality, it keeps the main `Tux` class cleaner
and more focused on its core responsibilities.

The manager is responsible for:
- Periodically monitoring all running asyncio tasks.
- Categorizing tasks based on their naming conventions (e.g., discord.py
  internal tasks, scheduled tasks, command tasks).
- Gracefully stopping and cancelling tasks during the bot's shutdown sequence.
- Health monitoring and automatic recovery of critical tasks.
- Collecting performance metrics and statistics.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections import defaultdict, deque
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, ClassVar, NamedTuple, cast

from discord.ext import tasks
from loguru import logger

from tux.utils.protocols import BotProtocol
from tux.utils.tracing import start_span, transaction


class TaskCategory(Enum):
    """Categories for background tasks."""

    SCHEDULED = auto()
    GATEWAY = auto()
    SYSTEM = auto()
    COMMAND = auto()
    UNKNOWN = auto()


class TaskPriority(Enum):
    """Task priority levels for shutdown ordering."""

    CRITICAL = auto()  # Essential tasks (database, core services)
    HIGH = auto()  # Important tasks (moderation, reminders)
    NORMAL = auto()  # Regular tasks (levels, starboard)
    LOW = auto()  # Optional tasks (status, activities)


@dataclass
class TaskMetrics:
    """Metrics tracking for individual tasks."""

    name: str
    category: TaskCategory
    priority: TaskPriority = TaskPriority.NORMAL
    start_time: float = field(default_factory=time.time)
    restart_count: int = 0
    last_restart: float | None = None
    total_runtime: float = 0.0
    avg_runtime: float = 0.0
    max_runtime: float = 0.0
    error_count: int = 0
    last_error: str | None = None
    last_error_time: float | None = None


class TaskHealth(NamedTuple):
    """Health status of a task."""

    is_healthy: bool
    uptime: float
    error_rate: float
    restart_count: int
    last_seen: float


@dataclass
class CriticalTaskConfig:
    """Configuration for critical tasks that should be monitored and restarted."""

    name: str
    cog_name: str
    task_attr: str
    priority: TaskPriority = TaskPriority.HIGH
    max_restarts: int = 5
    restart_delay: float = 30.0
    health_check_interval: float = 300.0  # 5 minutes


class TaskManager:
    """
    Enhanced task manager with health monitoring, metrics, and recovery capabilities.

    Manages the lifecycle of asyncio tasks for the bot with advanced features:
    - Task registration and health monitoring
    - Automatic recovery of failed critical tasks
    - Performance metrics and statistics collection
    """

    # This mapping is used to categorize tasks based on the prefix of their names.
    # It allows for easy identification of tasks from specific libraries or systems.
    TASK_PREFIX_MAP: ClassVar[dict[tuple[str, ...], TaskCategory]] = {
        ("discord-ext-tasks:",): TaskCategory.SCHEDULED,
        ("discord.py:", "discord-voice-", "discord-gateway-"): TaskCategory.GATEWAY,
        ("patch_asyncio",): TaskCategory.SYSTEM,
    }

    # Default critical tasks that should be monitored
    DEFAULT_CRITICAL_TASKS: ClassVar[list[CriticalTaskConfig]] = [
        CriticalTaskConfig("reminder_processor", "ReminderService", "reminder_processor", TaskPriority.CRITICAL),
        CriticalTaskConfig("tempban_checker", "TempBan", "check_tempbans", TaskPriority.HIGH),
        CriticalTaskConfig("afk_expiration_handler", "Afk", "handle_afk_expiration", TaskPriority.NORMAL),
        CriticalTaskConfig("old_gif_remover", "GifLimiter", "old_gif_remover", TaskPriority.NORMAL),
        CriticalTaskConfig("influx_guild_stats", "InfluxLogger", "_log_guild_stats", TaskPriority.LOW),
        CriticalTaskConfig("influx_db_logger", "InfluxLogger", "logger", TaskPriority.LOW),
    ]

    def __init__(self, bot: BotProtocol) -> None:
        """
        Initialize the TaskManager with enhanced monitoring capabilities.

        Parameters
        ----------
        bot : BotProtocol
            The bot instance that conforms to the protocol.
        """
        self.bot = bot

        # Task registration and monitoring
        self.critical_tasks: dict[str, CriticalTaskConfig] = {}
        self.task_metrics: dict[str, TaskMetrics] = {}
        self.task_history: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=100))

        # Health monitoring
        self.last_health_check: float = 0.0
        self.health_check_interval: float = 300.0  # 5 minutes

        # Note: Critical tasks are now registered after cogs are loaded
        # to ensure cogs exist before registering their tasks

    def setup_task_instrumentation(self) -> None:
        """
        Initializes instrumentation for all registered critical tasks.

        This method should be called after all cogs are loaded to ensure
        that the task objects are available to be wrapped.
        """
        logger.info("Setting up Sentry instrumentation for critical tasks...")

        for task_name, config in self.critical_tasks.items():
            if not (cog := self.bot.cogs.get(config.cog_name)):
                logger.warning(f"Cog {config.cog_name} not found for task {task_name}. Skipping instrumentation.")
                continue

            if not (task_loop := getattr(cog, config.task_attr, None)):
                logger.warning(
                    f"Task loop {config.task_attr} not found in cog {config.cog_name}. Skipping instrumentation.",
                )
                continue

            if isinstance(task_loop, tasks.Loop):
                try:
                    # We are confident .coro exists and is a callable coroutine on a tasks.Loop instance.
                    # The type checker struggles with this dynamic attribute from the discord.py library.
                    original_coro = cast(Callable[..., Coroutine[Any, Any, None]], task_loop.coro)  # type: ignore[attr-defined]
                    decorated_loop = transaction(op="task.run", name=f"task.{task_name}")(original_coro)
                    task_loop.coro = decorated_loop  # type: ignore[attr-defined]
                    logger.debug(f"Instrumented task: {task_name}")
                except AttributeError:
                    logger.warning(f"Could not find a 'coro' on task {task_name}. Skipping instrumentation.")
            else:
                logger.warning(
                    f"Attribute {config.task_attr} in {config.cog_name} is not a Loop. Skipping instrumentation.",
                )

    # --- Public Methods ---

    def start(self) -> None:
        """Starts the background task monitoring loop if it's not already running."""
        if not self._monitor_tasks_loop.is_running():
            self._monitor_tasks_loop.start()
            logger.debug("Task monitoring loop started.")
        logger.debug("Enhanced task monitoring started.")

    def stop(self) -> None:
        """Stops the background task monitoring loop."""
        if self._monitor_tasks_loop.is_running():
            self._monitor_tasks_loop.stop()
        logger.debug("Enhanced task monitoring stopped.")

    def register_critical_task(self, config: CriticalTaskConfig) -> None:
        """
        Register a critical task for health monitoring and recovery.

        Parameters
        ----------
        config : CriticalTaskConfig
            Configuration for the critical task.
        """
        self.critical_tasks[config.name] = config
        self.task_metrics[config.name] = TaskMetrics(
            name=config.name,
            category=TaskCategory.SCHEDULED,
            priority=config.priority,
        )
        logger.debug(f"Registered critical task: {config.name}")

    def unregister_critical_task(self, task_name: str) -> None:
        """
        Unregister a critical task when its cog is unloaded.

        Parameters
        ----------
        task_name : str
            The name of the task to unregister.
        """
        if task_name in self.critical_tasks:
            del self.critical_tasks[task_name]
            logger.debug(f"Unregistered critical task: {task_name}")

        if task_name in self.task_metrics:
            del self.task_metrics[task_name]
            logger.debug(f"Removed metrics for task: {task_name}")

    def cleanup_cog_tasks(self, cog_name: str) -> None:
        """
        Clean up all critical tasks associated with a specific cog.

        Parameters
        ----------
        cog_name : str
            The name of the cog that was unloaded.
        """
        tasks_to_remove = [
            task_name for task_name, config in self.critical_tasks.items() if config.cog_name == cog_name
        ]

        for task_name in tasks_to_remove:
            self.unregister_critical_task(task_name)

        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} critical tasks for unloaded cog: {cog_name}")

    def get_task_health(self, task_name: str) -> TaskHealth | None:
        """
        Get health status for a specific task.

        Parameters
        ----------
        task_name : str
            The name of the task to check.

        Returns
        -------
        TaskHealth | None
            Health status or None if task not found.
        """
        if (metrics := self.task_metrics.get(task_name)) is None:
            return None

        current_time = time.time()
        uptime = current_time - metrics.start_time

        # Calculate error rate (errors per hour)
        error_rate = (metrics.error_count / max(uptime / 3600, 0.1)) if uptime > 0 else 0.0

        # Task is healthy if it has low error rate and hasn't been restarting frequently
        is_healthy = (
            error_rate < 10.0  # Less than 10 errors per hour
            and metrics.restart_count < 3  # Less than 3 restarts
            and (not metrics.last_restart or current_time - metrics.last_restart > 300)  # No restart in last 5 minutes
        )

        return TaskHealth(
            is_healthy=is_healthy,
            uptime=uptime,
            error_rate=error_rate,
            restart_count=metrics.restart_count,
            last_seen=current_time,
        )

    def get_task_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive task statistics.

        Returns
        -------
        dict[str, Any]
            Statistics about all monitored tasks.
        """
        # Initialize counters
        healthy_tasks = 0
        unhealthy_tasks = 0
        total_restarts = 0
        total_errors = 0
        categories: defaultdict[str, int] = defaultdict(int)
        priorities: defaultdict[str, int] = defaultdict(int)

        for task_name, metrics in self.task_metrics.items():
            if health := self.get_task_health(task_name):
                if health.is_healthy:
                    healthy_tasks += 1
                else:
                    unhealthy_tasks += 1

            categories[metrics.category.name] += 1
            priorities[metrics.priority.name] += 1
            total_restarts += metrics.restart_count
            total_errors += metrics.error_count

        return {
            "total_tasks": len(self.task_metrics),
            "critical_tasks": len(self.critical_tasks),
            "healthy_tasks": healthy_tasks,
            "unhealthy_tasks": unhealthy_tasks,
            "categories": dict(categories),
            "priorities": dict(priorities),
            "total_restarts": total_restarts,
            "total_errors": total_errors,
        }

    async def restart_critical_task(self, task_name: str) -> bool:  # noqa: PLR0911
        """
        Attempt to restart a critical task.

        Parameters
        ----------
        task_name : str
            The name of the task to restart.

        Returns
        -------
        bool
            True if restart was successful, False otherwise.
        """
        # Validate task is critical and get config/metrics
        if task_name not in self.critical_tasks:
            logger.warning(f"Cannot restart non-critical task: {task_name}")
            return False

        config = self.critical_tasks[task_name]
        metrics = self.task_metrics[task_name]
        current_time = time.time()

        # Check restart constraints
        if metrics.restart_count >= config.max_restarts:
            logger.error(f"Task {task_name} has exceeded max restarts ({config.max_restarts})")
            return False

        if metrics.last_restart and current_time - metrics.last_restart < config.restart_delay:
            logger.warning(f"Task {task_name} is in restart cooldown")
            return False

        # Find and validate the cog and task
        cog = self.bot.cogs.get(config.cog_name)
        if not cog:
            logger.error(f"Cog {config.cog_name} not found for task {task_name}")
            return False

        task_loop = getattr(cog, config.task_attr, None)
        if not isinstance(task_loop, tasks.Loop):
            logger.error(f"Task {config.task_attr} not found in cog {config.cog_name}")
            return False

        # Attempt restart
        try:
            if task_loop.is_running():
                task_loop.restart()
            else:
                task_loop.start()
        except Exception as e:
            logger.error(f"Failed to restart task {task_name}: {e}")
            self.bot.sentry_manager.capture_exception(e)
            return False
        else:
            # Update metrics on successful restart
            metrics.restart_count += 1
            metrics.last_restart = current_time
            metrics.start_time = current_time

            logger.info(f"Successfully restarted critical task: {task_name}")
            return True

    async def cancel_all_tasks(self) -> None:
        """
        Gracefully cancels all managed asyncio tasks with priority ordering.

        This is the main entrypoint for the shutdown process. It stops all
        `discord.ext.tasks` loops and then proceeds to cancel all other
        categorized tasks in priority order.
        """
        with start_span("bot.cleanup_tasks", "Cleaning up running tasks"):
            try:
                await self._stop_task_loops()

                all_tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
                tasks_by_type = self._categorize_tasks(all_tasks)

                # Cancel tasks in priority order (low priority first)
                await self._cancel_tasks_by_priority(tasks_by_type)

            except Exception as e:
                logger.error(f"Error during task cleanup: {e}")
                self.bot.sentry_manager.capture_exception(e)

    # --- Monitoring Loop ---

    @tasks.loop(seconds=60)
    async def _monitor_tasks_loop(self) -> None:
        """
        Enhanced task monitoring with health checks and metrics collection.

        This loop runs every 60 seconds to gather all tasks, categorize them,
        handle finished tasks, perform health checks, and collect metrics.

        Raises
        ------
        RuntimeError
            If a critical, unhandled exception occurs during task monitoring.
        """
        with start_span("bot.monitor_tasks", "Monitoring async tasks"):
            try:
                current_time = time.time()
                all_tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
                tasks_by_type = self._categorize_tasks(all_tasks)

            except Exception as e:
                logger.error(f"Error during task categorization: {e}")
                self.bot.sentry_manager.capture_exception(e)
                return

            try:
                await self._process_finished_tasks(tasks_by_type)
            except Exception as e:
                logger.error(f"Error processing finished tasks: {e}")
                self.bot.sentry_manager.capture_exception(e)

            try:
                self._update_task_metrics(tasks_by_type, current_time)
            except Exception as e:
                logger.error(f"Error updating task metrics: {e}")
                self.bot.sentry_manager.capture_exception(e)

            try:
                if current_time - self.last_health_check > self.health_check_interval:
                    await self._perform_health_checks()
                    self.last_health_check = current_time
            except Exception as e:
                logger.error(f"Error performing health checks: {e}")
                self.bot.sentry_manager.capture_exception(e)

    # --- Task Categorization & Processing ---

    def _categorize_tasks(self, tasks: list[asyncio.Task[Any]]) -> dict[TaskCategory, list[asyncio.Task[Any]]]:
        """
        Categorizes a list of tasks based on their names.

        Parameters
        ----------
        tasks : list[asyncio.Task[Any]]
            The list of asyncio tasks to categorize.

        Returns
        -------
        dict[TaskCategory, list[asyncio.Task[Any]]]
            A dictionary mapping each task category to a list of tasks.
        """
        tasks_by_type: dict[TaskCategory, list[asyncio.Task[Any]]] = {category: [] for category in TaskCategory}

        for task in tasks:
            if task.done():
                continue

            name = self._get_task_name(task)
            category = self._get_task_category(name)
            tasks_by_type.setdefault(category, []).append(task)

        if unknown_tasks := tasks_by_type.get(TaskCategory.UNKNOWN):
            task_names = [self._get_task_name(t) for t in unknown_tasks]
            logger.warning(f"Found {len(unknown_tasks)} uncategorized tasks: {', '.join(task_names)}")

        return tasks_by_type

    def _get_task_category(self, name: str) -> TaskCategory:
        """
        Determines the category of a task from its name.

        It first checks against the `TASK_PREFIX_MAP` for known system/library
        tasks, then checks for command-related tasks, and finally defaults
        to a general system task.

        Parameters
        ----------
        name : str
            The name of the asyncio task.

        Returns
        -------
        TaskCategory
            The determined category for the task.
        """
        if name in self.critical_tasks:
            return TaskCategory.SCHEDULED

        # Default asyncio tasks (e.g., Task-1) are considered SYSTEM tasks.
        if name.startswith("Task-"):
            return TaskCategory.SYSTEM

        return next(
            (
                category
                for prefixes, category in self.TASK_PREFIX_MAP.items()
                if any(name.startswith(p) for p in prefixes)
            ),
            (TaskCategory.COMMAND if "command_" in name.lower() else TaskCategory.UNKNOWN),
        )

    async def _process_finished_tasks(self, tasks_by_type: dict[TaskCategory, list[asyncio.Task[Any]]]) -> None:
        """
        Awaits any tasks that have already completed to handle their results.

        This is important for preventing "awaitable was never awaited" warnings
        and ensuring that exceptions from completed tasks are raised and logged.

        Parameters
        ----------
        tasks_by_type : dict[TaskCategory, list[asyncio.Task[Any]]]
            A dictionary of tasks, categorized by type.
        """
        for task_list in tasks_by_type.values():
            for task in task_list:
                if task.done():
                    with contextlib.suppress(asyncio.CancelledError):
                        try:
                            await task
                        except Exception as e:
                            # Log task exceptions and update metrics
                            logger.error(f"Task {(task_name := self._get_task_name(task))} failed with exception: {e}")
                            self._record_task_error(task_name, str(e))

    def _update_task_metrics(
        self,
        tasks_by_type: dict[TaskCategory, list[asyncio.Task[Any]]],
        current_time: float,
    ) -> None:
        """
        Update metrics for all running tasks.

        Parameters
        ----------
        tasks_by_type : dict[TaskCategory, list[asyncio.Task[Any]]]
            Categorized tasks.
        current_time : float
            Current timestamp.
        """
        # Update runtime metrics for critical tasks
        for task_name, config in self.critical_tasks.items():
            if cog := self.bot.cogs.get(config.cog_name):
                task_loop = getattr(cog, config.task_attr, None)
                if isinstance(task_loop, tasks.Loop) and task_loop.is_running():
                    metrics = self.task_metrics[task_name]
                    metrics.total_runtime = current_time - metrics.start_time
                    self.task_history[task_name].append(current_time)

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all critical tasks."""
        unhealthy_tasks: list[str] = []

        for task_name, config in self.critical_tasks.items():
            cog = self.bot.cogs.get(config.cog_name)
            if not cog:
                logger.warning(f"Cog {config.cog_name} not found for critical task {task_name}")
                continue

            task_loop = getattr(cog, config.task_attr, None)
            if not isinstance(task_loop, tasks.Loop):
                logger.warning(f"Task {config.task_attr} not found in cog {config.cog_name}")
                continue

            # Check if task is running
            if not task_loop.is_running():
                logger.warning(f"Critical task {task_name} is not running")
                unhealthy_tasks.append(task_name)
                continue

            # Check task health
            health = self.get_task_health(task_name)
            if health and not health.is_healthy:
                logger.warning(f"Critical task {task_name} is unhealthy: {health}")
                unhealthy_tasks.append(task_name)

        # Attempt to restart unhealthy critical tasks
        for task_name in unhealthy_tasks:
            if await self.restart_critical_task(task_name):
                logger.info(f"Successfully recovered unhealthy task: {task_name}")

    def _record_task_error(self, task_name: str, error_msg: str) -> None:
        """
        Record an error for a task.

        Parameters
        ----------
        task_name : str
            The name of the task.
        error_msg : str
            The error message.
        """
        if task_name in self.task_metrics:
            metrics = self.task_metrics[task_name]
            metrics.error_count += 1
            metrics.last_error = error_msg
            metrics.last_error_time = time.time()

    # --- Shutdown & Cleanup ---

    async def _stop_task_loops(self) -> None:
        """
        Stops all registered `discord.ext.tasks.Loop` instances in all cogs.

        This is a critical first step in the cleanup process to prevent new
        tasks from being created while shutdown is in progress.
        """
        with start_span("bot.stop_task_loops", "Stopping task loops"):
            for cog_name, cog in self.bot.cogs.items():
                if not cog:
                    continue

                for name, value in cog.__dict__.items():
                    if isinstance(value, tasks.Loop):
                        try:
                            value.stop()
                            logger.debug(f"Stopped task loop {cog_name}.{name}")
                        except Exception as e:
                            logger.error(f"Error stopping task loop {cog_name}.{name}: {e}")

            # Only stop the monitor loop if all cog tasks were processed without critical errors
            if self._monitor_tasks_loop.is_running():
                self._monitor_tasks_loop.stop()

    @staticmethod
    def _get_task_name(task: asyncio.Task[Any]) -> str:
        """
        Gets a descriptive name for an asyncio task.

        If a task was not explicitly named, it attempts to derive a name
        from its coroutine object for better logging.

        Parameters
        ----------
        task : asyncio.Task[Any]
            The asyncio task to get the name from.

        Returns
        -------
        str
            A descriptive name for the task.
        """
        name = task.get_name() or "unnamed"
        if name in ("None", "unnamed"):
            coro = task.get_coro()
            name = getattr(coro, "__qualname__", str(coro))
        return name

    async def _cancel_tasks_by_priority(self, tasks_by_type: dict[TaskCategory, list[asyncio.Task[Any]]]) -> None:
        """
        Cancel tasks in priority order (low priority first).

        Parameters
        ----------
        tasks_by_type : dict[TaskCategory, list[asyncio.Task[Any]]]
            The dictionary of tasks to be cancelled.
        """
        # Define shutdown priority order (low priority first)
        shutdown_order = [
            TaskCategory.UNKNOWN,
            TaskCategory.COMMAND,
            TaskCategory.SYSTEM,
            TaskCategory.SCHEDULED,
            TaskCategory.GATEWAY,
        ]

        with start_span("bot.cancel_tasks", "Cancelling tasks by priority") as span:
            for category in shutdown_order:
                task_list = tasks_by_type.get(category, [])
                if not task_list:
                    continue

                task_names = [self._get_task_name(t) for t in task_list]
                names = ", ".join(task_names)

                logger.debug(f"Cancelling {len(task_list)} {category.name}: {names}")
                span.set_data(f"tasks.{category.name.lower()}", task_names)

                for task in task_list:
                    task.cancel()

                results = await asyncio.gather(*task_list, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                        logger.error(f"Exception during task cancellation for {category.name}: {result!r}")

                logger.debug(f"Cancelled {category.name}")

    async def _cancel_tasks(self, tasks_by_type: dict[TaskCategory, list[asyncio.Task[Any]]]) -> None:
        """
        Legacy method - redirects to priority-based cancellation.

        Parameters
        ----------
        tasks_by_type : dict[TaskCategory, list[asyncio.Task[Any]]]
            The dictionary of tasks to be cancelled.
        """
        await self._cancel_tasks_by_priority(tasks_by_type)
