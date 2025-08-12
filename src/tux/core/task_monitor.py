"""Task monitoring and cleanup utilities for the Tux bot.

Encapsulates background task monitoring and shutdown cleanup routines.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from discord.ext import tasks
from loguru import logger

from tux.services.tracing import capture_exception_safe, start_span


class TaskMonitor:
    """Manage monitoring and cleanup of asyncio tasks for a bot instance."""

    def __init__(self, bot: Any) -> None:
        self.bot = bot
        # Create the background monitor loop bound to this instance
        self._monitor_loop = tasks.loop(seconds=60)(self._monitor_tasks_loop_impl)

    def start(self) -> None:
        """Start the background task monitoring loop."""
        self._monitor_loop.start()
        logger.debug("Task monitoring started")

    def stop(self) -> None:
        """Stop the background task monitoring loop if running."""
        if self._monitor_loop.is_running():
            self._monitor_loop.stop()

    async def _monitor_tasks_loop_impl(self) -> None:
        """Monitor and clean up running tasks periodically."""
        with start_span("bot.monitor_tasks", "Monitoring async tasks"):
            try:
                all_tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
                tasks_by_type = self._categorize_tasks(all_tasks)
                await self._process_finished_tasks(tasks_by_type)
            except Exception as e:
                logger.error(f"Task monitoring failed: {e}")
                capture_exception_safe(e)
                msg = "Critical failure in task monitoring system"
                raise RuntimeError(msg) from e

    def _categorize_tasks(self, tasks_list: list[asyncio.Task[Any]]) -> dict[str, list[asyncio.Task[Any]]]:
        """Categorize tasks by type for monitoring and cleanup."""
        tasks_by_type: dict[str, list[asyncio.Task[Any]]] = {
            "SCHEDULED": [],
            "GATEWAY": [],
            "SYSTEM": [],
            "COMMAND": [],
        }

        for task in tasks_list:
            if task.done():
                continue

            name = task.get_name()

            if name.startswith("discord-ext-tasks:"):
                tasks_by_type["SCHEDULED"].append(task)
            elif name.startswith(("discord.py:", "discord-voice-", "discord-gateway-")):
                tasks_by_type["GATEWAY"].append(task)
            elif "command_" in name.lower():
                tasks_by_type["COMMAND"].append(task)
            else:
                tasks_by_type["SYSTEM"].append(task)

        return tasks_by_type

    async def _process_finished_tasks(self, tasks_by_type: dict[str, list[asyncio.Task[Any]]]) -> None:
        """Process and clean up finished tasks."""
        for task_list in tasks_by_type.values():
            for task in task_list:
                if task.done():
                    with contextlib.suppress(asyncio.CancelledError):
                        await task

    async def cleanup_tasks(self) -> None:
        """Clean up all running tasks across the bot and cogs."""
        with start_span("bot.cleanup_tasks", "Cleaning up running tasks"):
            try:
                await self._stop_task_loops()

                all_tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
                tasks_by_type = self._categorize_tasks(all_tasks)

                await self._cancel_tasks(tasks_by_type)
            except Exception as e:
                logger.error(f"Error during task cleanup: {e}")
                capture_exception_safe(e)

    async def _stop_task_loops(self) -> None:
        """Stop all task loops in cogs as well as the monitor loop itself."""
        with start_span("bot.stop_task_loops", "Stopping task loops"):
            for cog_name in self.bot.cogs:
                cog = self.bot.get_cog(cog_name)
                if not cog:
                    continue

                for name, value in cog.__dict__.items():
                    if isinstance(value, tasks.Loop):
                        try:
                            value.stop()
                            logger.debug(f"Stopped task loop {cog_name}.{name}")
                        except Exception as e:
                            logger.error(f"Error stopping task loop {cog_name}.{name}: {e}")

            if self._monitor_loop.is_running():
                self._monitor_loop.stop()

    async def _cancel_tasks(self, tasks_by_type: dict[str, list[asyncio.Task[Any]]]) -> None:
        """Cancel tasks by category and await their completion."""
        with start_span("bot.cancel_tasks", "Cancelling tasks by category") as span:
            for task_type, task_list in tasks_by_type.items():
                if not task_list:
                    continue

                task_names: list[str] = []
                for t in task_list:
                    name = t.get_name() or "unnamed"
                    if name in ("None", "unnamed"):
                        coro = t.get_coro()
                        name = getattr(coro, "__qualname__", str(coro))
                    task_names.append(name)

                logger.debug(f"Cancelling {len(task_list)} {task_type}: {', '.join(task_names)}")
                span.set_data(f"tasks.{task_type.lower()}", task_names)

                for task in task_list:
                    task.cancel()

                results = await asyncio.gather(*task_list, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                        logger.error(f"Exception during task cancellation for {task_type}: {result!r}")
