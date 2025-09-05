"""
Monitoring and audit system for moderation operations.

Provides comprehensive tracking, metrics collection, and audit trail logging.
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


@dataclass
class OperationMetrics:
    """Metrics for a specific operation type."""

    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    average_response_time: float = 0.0
    last_operation_time: float = 0.0
    error_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    response_times: deque[float] = field(default_factory=lambda: deque(maxlen=100))


@dataclass
class ModerationAuditEvent:
    """Audit event for moderation operations."""

    timestamp: float
    operation_type: str
    user_id: int
    moderator_id: int
    guild_id: int
    case_type: str
    success: bool
    response_time: float
    error_message: str | None = None
    dm_sent: bool = False
    case_created: bool = False
    case_number: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ModerationMonitor:
    """
    Monitors moderation operations and maintains audit trails.

    Tracks performance metrics, error rates, and provides comprehensive
    logging for moderation system operations.
    """

    def __init__(self, max_audit_history: int = 1000):
        self._max_audit_history = max_audit_history
        self._metrics: dict[str, OperationMetrics] = {}
        self._audit_log: deque[ModerationAuditEvent] = deque(maxlen=max_audit_history)
        self._lock_contention_count: int = 0
        self._circuit_breaker_trips: dict[str, int] = defaultdict(int)

    def start_operation(self, operation_type: str) -> float:
        """
        Mark the start of a moderation operation.

        Parameters
        ----------
        operation_type : str
            Type of operation being started

        Returns
        -------
        float
            Start timestamp for duration calculation
        """
        start_time = time.time()

        if operation_type not in self._metrics:
            self._metrics[operation_type] = OperationMetrics()

        self._metrics[operation_type].total_operations += 1
        self._metrics[operation_type].last_operation_time = start_time

        logger.debug(f"Started {operation_type} operation")
        return start_time

    def end_operation(
        self,
        operation_type: str,
        start_time: float,
        success: bool,
        error_message: str | None = None,
        **metadata: Any,
    ) -> None:
        """
        Mark the end of a moderation operation and record metrics.

        Parameters
        ----------
        operation_type : str
            Type of operation that completed
        start_time : float
            Start timestamp from start_operation
        success : bool
            Whether the operation was successful
        error_message : str | None
            Error message if operation failed
        **metadata : Any
            Additional metadata to record
        """
        end_time = time.time()
        response_time = end_time - start_time

        if operation_type not in self._metrics:
            self._metrics[operation_type] = OperationMetrics()

        metrics = self._metrics[operation_type]

        if success:
            metrics.successful_operations += 1
        else:
            metrics.failed_operations += 1
            if error_message:
                # Extract error type for categorization
                if isinstance(error_message, str):  # type: ignore
                    # Try to extract error type from message
                    if ":" in error_message:
                        error_type = error_message.split(":")[0].strip()
                    else:
                        # Use the whole message or first few words
                        words = error_message.split()
                        error_type = words[0] if words else "Unknown"
                else:
                    error_type = type(error_message).__name__
                metrics.error_counts[error_type] += 1

        # Update response time metrics
        metrics.response_times.append(response_time)
        metrics.average_response_time = sum(metrics.response_times) / len(metrics.response_times)

        logger.info(
            f"Completed {operation_type} operation in {response_time:.3f}s - {'SUCCESS' if success else 'FAILED'}",
        )

        if not success and error_message:
            logger.warning(f"{operation_type} failed: {error_message}")

    def record_audit_event(self, event: ModerationAuditEvent) -> None:
        """
        Record a moderation audit event.

        Parameters
        ----------
        event : ModerationAuditEvent
            The audit event to record
        """
        self._audit_log.append(event)

        # Log significant events
        if not event.success:
            logger.error(
                f"AUDIT: Failed {event.operation_type} on user {event.user_id} "
                f"by moderator {event.moderator_id} in guild {event.guild_id} - {event.error_message}",
            )
        elif event.case_type in ["BAN", "KICK", "TEMPBAN"]:
            # Log significant moderation actions
            logger.info(
                f"AUDIT: {event.case_type} case #{event.case_number} created for user {event.user_id} "
                f"by moderator {event.moderator_id} in guild {event.guild_id} "
                f"(DM sent: {event.dm_sent})",
            )

    def record_lock_contention(self) -> None:
        """Record an instance of lock contention."""
        self._lock_contention_count += 1
        logger.debug("Lock contention detected")

    def record_circuit_breaker_trip(self, operation_type: str) -> None:
        """Record a circuit breaker trip."""
        self._circuit_breaker_trips[operation_type] += 1
        logger.warning(f"Circuit breaker tripped for {operation_type}")

    def get_operation_metrics(self, operation_type: str) -> OperationMetrics | None:
        """Get metrics for a specific operation type."""
        return self._metrics.get(operation_type)

    def get_all_metrics(self) -> dict[str, OperationMetrics]:
        """Get metrics for all operation types."""
        return self._metrics.copy()

    def get_audit_log(self, limit: int | None = None) -> list[ModerationAuditEvent]:
        """Get recent audit events."""
        if limit is None:
            return list(self._audit_log)
        return list(self._audit_log)[-limit:]

    def get_error_summary(self, operation_type: str | None = None) -> dict[str, Any]:
        """Get error summary statistics."""
        if operation_type:
            metrics = self._metrics.get(operation_type)
            if not metrics:
                return {}
            return {
                "total_operations": metrics.total_operations,
                "error_rate": metrics.failed_operations / max(metrics.total_operations, 1),
                "error_counts": dict(metrics.error_counts),
                "most_common_error": max(metrics.error_counts.items(), key=lambda x: x[1], default=(None, 0))[0],
            }

        # Aggregate across all operation types
        total_ops = sum(m.total_operations for m in self._metrics.values())
        total_errors = sum(m.failed_operations for m in self._metrics.values())
        all_errors: defaultdict[str, int] = defaultdict(int)
        for metrics in self._metrics.values():
            for error_type, count in metrics.error_counts.items():
                all_errors[error_type] += count

        return {  # type: ignore
            "total_operations": total_ops,
            "error_rate": total_errors / max(total_ops, 1),
            "error_counts": dict(all_errors),  # type: ignore
            "most_common_error": max(all_errors.items(), key=lambda x: x[1], default=(None, 0))[0],  # type: ignore
        }

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary across all operations."""
        summaries = {}
        for op_type, metrics in self._metrics.items():
            summaries[op_type] = {
                "total_operations": metrics.total_operations,
                "success_rate": metrics.successful_operations / max(metrics.total_operations, 1),
                "average_response_time": metrics.average_response_time,
                "operations_per_minute": (
                    metrics.total_operations / max(time.time() - (metrics.last_operation_time - 3600), 3600) * 60
                ),
            }

        return summaries  # type: ignore

    def get_system_health(self) -> dict[str, Any]:
        """Get overall system health metrics."""
        total_ops = sum(m.total_operations for m in self._metrics.values())
        total_success = sum(m.successful_operations for m in self._metrics.values())
        avg_response_time = sum(m.average_response_time * m.total_operations for m in self._metrics.values()) / max(
            total_ops,
            1,
        )

        return {
            "overall_success_rate": total_success / max(total_ops, 1),
            "average_response_time": avg_response_time,
            "lock_contention_count": self._lock_contention_count,
            "circuit_breaker_trips": dict(self._circuit_breaker_trips),
            "active_operation_types": len(self._metrics),
            "audit_log_size": len(self._audit_log),
        }

    def clear_old_data(self, max_age_hours: float = 24.0) -> None:
        """Clear old audit data to prevent memory bloat."""
        cutoff_time = time.time() - (max_age_hours * 3600)

        # Clear old audit events
        original_size = len(self._audit_log)
        self._audit_log = deque(
            (event for event in self._audit_log if event.timestamp > cutoff_time),
            maxlen=self._audit_log.maxlen,
        )

        removed_count = original_size - len(self._audit_log)
        if removed_count > 0:
            logger.info(f"Cleared {removed_count} old audit events")

        # Reset circuit breaker counts periodically
        self._circuit_breaker_trips.clear()
        self._lock_contention_count = 0


# Global instance for the moderation system
moderation_monitor = ModerationMonitor()
