# Observability Best Practices Guide

## Overview

This guide provides comprehensive best practices for implementing and maintaining observability in the Tux Discord bot. It covers the three pillars of observability: metrics, logs, and traces, along with practical implementation guidelines and standards.

## Core Principles

### The Three Pillars of Observability

1. **Metrics**: Numerical data about system behavior over time
2. **Logs**: Detailed records of discrete events that happened
3. **Traces**: Information about the flow of requests through distributed systems

### The Four Golden Signals

1. **Latency**: How long it takes to service a request
2. **Traffic**: How much demand is being placed on your system
3. **Errors**: The rate of requests that fail
4. **Saturation**: How "full" yis

## Metrics Best Practices

### Naming Conventions

#### Standard Format

- **Prefix**: All metrics should start with `tux_`
- **Format**: Use snake_case for metric names
- **Units**: Include units in metric names where applicable

#### Unit Suffixes

```
_seconds      # For duration measurements
_bytes        # For size measurements
_total        # For counters
_per_second   # For rates
_percent      # For percentages
```

#### Examples

```python
# Good metric names
tux_commands_total{command="ban", status="success"}
tux_command_duration_seconds{command="ban"}
tux_database_query_duration_seconds{operation="select", table="users"}
tux_memory_usage_percent
tux_active_guilds_total

# Bad metric names
tux_cmd_count  # Unclear abbreviation
tux_db_time    # Missing units
commands       # Missing prefix
```

### Metric Types

#### Counters

Use for values that only increase:

```python
tux_commands_total
tux_database_queries_total
tux_errors_total
```

#### Gauges

Use for values that can go up and down:

```python
tux_active_users_total
tux_memory_usage_percent
tux_database_connections_active
```

#### Histograms

Use for measuring distributions:

```python
tux_command_duration_seconds
tux_database_query_duration_seconds
tux_response_size_bytes
```

### Label Guidelines

#### Required Labels

- `service`: Always "tux-discord-bot"
- `environment`: "development", "staging", "production"

#### Optional Labels

- `guild_id`: For guild-specific metrics
- `command`: For command-specific metrics
- `user_type`: "member", "moderator", "admin"
- `error_type`: For error categorization

#### Label Best Practices

```python
# Good: Bounded cardinality
tux_commands_total{command="ban", status="success", user_type="moderator"}

# Bad: Unbounded cardinality (user IDs change constantly)
tux_commands_total{user_id="123456789", command="ban"}

# Good: Categorical values
tux_database_queries_total{operation="select", table="users", status="success"}

# Bad: High cardinality values
tux_database_queries_total{query="SELECT * FROM users WHERE id = 123"}
```

## Logging Best Practices

### Log Levels

#### TRACE

- **Purpose**: High-frequency events for detailed debugging
- **Examples**: Message events, presence updates, gateway events
- **Usage**: Development and debugging only

#### DEBUG

- **Purpose**: Detailed information for debugging
- **Examples**: Function entry/exit, variable values, detailed flow
- **Usage**: Development and troubleshooting

#### INFO

- **Purpose**: General operational events
- **Examples**: Command execution, user actions, system state changes
- **Usage**: Production monitoring

#### WARNING

- **Purpose**: Potentially harmful situations
- **Examples**: Rate limit warnings, configuration issues, deprecated usage
- **Usage**: Production monitoring and alerting

#### ERROR

- **Purpose**: Error events that don't stop the application
- **Examples**: Command failures, API errors, validation failures
- **Usage**: Production monitoring and alerting

#### CRITICAL

- **Purpose**: Serious errors that may cause application abort
- **Examples**: Database connection failures, critical system errors
- **Usage**: Production monitoring and immediate alerting

### Structured Logging Format

#### Required Fields

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "message": "Command executed successfully",
  "correlation_id": "req-123e4567-e89b-12d3-a456-426614174000",
  "service": "tux-discord-bot",
  "environment": "production"
}
```

#### Optional Context Fields

```json
{
  "user_context": {
    "user_id": "123456789",
    "username": "user123",
    "guild_id": "987654321"
  },
  "guild_context": {
    "guild_id": "987654321",
    "guild_name": "Example Guild",
    "member_count": 1500
  },
  "command_context": {
    "command": "ban",
    "duration_ms": 250,
    "success": true
  }
}
```

### Correlation IDs

#### Purpose

- Track related log entries across different components
- Enable distributed tracing
- Simplify debugging and troubleshooting

#### Implementation

```python
import uuid
from contextvars import ContextVar

correlation_id: ContextVar[str] = ContextVar('correlation_id')

def set_correlation_id():
    corr_id = str(uuid.uuid4())
    correlation_id.set(corr_id)
    return corr_id

def log_with_correlation(message, **kwargs):
    logger.info(message, extra={
        'correlation_id': correlation_id.get(),
        **kwargs
    })
```

### Log Message Guidelines

#### Good Log Messages

```python
# Clear, actionable messages
logger.info("Command executed successfully", extra={
    'command': 'ban',
    'user_id': '123456789',
    'target_user_id': '987654321',
    'duration_ms': 250
})

logger.error("Database query failed", extra={
    'operation': 'select',
    'table': 'users',
    'error': 'connection timeout',
    'duration_ms': 5000
})
```

#### Bad Log Messages

```python
# Vague, unhelpful messages
logger.info("Success")
logger.error("Error occurred")
logger.debug("Processing...")
```

## Health Monitoring

### Health Check Endpoints

#### Liveness Probe (`/health/live`)

- **Purpose**: Indicates if the application is running
- **Response**: Always returns 200 if the process is alive
- **Use Case**: Kubernetes liveness probe

#### Readiness Probe (`/health/ready`)

- **Purpose**: Indicates if the application is ready to serve traffic
- **Checks**: Database connectivity, external service availability
- **Response**: 200 if ready, 503 if not ready
- **Use Case**: Kubernetes readiness probe, load balancer health checks

#### Status Endpoint (`/health/status`)

- **Purpose**: Detailed health information for monitoring
- **Response**: Comprehensive status of all components
- **Use Case**: Monitoring dashboards, detailed health checks

### Health Check Implementation

```python
@app.get("/health/live")
async def liveness_check():
    return {
        'status': 'alive',
        'timestamp': datetime.now(UTC).isoformat(),
        'uptime_seconds': time.time() - start_time
    }

@app.get("/health/ready")
async def readiness_check():
    checks = {
        'database': await check_database_health(),
        'discord_api': await check_discord_api_health(),
        'system_resources': check_system_resources()
    }
    
    all_healthy = all(
        check['status'] in ['healthy', 'warning'] 
        for check in checks.values()
    )
    
    return {
        'status': 'ready' if all_healthy else 'not_ready',
        'checks': checks,
        'timestamp': datetime.now(UTC).isoformat()
    }, 200 if all_healthy else 503
```

## Alerting Best Practices

### Alert Severity Levels

#### CRITICAL

- **Description**: Service is down or severely degraded
- **Response Time**: < 5 minutes
- **Channels**: Discord, Email, SMS
- **Examples**: Service unavailable, database connection failed

#### WARNING

- **Description**: Service is degraded but functional
- **Response Time**: < 30 minutes
- **Channels**: Discord, Email
- **Examples**: High error rate, slow response times

#### INFO

- **Description**: Informational alerts
- **Response Time**: < 4 hours
- **Channels**: Discord
- **Examples**: Deployment notifications, capacity warnings

### Alert Rule Guidelines

#### Good Alert Rules

```python
# Specific, actionable alerts
AlertRule(
    name="high_command_error_rate",
    description="Command error rate exceeds 5% over 5 minutes",
    condition=lambda: get_error_rate_5min() > 0.05,
    severity=AlertSeverity.CRITICAL,
    cooldown_minutes=10
)

AlertRule(
    name="database_slow_queries",
    description="Database queries taking longer than 2 seconds",
    condition=lambda: get_slow_query_count() > 10,
    severity=AlertSeverity.WARNING,
    cooldown_minutes=30
)
```

#### Bad Alert Rules

```python
# Vague, non-actionable alerts
AlertRule(
    name="something_wrong",
    description="System is not working properly",
    condition=lambda: check_system(),
    severity=AlertSeverity.CRITICAL
)
```

### Alert Fatigue Prevention

#### Cooldown Periods

- Use appropriate cooldown periods to prevent spam
- Critical alerts: 5-10 minutes
- Warning alerts: 15-30 minutes
- Info alerts: 1-4 hours

#### Alert Grouping

- Group related alerts together
- Use alert dependencies to prevent cascading alerts
- Implement alert escalation for unacknowledged critical alerts

#### Regular Review

- Review alert rules monthly
- Remove or adjust noisy alerts
- Ensure alerts are still relevant and actionable

## Dashboard Design

### Operational Dashboard

#### Key Metrics to Display

1. **Service Health**: Uptime, health check status
2. **Performance**: Response times, throughput
3. **Errors**: Error rates, error types
4. **Resources**: CPU, memory, disk usage

#### Layout Principles

- Most important metrics at the top
- Use consistent color schemes
- Include time range selectors
- Provide drill-down capabilities

### Business Intelligence Dashboard

#### Key Metrics to Display

1. **User Engagement**: Active users, command usage
2. **Guild Activity**: Active guilds, member growth
3. **Feature Adoption**: Feature usage rates
4. **Moderation**: Action counts, case resolution times

## Performance Monitoring

### Service Level Indicators (SLIs)

#### Availability

- **Definition**: Percentage of successful health checks
- **Target**: 99.9% uptime
- **Measurement**: `health_check_success_rate`

#### Latency

- **Definition**: 95th percentile command response time
- **Target**: < 1 second
- **Measurement**: `command_duration_p95`

#### Error Rate

- **Definition**: Percentage of failed commands
- **Target**: < 1% error rate
- **Measurement**: `command_error_rate`

#### Throughput

- **Definition**: Commands processed per second
- **Target**: > 100 commands/second capacity
- **Measurement**: `command_throughput`

### Performance Thresholds

#### Command Execution

- **Target**: < 500ms
- **Warning**: > 1s
- **Critical**: > 5s

#### Database Queries

- **Target**: < 100ms
- **Warning**: > 500ms
- **Critical**: > 2s

#### System Resources

- **Memory Target**: < 70%
- **Memory Warning**: > 80%
- **Memory Critical**: > 90%
- **CPU Target**: < 60%
- **CPU Warning**: > 80%
- **CPU Critical**: > 95%

## Implementation Checklist

### Metrics Collection

- [ ] Implement Prometheus metrics collection
- [ ] Add command execution metrics
- [ ] Add database performance metrics
- [ ] Add Discord API metrics
- [ ] Add business intelligence metrics
- [ ] Add system resource metrics
- [ ] Configure metrics retention and storage

### Logging Enhancement

- [ ] Implement structured logging with JSON format
- [ ] Add correlation IDs for request tracing
- [ ] Standardize log levels across all modules
- [ ] Configure log rotation and retention
- [ ] Set up log aggregation (ELK stack)
- [ ] Create log analysis queries and dashboards

### Health Monitoring

- [ ] Implement health check endpoints
- [ ] Add database connectivity checks
- [ ] Add Discord API connectivity checks
- [ ] Add system resource health checks
- [ ] Configure health check monitoring

### Alerting Setup

- [ ] Define alert rules and thresholds
- [ ] Configure alert channels
- [ ] Set up alert cooldown periods
- [ ] Test alert delivery mechanisms
- [ ] Create incident response procedures

### Dashboard Creation

- [ ] Create operational dashboard
- [ ] Create business intelligence dashboard
- [ ] Create performance monitoring dashboard
- [ ] Create error tracking dashboard
- [ ] Set up dashboard access controls

## Troubleshooting Guide

### Common Issues

#### High Cardinality Metrics

- **Problem**: Too many unique label combinations
- **Solution**: Reduce label cardinality, use sampling
- **Prevention**: Review label design before implementation

#### Log Volume Issues

- **Problem**: Too many logs causing performance issues
- **Solution**: Implement log sampling, adjust log levels
- **Prevention**: Use appropriate log levels, implement sampling

#### Alert Fatigue

- **Problem**: Too many false positive alerts
- **Solution**: Adjust thresholds, implement cooldowns
- **Prevention**: Test alerts thoroughly, regular review

#### Dashboard Performance

- **Problem**: Slow loading dashboards
- **Solution**: Optimize queries, reduce time ranges
- **Prevention**: Design efficient queries, use appropriate aggregations

## Conclusion

Following these best practices will ensure that the Tux Discord bot has comprehensive, maintainable, and effective observability. Regular review and updates of these practices are essential as the system evolves and grows.

Remember that observability is not just about collecting data—it's about making that data actionable and useful for maintaining and improving the system.
