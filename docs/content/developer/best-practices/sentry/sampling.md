---
title: Sampling
description: How Sentry sampling works in Tux and how to configure it
tags:
  - developer-guide
  - best-practices
  - sentry
---

# Sampling

Tux uses Sentry's sampling system to control the volume of events sent to Sentry while maintaining data quality. This guide explains how sampling works and how it's configured.

## Overview

Sampling helps balance:

- **Data quality** - Enough data to draw meaningful conclusions
- **Performance** - Minimal overhead from tracing
- **Volume** - Manageable number of events sent to Sentry

Tux uses different sampling strategies for errors and transactions.

## Error Sampling

**By default, all errors are sent to Sentry** (100% sample rate). This ensures you don't miss critical issues.

### Current Configuration

Tux doesn't configure `sample_rate` or `error_sampler`, which means:

- All errors are captured and sent to Sentry
- No error sampling is applied

### When to Use Error Sampling

Error sampling is useful when:

- You have very high error volume
- You want to reduce Sentry quota usage
- You can tolerate missing some errors

**Note:** Sentry recommends using [rate limiting](https://docs.sentry.io/pricing/quotas/manage-event-stream-guide.md#rate-limiting) instead of error sampling, as rate limiting only drops events when volume is high, preserving important errors.

### Configuring Error Sampling

If you need to sample errors, you can add configuration to `src/tux/services/sentry/config.py`:

```python
# Static sample rate (25% of errors)
sentry_sdk.init(
    # ...
    sample_rate=0.25,
)

# Or dynamic sampling based on error type
def error_sampler(event: Event, hint: Hint) -> float:
    error_class = hint["exc_info"][0]
    
    # Sample critical errors at 100%
    if error_class in [TuxDatabaseConnectionError, TuxCogLoadError]:
        return 1.0
    
    # Sample other errors at 50%
    return 0.5

sentry_sdk.init(
    # ...
    error_sampler=error_sampler,
)
```

## Transaction Sampling

Tux uses a **dynamic sampling function** (`traces_sampler`) that samples different operation types at different rates.

### Current Sampling Rates

Tux samples transactions based on operation type:

| Operation Type | Sample Rate | Rationale |
|---------------|-------------|-----------|
| Commands & Interactions | 10% | High value, moderate volume |
| Database Queries | 5% | Frequent operations, lower value per transaction |
| HTTP Requests | 5% | Frequent operations, lower value per transaction |
| Background Tasks | 2% | Periodic operations, lower priority |
| Other Operations | 1% | Catch-all for low-volume operations |

### Parent Sampling Inheritance

Tux's `traces_sampler` **always respects parent sampling decisions** to maintain distributed trace integrity:

```python
def traces_sampler(sampling_context: dict[str, Any]) -> float:
    # Always inherit parent sampling decision
    parent_sampled = sampling_context.get("parent_sampled")
    if parent_sampled is not None:
        return float(parent_sampled)
    
    # ... rest of sampling logic
```

This ensures that if a transaction has a parent (from distributed tracing), it inherits the parent's sampling decision, preventing broken traces.

### Sampling Context

The sampling function receives context about the transaction:

```python
{
    "transaction_context": {
        "name": "command.ping",  # Transaction name
        "op": "discord.command"  # Operation type
    },
    "parent_sampled": True,  # Parent's sampling decision (if exists)
    # ... other attributes
}
```

### Custom Sampling Context

When creating custom transactions, you can pass additional context for sampling:

```python
from tux.services.sentry import start_transaction

with start_transaction(
    op="task",
    name="process_report",
    custom_sampling_context={
        "priority": "high",
        "user_tier": "premium",
    }
) as txn:
    # Sampling function can access custom_sampling_context
    await process_report()
```

## Adjusting Sampling Rates

To adjust sampling rates, modify `src/tux/services/sentry/handlers.py`:

```python
def traces_sampler(sampling_context: dict[str, Any]) -> float:
    # Always inherit parent sampling decision
    parent_sampled = sampling_context.get("parent_sampled")
    if parent_sampled is not None:
        return float(parent_sampled)

    transaction_context = sampling_context.get("transaction_context", {})
    op = transaction_context.get("op", "")

    # Adjust rates based on your needs
    if op in ["discord.command", "discord.interaction"]:
        return 0.2  # Increased from 0.1 to 20%
    
    if op in ["database.query", "http.request"]:
        return 0.1  # Increased from 0.05 to 10%
    
    if op in ["task.background", "task.scheduled"]:
        return 0.05  # Increased from 0.02 to 5%
    
    return 0.02  # Increased from 0.01 to 2%
```

## Best Practices

### ✅ Do

- **Respect parent sampling decisions** - Always check `parent_sampled` first
- **Sample based on operation value** - Higher value operations get higher rates
- **Start with low rates** - Gradually increase as you learn about traffic patterns
- **Monitor volume** - Adjust rates based on Sentry quota usage

### ❌ Don't

- **Override parent sampling** - This breaks distributed traces
- **Sample too aggressively** - You need enough data for meaningful insights
- **Sample errors** - Use rate limiting instead (unless volume is extremely high)
- **Forget to test** - Verify sampling works as expected in production

## Sampling Precedence

When multiple sampling mechanisms could apply, Sentry uses this precedence:

1. **Explicit decision** - If `sampled=True/False` is passed to `start_transaction()`, that decision is used
2. **Sampling function** - If `traces_sampler` is defined, its decision is used (can inherit parent)
3. **Parent inheritance** - If no sampler but parent exists, inherit parent's decision
4. **Static rate** - If `traces_sample_rate` is set, use that rate

Tux uses option 2 (sampling function) which respects parent decisions.

## Monitoring Sampling

To monitor sampling effectiveness:

1. **Check Sentry Insights** - View transaction volume and distribution
2. **Review sampling rates** - Ensure rates match your expectations
3. **Monitor quota usage** - Adjust rates if approaching limits
4. **Verify trace completeness** - Ensure distributed traces aren't broken

## Related Documentation

- [Choosing Instrumentation](./choosing-instrumentation.md) - When to use transactions/spans vs metrics
- [Transactions and Spans](./transactions-spans.md) - How to use transactions and spans
- [Sentry Integration](./index.md) - General Sentry setup
