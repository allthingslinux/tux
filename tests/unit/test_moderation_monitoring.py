"""
🚀 Moderation Monitoring Unit Tests - Audit System Testing

Tests for the ModerationMonitor that handles performance metrics,
error tracking, and audit trail logging for moderation operations.

Test Coverage:
- Operation metrics collection
- Audit event recording
- Error rate calculation
- Performance summary generation
- System health monitoring
- Old data cleanup
- Circuit breaker trip recording
- Lock contention tracking
"""

import time
from collections import deque
from unittest.mock import MagicMock

import pytest

from tux.services.moderation.monitoring import (
    ModerationMonitor,
    ModerationAuditEvent,
    OperationMetrics,
)


class TestModerationMonitor:
    """📊 Test ModerationMonitor functionality."""

    @pytest.fixture
    def monitor(self) -> ModerationMonitor:
        """Create a ModerationMonitor instance for testing."""
        return ModerationMonitor(max_audit_history=50)  # Small history for testing

    @pytest.mark.unit
    async def test_start_operation_basic(self, monitor: ModerationMonitor) -> None:
        """Test basic operation start tracking."""
        operation_type = "ban_kick"
        start_time = monitor.start_operation(operation_type)

        assert isinstance(start_time, float)
        assert operation_type in monitor._metrics
        assert monitor._metrics[operation_type].total_operations == 1
        assert monitor._metrics[operation_type].last_operation_time == start_time

    @pytest.mark.unit
    async def test_end_operation_success(self, monitor: ModerationMonitor) -> None:
        """Test successful operation completion tracking."""
        operation_type = "ban_kick"
        start_time = monitor.start_operation(operation_type)

        # Simulate some response time
        time.sleep(0.01)

        monitor.end_operation(operation_type, start_time, True)

        metrics = monitor._metrics[operation_type]
        assert metrics.successful_operations == 1
        assert metrics.failed_operations == 0
        assert metrics.average_response_time > 0
        assert len(metrics.response_times) == 1

    @pytest.mark.unit
    async def test_end_operation_failure(self, monitor: ModerationMonitor) -> None:
        """Test failed operation tracking."""
        operation_type = "timeout"
        start_time = monitor.start_operation(operation_type)
        error_message = "Rate limit exceeded"

        monitor.end_operation(operation_type, start_time, False, error_message)

        metrics = monitor._metrics[operation_type]
        assert metrics.successful_operations == 0
        assert metrics.failed_operations == 1
        assert "Rate" in metrics.error_counts  # Should extract "Rate" from "Rate limit exceeded"
        assert metrics.error_counts["Rate"] == 1

    @pytest.mark.unit
    async def test_end_operation_multiple_calls(self, monitor: ModerationMonitor) -> None:
        """Test multiple operation calls and metric aggregation."""
        operation_type = "messages"

        # First operation - success
        start1 = monitor.start_operation(operation_type)
        monitor.end_operation(operation_type, start1, True)

        # Second operation - failure
        start2 = monitor.start_operation(operation_type)
        monitor.end_operation(operation_type, start2, False, "Network error")

        # Third operation - success
        start3 = monitor.start_operation(operation_type)
        monitor.end_operation(operation_type, start3, True)

        metrics = monitor._metrics[operation_type]
        assert metrics.total_operations == 3
        assert metrics.successful_operations == 2
        assert metrics.failed_operations == 1
        assert metrics.error_counts["Network"] == 1
        assert len(metrics.response_times) == 3

    @pytest.mark.unit
    async def test_record_audit_event_success(self, monitor: ModerationMonitor) -> None:
        """Test successful audit event recording."""
        event = ModerationAuditEvent(
            timestamp=time.time(),
            operation_type="ban_kick",
            user_id=123456789,
            moderator_id=987654321,
            guild_id=111111111,
            case_type="BAN",
            success=True,
            response_time=0.5,
            dm_sent=True,
            case_created=True,
            case_number=42,
        )

        monitor.record_audit_event(event)

        assert len(monitor._audit_log) == 1
        logged_event = monitor._audit_log[0]
        assert logged_event.operation_type == "ban_kick"
        assert logged_event.success is True
        assert logged_event.dm_sent is True

    @pytest.mark.unit
    async def test_record_audit_event_failure(self, monitor: ModerationMonitor) -> None:
        """Test failed audit event recording and error logging."""
        event = ModerationAuditEvent(
            timestamp=time.time(),
            operation_type="timeout",
            user_id=123456789,
            moderator_id=987654321,
            guild_id=111111111,
            case_type="TIMEOUT",
            success=False,
            response_time=2.0,
            error_message="Rate limit exceeded",
        )

        monitor.record_audit_event(event)

        assert len(monitor._audit_log) == 1
        logged_event = monitor._audit_log[0]
        assert logged_event.success is False
        assert logged_event.error_message == "Rate limit exceeded"

    @pytest.mark.unit
    async def test_audit_log_size_limit(self, monitor: ModerationMonitor) -> None:
        """Test that audit log respects size limits."""
        # Fill the audit log to capacity
        for i in range(55):  # More than max_audit_history (50)
            event = ModerationAuditEvent(
                timestamp=time.time(),
                operation_type=f"op_{i}",
                user_id=i,
                moderator_id=i + 1000,
                guild_id=111111111,
                case_type="WARN",
                success=True,
                response_time=0.1,
            )
            monitor.record_audit_event(event)

        # Should only keep the most recent 50 events
        assert len(monitor._audit_log) == 50

    @pytest.mark.unit
    async def test_get_operation_metrics_existing(self, monitor: ModerationMonitor) -> None:
        """Test getting metrics for existing operation type."""
        operation_type = "ban_kick"
        monitor.start_operation(operation_type)
        monitor.end_operation(operation_type, time.time(), True)

        metrics = monitor.get_operation_metrics(operation_type)

        assert metrics is not None
        assert isinstance(metrics, OperationMetrics)
        assert metrics.total_operations == 1

    @pytest.mark.unit
    async def test_get_operation_metrics_nonexistent(self, monitor: ModerationMonitor) -> None:
        """Test getting metrics for non-existent operation type."""
        metrics = monitor.get_operation_metrics("nonexistent")

        assert metrics is None

    @pytest.mark.unit
    async def test_get_all_metrics(self, monitor: ModerationMonitor) -> None:
        """Test getting all operation metrics."""
        # Add some metrics
        monitor.start_operation("ban_kick")
        monitor.end_operation("ban_kick", time.time(), True)

        monitor.start_operation("timeout")
        monitor.end_operation("timeout", time.time(), False, "Error")

        all_metrics = monitor.get_all_metrics()

        assert isinstance(all_metrics, dict)
        assert "ban_kick" in all_metrics
        assert "timeout" in all_metrics
        assert len(all_metrics) == 2

    @pytest.mark.unit
    async def test_get_audit_log_all(self, monitor: ModerationMonitor) -> None:
        """Test getting all audit log events."""
        # Add some events
        for i in range(3):
            event = ModerationAuditEvent(
                timestamp=time.time(),
                operation_type=f"test_{i}",
                user_id=i,
                moderator_id=i + 10,
                guild_id=111111111,
                case_type="NOTE",
                success=True,
                response_time=0.1,
            )
            monitor.record_audit_event(event)

        audit_log = monitor.get_audit_log()

        assert len(audit_log) == 3
        assert all(isinstance(event, ModerationAuditEvent) for event in audit_log)

    @pytest.mark.unit
    async def test_get_audit_log_limited(self, monitor: ModerationMonitor) -> None:
        """Test getting limited number of audit log events."""
        # Add many events
        for i in range(10):
            event = ModerationAuditEvent(
                timestamp=time.time(),
                operation_type=f"test_{i}",
                user_id=i,
                moderator_id=i + 10,
                guild_id=111111111,
                case_type="WARN",
                success=True,
                response_time=0.1,
            )
            monitor.record_audit_event(event)

        audit_log = monitor.get_audit_log(limit=5)

        assert len(audit_log) == 5

    @pytest.mark.unit
    async def test_get_error_summary_specific_operation(self, monitor: ModerationMonitor) -> None:
        """Test error summary for specific operation type."""
        operation_type = "messages"

        # Add mix of success and failures
        monitor.start_operation(operation_type)
        monitor.end_operation(operation_type, time.time(), True)   # Success
        monitor.start_operation(operation_type)
        monitor.end_operation(operation_type, time.time(), False, "Network error")  # Failure
        monitor.start_operation(operation_type)
        monitor.end_operation(operation_type, time.time(), False, "Timeout")       # Failure
        monitor.start_operation(operation_type)
        monitor.end_operation(operation_type, time.time(), False, "Network error") # Another network error

        summary = monitor.get_error_summary(operation_type)

        assert summary["total_operations"] == 4
        assert summary["error_rate"] == 0.75  # 3 failures out of 4
        assert summary["error_counts"]["Network"] == 2
        assert summary["error_counts"]["Timeout"] == 1
        assert summary["most_common_error"] == "Network"

    @pytest.mark.unit
    async def test_get_error_summary_all_operations(self, monitor: ModerationMonitor) -> None:
        """Test error summary across all operation types."""
        # Add errors to different operations
        monitor.start_operation("ban_kick")
        monitor.end_operation("ban_kick", time.time(), False, "Permission denied")
        monitor.start_operation("timeout")
        monitor.end_operation("timeout", time.time(), False, "Rate limit")
        monitor.start_operation("messages")
        monitor.end_operation("messages", time.time(), False, "Permission denied")

        summary = monitor.get_error_summary()

        assert summary["total_operations"] == 3
        assert summary["error_rate"] == 1.0
        assert summary["error_counts"]["Permission"] == 2
        assert summary["most_common_error"] == "Permission"

    @pytest.mark.unit
    async def test_get_performance_summary(self, monitor: ModerationMonitor) -> None:
        """Test performance summary generation."""
        # Simulate some operations with timing
        start_time = monitor.start_operation("ban_kick")
        time.sleep(0.01)  # Simulate 10ms operation
        monitor.end_operation("ban_kick", start_time, True)

        start_time = monitor.start_operation("ban_kick")
        time.sleep(0.02)  # Simulate 20ms operation
        monitor.end_operation("ban_kick", start_time, False, "Error")

        summary = monitor.get_performance_summary()

        assert "ban_kick" in summary
        ban_kick_stats = summary["ban_kick"]
        assert ban_kick_stats["total_operations"] == 2
        assert ban_kick_stats["success_rate"] == 0.5
        assert ban_kick_stats["average_response_time"] > 0

    @pytest.mark.unit
    async def test_get_system_health(self, monitor: ModerationMonitor) -> None:
        """Test system health metrics generation."""
        # Add some test data
        monitor.start_operation("ban_kick")
        monitor.end_operation("ban_kick", time.time(), True)
        monitor.start_operation("timeout")
        monitor.end_operation("timeout", time.time(), False, "Error")
        monitor.record_lock_contention()
        monitor.record_lock_contention()
        monitor.record_circuit_breaker_trip("ban_kick")

        health = monitor.get_system_health()

        assert isinstance(health, dict)
        assert "overall_success_rate" in health
        assert "average_response_time" in health
        assert "lock_contention_count" in health
        assert "circuit_breaker_trips" in health
        assert "active_operation_types" in health
        assert "audit_log_size" in health

        assert health["lock_contention_count"] == 2
        assert health["circuit_breaker_trips"]["ban_kick"] == 1

    @pytest.mark.unit
    async def test_record_lock_contention(self, monitor: ModerationMonitor) -> None:
        """Test lock contention recording."""
        initial_count = monitor._lock_contention_count

        monitor.record_lock_contention()
        monitor.record_lock_contention()
        monitor.record_lock_contention()

        assert monitor._lock_contention_count == initial_count + 3

    @pytest.mark.unit
    async def test_record_circuit_breaker_trip(self, monitor: ModerationMonitor) -> None:
        """Test circuit breaker trip recording."""
        operation_type = "test_operation"

        monitor.record_circuit_breaker_trip(operation_type)
        monitor.record_circuit_breaker_trip(operation_type)
        monitor.record_circuit_breaker_trip("other_operation")

        assert monitor._circuit_breaker_trips[operation_type] == 2
        assert monitor._circuit_breaker_trips["other_operation"] == 1

    @pytest.mark.unit
    async def test_clear_old_data(self, monitor: ModerationMonitor) -> None:
        """Test old data cleanup functionality."""
        # Add some old audit events (simulate old timestamps)
        old_time = time.time() - (25 * 3600)  # 25 hours ago

        for i in range(10):
            event = ModerationAuditEvent(
                timestamp=old_time - i,
                operation_type=f"old_op_{i}",
                user_id=i,
                moderator_id=i + 100,
                guild_id=111111111,
                case_type="NOTE",
                success=True,
                response_time=0.1,
            )
            monitor.record_audit_event(event)

        # Add some recent events
        for i in range(5):
            event = ModerationAuditEvent(
                timestamp=time.time(),
                operation_type=f"recent_op_{i}",
                user_id=i + 1000,
                moderator_id=i + 1100,
                guild_id=111111111,
                case_type="WARN",
                success=True,
                response_time=0.1,
            )
            monitor.record_audit_event(event)

        original_size = len(monitor._audit_log)

        # Clear old data (24 hour default cutoff)
        monitor.clear_old_data()

        # Should have removed old events but kept recent ones
        assert len(monitor._audit_log) < original_size
        assert len(monitor._audit_log) >= 5  # At least the recent events

        # Circuit breaker counts should be reset
        assert len(monitor._circuit_breaker_trips) == 0
        assert monitor._lock_contention_count == 0

    @pytest.mark.unit
    async def test_clear_old_data_custom_age(self, monitor: ModerationMonitor) -> None:
        """Test old data cleanup with custom age limit."""
        # Add events with different ages
        for hours_ago in [1, 5, 10, 20, 30]:
            event = ModerationAuditEvent(
                timestamp=time.time() - (hours_ago * 3600),
                operation_type=f"op_{hours_ago}h",
                user_id=hours_ago,
                moderator_id=hours_ago + 100,
                guild_id=111111111,
                case_type="NOTE",
                success=True,
                response_time=0.1,
            )
            monitor.record_audit_event(event)

        # Clear events older than 12 hours
        monitor.clear_old_data(max_age_hours=12.0)

        # Should keep events from 1h, 5h, 10h ago, remove 20h and 30h
        remaining_events = [e for e in monitor._audit_log if e.timestamp > time.time() - (12 * 3600)]
        assert len(remaining_events) == 3

    @pytest.mark.unit
    async def test_monitor_initialization(self) -> None:
        """Test ModerationMonitor initialization."""
        monitor = ModerationMonitor(max_audit_history=100)

        assert monitor._max_audit_history == 100
        assert isinstance(monitor._metrics, dict)
        assert isinstance(monitor._audit_log, deque)
        assert monitor._lock_contention_count == 0
        assert isinstance(monitor._circuit_breaker_trips, dict)
