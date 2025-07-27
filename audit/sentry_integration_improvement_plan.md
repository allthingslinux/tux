# Sentry Integration Improvement Plan

## Current State Assessment

### Existing Sentry Integration Strengths

- **Transaction Tracking**: Good coverage for command execution tracking
- **Error Reporting**: Basic error capture and reporting
- **Context Tags**: Command name, guild ID, user ID, and interaction type tracking
- **Performance Monitoring**: Transaction timing for commands

### Identified Gaps

- **Incomplete Error Context**: Missing detailed error context for debugging
- **Limited Error Correlation**: Difficult to correlate related errors
- **Missing Custom Metrics**: No custom business metrics tracking
- **Inconsistent Integration**: Not all error paths properly integrated
- **Limited Performance Insights**: Missing detailed performance breakdowns

## Improvement Strategy

### 1. Enhanced Error Context Collection

#### Current Context

```python
# Current basic context in error handler
log_context = {
    "command_name": command_name,
    "guild_id": guild_id,
    "user_id": user_id,
    "error_type": error_type.__name__
}
```

#### Enhanced Context Implementation

```python
class SentryContextCollector:
    """Collects comprehensive context for Sentry error reports."""
    
    def collect_error_context(
        self,
        error: Exception,
        source: ContextOrInteraction,
        additional_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Collect comprehensive error context."""
        
        context = {
            # Error Information
            'error': {
                'type': type(error).__name__,
                'message': str(error),
                'module': error.__class__.__module__,
                'traceback_hash': self._generate_traceback_hash(error),
                'custom_context': getattr(error, 'context', {})
            },
            
            # Command Context
            'command': {
                'name': self._extract_command_name(source),
                'type': 'slash' if isinstance(source, discord.Interaction) else 'prefix',
                'qualified_name': self._get_qualified_command_name(source),
                'cog_name': self._get_cog_name(source),
                'parameters': self._extract_command_parameters(source)
            },
            
            # User Context
            'user': {
                'id': self._get_user_id(source),
                'username': self._get_username(source),
                'discriminator': self._get_discriminator(source),
                'bot': self._is_bot_user(source),
                'permissions': self._get_user_permissions(source)
            },
            
            # Guild Context
            'guild': {
                'id': self._get_guild_id(source),
                'name': self._get_guild_name(source),
                'member_count': self._get_member_count(source),
                'features': self._get_guild_features(source),
                'premium_tier': self._get_premium_tier(source)
            },
            
            # Channel Context
            'channel': {
                'id': self._get_channel_id(source),
                'name': self._get_channel_name(source),
                'type': self._get_channel_type(source),
                'nsfw': self._is_nsfw_channel(source)
            },
            
            # System Context
            'system': {
                'bot_version': self._get_bot_version(),
                'discord_py_version': discord.__version__,
                'python_version': sys.version_info[:3],
                'platform': platform.platform(),
                'memory_usage': self._get_memory_usage(),
                'uptime': self._get_bot_uptime()
            },
            
            # Performance Context
            'performance': {
                'response_time': self._get_response_time(source),
                'database_query_count': self._get_db_query_count(),
                'cache_hit_rate': self._get_cache_hit_rate(),
                'active_transactions': len(self.bot.active_sentry_transactions)
            },
            
            # Additional Context
            **(additional_context or {})
        }
        
        return context
```

### 2. Custom Metrics Implementation

#### Error Metrics

```python
class ErrorMetricsReporter:
    """Reports custom error metrics to Sentry."""
    
    def __init__(self):
        self.metrics_buffer = []
        self.last_flush = time.time()
        self.flush_interval = 60  # seconds
    
    def record_error_metric(self, error: ProcessedError, context: dict[str, Any]):
        """Record error occurrence with detailed metrics."""
        
        # Error count metric
        sentry_sdk.metrics.incr(
            key="tux.errors.total",
            value=1,
            tags={
                "error_type": error.classified_error.__class__.__name__,
                "error_category": error.category,
                "severity": error.severity,
                "command_type": context.get('command', {}).get('type', 'unknown'),
                "cog_name": context.get('command', {}).get('cog_name', 'unknown')
            }
        )
        
        # Error rate metric (errors per minute)
        sentry_sdk.metrics.gauge(
            key="tux.errors.rate",
            value=self._calculate_error_rate(),
            tags={
                "time_window": "1m"
            }
        )
        
        # Response time for error handling
        if response_time := context.get('performance', {}).get('response_time'):
            sentry_sdk.metrics.timing(
                key="tux.error_handling.duration",
                value=response_time,
                tags={
                    "error_type": error.classified_error.__class__.__name__,
                    "severity": error.severity
                }
            )
    
    def record_command_metrics(self, command_context: dict[str, Any]):
        """Record command execution metrics."""
        
        # Command execution count
        sentry_sdk.metrics.incr(
            key="tux.commands.executed",
            value=1,
            tags={
                "command_name": command_context.get('name', 'unknown'),
                "command_type": command_context.get('type', 'unknown'),
                "cog_name": command_context.get('cog_name', 'unknown')
            }
        )
        
        # Command response time
        if response_time := command_context.get('response_time'):
            sentry_sdk.metrics.timing(
                key="tux.commands.duration",
                value=response_time,
                tags={
                    "command_name": command_context.get('name', 'unknown'),
                    "command_type": command_context.get('type', 'unknown')
                }
            )
```

#### Business Metrics

```python
class BusinessMetricsReporter:
    """Reports business-specific metrics to Sentry."""
    
    def record_user_activity(self, activity_type: str, user_id: int, guild_id: int | None = None):
        """Record user activity metrics."""
        
        sentry_sdk.metrics.incr(
            key="tux.user_activity",
            value=1,
            tags={
                "activity_type": activity_type,
                "guild_id": str(guild_id) if guild_id else "dm"
            }
        )
    
    def record_database_operation(self, operation: str, table: str, duration: float):
        """Record database operation metrics."""
        
        sentry_sdk.metrics.incr(
            key="tux.database.operations",
            value=1,
            tags={
                "operation": operation,
                "table": table
            }
        )
        
        sentry_sdk.metrics.timing(
            key="tux.database.duration",
            value=duration,
            tags={
                "operation": operation,
                "table": table
            }
        )
    
    def record_external_api_call(self, service: str, endpoint: str, status_code: int, duration: float):
        """Record external API call metrics."""
        
        sentry_sdk.metrics.incr(
            key="tux.external_api.calls",
            value=1,
            tags={
                "service": service,
                "endpoint": endpoint,
                "status_code": str(status_code),
                "success": str(200 <= status_code < 300)
            }
        )
        
        sentry_sdk.metrics.timing(
            key="tux.external_api.duration",
            value=duration,
            tags={
                "service": service,
                "endpoint": endpoint
            }
        )
```

### 3. Enhanced Transaction Tracking

#### Hierarchical Transaction Structure

```python
class EnhancedTransactionManager:
    """Manages hierarchical Sentry transactions with better correlation."""
    
    def __init__(self, bot: Tux):
        self.bot = bot
        self.transaction_stack = {}  # Track nested transactions
        self.correlation_ids = {}    # Track related transactions
    
    def start_command_transaction(
        self,
        source: ContextOrInteraction,
        command_name: str
    ) -> sentry_sdk.Transaction | None:
        """Start a command transaction with enhanced tracking."""
        
        if not sentry_sdk.is_initialized():
            return None
        
        # Generate correlation ID for related operations
        correlation_id = str(uuid.uuid4())
        
        transaction = sentry_sdk.start_transaction(
            op="discord.command",
            name=command_name,
            description=self._get_command_description(source)
        )
        
        # Set transaction tags
        transaction.set_tag("command.name", command_name)
        transaction.set_tag("command.type", self._get_command_type(source))
        transaction.set_tag("correlation_id", correlation_id)
        transaction.set_tag("guild.id", str(self._get_guild_id(source)))
        transaction.set_tag("user.id", str(self._get_user_id(source)))
        
        # Store transaction and correlation ID
        source_id = self._get_source_id(source)
        self.bot.active_sentry_transactions[source_id] = transaction
        self.correlation_ids[source_id] = correlation_id
        
        # Add breadcrumb
        sentry_sdk.add_breadcrumb(
            message=f"Started command: {command_name}",
            category="command",
            level="info",
            data={
                "command_name": command_name,
                "correlation_id": correlation_id
            }
        )
        
        return transaction
    
    def start_child_transaction(
        self,
        parent_source_id: int,
        operation: str,
        description: str
    ) -> sentry_sdk.Transaction | None:
        """Start a child transaction for sub-operations."""
        
        parent_transaction = self.bot.active_sentry_transactions.get(parent_source_id)
        if not parent_transaction:
            return None
        
        child_transaction = parent_transaction.start_child(
            op=operation,
            description=description
        )
        
        # Inherit correlation ID from parent
        if correlation_id := self.correlation_ids.get(parent_source_id):
            child_transaction.set_tag("correlation_id", correlation_id)
            child_transaction.set_tag("parent_operation", parent_transaction.op)
        
        return child_transaction
```

#### Database Operation Tracking

```python
class DatabaseTransactionTracker:
    """Tracks database operations within Sentry transactions."""
    
    def track_database_operation(
        self,
        operation: str,
        table: str,
        query: str | None = None
    ):
        """Context manager for tracking database operations."""
        
        return sentry_sdk.start_span(
            op="db.query",
            description=f"{operation} on {table}"
        ) as span:
            span.set_tag("db.operation", operation)
            span.set_tag("db.table", table)
            if query:
                span.set_data("db.query", query[:500])  # Truncate long queries
            
            yield span
```

### 4. Error Correlation and Analysis

#### Error Fingerprinting

```python
class ErrorFingerprintGenerator:
    """Generates consistent fingerprints for error grouping."""
    
    def generate_fingerprint(self, error: Exception, context: dict[str, Any]) -> list[str]:
        """Generate fingerprint for error grouping in Sentry."""
        
        fingerprint_parts = [
            # Error type and message pattern
            type(error).__name__,
            self._normalize_error_message(str(error)),
            
            # Command context
            context.get('command', {}).get('name', 'unknown'),
            context.get('command', {}).get('cog_name', 'unknown'),
            
            # Error location (if available)
            self._extract_error_location(error)
        ]
        
        # Remove None values and create fingerprint
        return [part for part in fingerprint_parts if part]
    
    def _normalize_error_message(self, message: str) -> str:
        """Normalize error message for consistent grouping."""
        # Remove user-specific data (IDs, names, etc.)
        normalized = re.sub(r'\b\d{17,19}\b', '<ID>', message)  # Discord IDs
        normalized = re.sub(r'\b\w+#\d{4}\b', '<USER>', normalized)  # Discord tags
        normalized = re.sub(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', '<EMAIL>', normalized)
        return normalized[:100]  # Limit length
```

#### Related Error Detection

```python
class RelatedErrorDetector:
    """Detects and correlates related errors."""
    
    def __init__(self):
        self.recent_errors = deque(maxlen=100)
        self.error_patterns = {}
    
    def record_error(self, error: ProcessedError, context: dict[str, Any]):
        """Record error for correlation analysis."""
        
        error_record = {
            'timestamp': time.time(),
            'error_type': type(error.classified_error).__name__,
            'fingerprint': self._generate_fingerprint(error, context),
            'correlation_id': context.get('correlation_id'),
            'user_id': context.get('user', {}).get('id'),
            'guild_id': context.get('guild', {}).get('id'),
            'command_name': context.get('command', {}).get('name')
        }
        
        self.recent_errors.append(error_record)
        
        # Check for related errors
        related_errors = self._find_related_errors(error_record)
        if related_errors:
            self._report_error_correlation(error_record, related_errors)
    
    def _find_related_errors(self, current_error: dict[str, Any]) -> list[dict[str, Any]]:
        """Find errors that might be related to the current error."""
        
        related = []
        current_time = current_error['timestamp']
        
        for error_record in self.recent_errors:
            # Skip the current error
            if error_record == current_error:
                continue
            
            # Check time window (last 5 minutes)
            if current_time - error_record['timestamp'] > 300:
                continue
            
            # Check for correlation patterns
            if self._are_errors_related(current_error, error_record):
                related.append(error_record)
        
        return related
```

### 5. Performance Monitoring Enhancements

#### Detailed Performance Tracking

```python
class PerformanceMonitor:
    """Enhanced performance monitoring for Sentry."""
    
    def __init__(self):
        self.performance_data = {}
        self.baseline_metrics = {}
    
    def track_command_performance(self, command_name: str, duration: float, context: dict[str, Any]):
        """Track detailed command performance metrics."""
        
        # Record timing metric
        sentry_sdk.metrics.timing(
            key="tux.command.performance",
            value=duration,
            tags={
                "command_name": command_name,
                "performance_tier": self._classify_performance(duration)
            }
        )
        
        # Check for performance anomalies
        if self._is_performance_anomaly(command_name, duration):
            self._report_performance_anomaly(command_name, duration, context)
    
    def track_resource_usage(self):
        """Track system resource usage."""
        
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        cpu_percent = psutil.Process().cpu_percent()
        
        sentry_sdk.metrics.gauge("tux.system.memory_usage", memory_usage)
        sentry_sdk.metrics.gauge("tux.system.cpu_usage", cpu_percent)
        
        # Alert on high resource usage
        if memory_usage > 500 or cpu_percent > 80:
            sentry_sdk.add_breadcrumb(
                message="High resource usage detected",
                category="performance",
                level="warning",
                data={
                    "memory_mb": memory_usage,
                    "cpu_percent": cpu_percent
                }
            )
```

## Implementation Roadmap

### Phase 1: Enhanced Context Collection (Week 1-2)

- [ ] Implement `SentryContextCollector`
- [ ] Update error handler to use enhanced context
- [ ] Add performance context collection
- [ ] Test context collection accuracy

### Phase 2: Custom Metrics Implementation (Week 3-4)

- [ ] Implement `ErrorMetricsReporter`
- [ ] Implement `BusinessMetricsReporter`
- [ ] Add metrics collection to key operations
- [ ] Set up Sentry dashboards for metrics

### Phase 3: Transaction Enhancements (Week 5-6)

- [ ] Implement `EnhancedTransactionManager`
- [ ] Add hierarchical transaction support
- [ ] Implement database operation tracking
- [ ] Add correlation ID system

### Phase 4: Error Correlation (Week 7-8)

- [ ] Implement error fingerprinting
- [ ] Add related error detection
- [ ] Create error correlation reports
- [ ] Set up alerting for error patterns

### Phase 5: Performance Monitoring (Week 9-10)

- [ ] Implement detailed performance tracking
- [ ] Add resource usage monitoring
- [ ] Create performance anomaly detection
- [ ] Set up performance dashboards

## Success Metrics

### Error Tracking Improvements

- **Context Richness**: 90% of errors include comprehensive context
- **Error Correlation**: Related errors properly grouped and correlated
- **Resolution Time**: 50% reduction in error investigation time

### Performance Monitoring

- **Metric Coverage**: All critical operations tracked with custom metrics
- **Anomaly Detection**: Performance issues detected within 5 minutes
- **Resource Monitoring**: Real-time visibility into system resource usage

### Developer Experience

- **Debugging Efficiency**: Faster error diagnosis with rich context
- **Proactive Monitoring**: Issues detected before user reports
- **Operational Insights**: Clear visibility into system health and performance

This comprehensive Sentry integration improvement plan will significantly enhance the bot's observability, error tracking, and performance monitoring capabilities.
