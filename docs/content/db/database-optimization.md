# Database Optimization Guide

This guide provides comprehensive database optimization recommendations for Tux self-hosters, covering PostgreSQL configuration, maintenance schedules, and performance tuning.

## 🎯 **Quick Start: Database Health Check**

Run this command to get a complete analysis of your database:

```bash
make db-optimize
```

This will show you:
- Current PostgreSQL settings
- Table maintenance status
- Index usage analysis
- Specific optimization recommendations

## 📊 **Current Database Analysis Results**

Based on the analysis, here are the key findings and recommendations:

### **🔧 Immediate Actions Required:**

1. **Run ANALYZE on all tables:**
   ```bash
   make db-analyze
   ```
   - All tables show "Last analyze: Never"
   - This affects query planner performance

2. **Check for tables needing VACUUM:**
   ```bash
   make db-vacuum
   ```
   - `alembic_version` table has 1 dead row
   - Consider running VACUUM for cleanup

3. **Monitor index usage:**
   ```bash
   make db-queries
   ```
   - Check for long-running queries
   - Monitor performance patterns

### **⚙️ Configuration Optimizations:**

#### **Memory Settings (Critical for Performance):**

```ini
# postgresql.conf - Memory Configuration
# Set these based on your server's available RAM

# Shared buffers: 25% of RAM for dedicated database server
shared_buffers = 256MB                    # Current: 128MB (too low)

# Effective cache size: 75% of RAM
effective_cache_size = 768MB              # Current: 4GB (good)

# Work memory: Increase for complex queries
work_mem = 16MB                           # Current: 4MB (too low)

# Maintenance work memory: For faster VACUUM/ANALYZE
maintenance_work_mem = 128MB              # Current: 64MB (could be higher)
```

#### **Autovacuum Settings (Automatic Maintenance):**

```ini
# Autovacuum Configuration
autovacuum = on                           # Current: on (good)
autovacuum_vacuum_scale_factor = 0.2      # Current: 0.2 (good)
autovacuum_analyze_scale_factor = 0.1     # Current: 0.1 (good)

# More aggressive autovacuum for active databases
autovacuum_vacuum_threshold = 50          # Default: 50
autovacuum_analyze_threshold = 50         # Default: 50
```

#### **Checkpoint and WAL Settings:**

```ini
# Write-Ahead Log Configuration
checkpoint_completion_target = 0.9        # Current: 0.9 (good)
wal_buffers = 16MB                        # Current: 4MB (could be higher)
fsync = on                                # Current: on (good for data safety)
synchronous_commit = on                   # Current: on (good for data safety)
```

#### **Query Planning and Statistics:**

```ini
# Query Planning
default_statistics_target = 100           # Current: 100 (good)
random_page_cost = 1.1                    # Current: 4.0 (adjust for SSD)
effective_io_concurrency = 200            # Current: 1 (increase for SSD)
```

## 🚀 **Performance Tuning by Server Type**

### **🖥️ Small VPS (1-2GB RAM):**

```ini
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 8MB
maintenance_work_mem = 64MB
max_connections = 50
```

### **💻 Medium Server (4-8GB RAM):**

```ini
shared_buffers = 1GB
effective_cache_size = 6GB
work_mem = 16MB
maintenance_work_mem = 256MB
max_connections = 100
```

### **🖥️ Large Server (16GB+ RAM):**

```ini
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 32MB
maintenance_work_mem = 512MB
max_connections = 200
```

### **☁️ Cloud Database (Managed):**

For managed PostgreSQL services (AWS RDS, Google Cloud SQL, etc.):
- Most settings are managed automatically
- Focus on connection pooling and query optimization
- Use `make db-optimize` to identify bottlenecks

## 🔄 **Maintenance Schedule**

### **📅 Daily Tasks:**
```bash
# Check for long-running queries
make db-queries

# Monitor database health
make db-health
```

### **📅 Weekly Tasks:**
```bash
# Analyze table statistics for query planning
make db-analyze

# Check table maintenance status
make db-vacuum
```

### **📅 Monthly Tasks:**
```bash
# Full optimization analysis
make db-optimize

# Check index usage and remove unused indexes
# (Currently all indexes show 0 scans - this is normal for new databases)
```

### **📅 As Needed:**
```bash
# When tables have many dead rows
make db-vacuum

# After major data changes
make db-analyze

# For performance issues
make db-optimize
```

## 🛠️ **Database Maintenance Commands**

### **📊 Health Monitoring:**
```bash
# Comprehensive health check
make db-health

# Performance metrics
make db-performance

# Table statistics
make db-stats
```

### **🔧 Maintenance Operations:**
```bash
# Analyze table statistics
make db-analyze

# Reindex tables for performance
make db-reindex

# Show maintenance information
make db-vacuum
```

### **📋 Information and Analysis:**
```bash
# List all tables with row counts
make db-tables

# Check for long-running queries
make db-queries

# Full optimization analysis
make db-optimize
```

## 📈 **Performance Monitoring**

### **Key Metrics to Watch:**

1. **Query Performance:**
   - Long-running queries (>1 second)
   - Sequential scans vs index scans
   - Cache hit ratios

2. **Table Health:**
   - Dead row counts
   - Last VACUUM/ANALYZE times
   - Table and index sizes

3. **Resource Usage:**
   - Memory utilization
   - Connection counts
   - Disk I/O patterns

### **Performance Thresholds:**

- **Response Time:** Queries should complete in <100ms for simple operations
- **Cache Hit Ratio:** Should be >95% for read-heavy workloads
- **Dead Rows:** Should be <10% of live rows
- **Index Usage:** Unused indexes should be reviewed monthly

## 🚨 **Troubleshooting Common Issues**

### **Problem: Slow Queries**
```bash
# Check for long-running queries
make db-queries

# Analyze table statistics
make db-analyze

# Check index usage
make db-optimize
```

### **Problem: High Memory Usage**
```bash
# Check current settings
make db-optimize

# Look for memory-related settings in output
# Adjust shared_buffers and work_mem if needed
```

### **Problem: Tables Not Being Maintained**
```bash
# Check autovacuum status
make db-vacuum

# Run manual maintenance
make db-analyze
```

### **Problem: Indexes Not Being Used**
```bash
# Check index usage
make db-optimize

# Look for "Index never used" warnings
# Consider removing unused indexes
```

## 🔧 **Advanced Optimizations**

### **Connection Pooling:**
For high-traffic applications, consider using PgBouncer:
```ini
# pgbouncer.ini
[databases]
tuxdb = host=localhost port=5432 dbname=tuxdb

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```

### **Partitioning:**
For very large tables (millions of rows), consider table partitioning:
```sql
-- Example: Partition cases table by date
CREATE TABLE cases_partitioned (
    LIKE cases INCLUDING ALL
) PARTITION BY RANGE (case_created_at);

-- Create monthly partitions
CREATE TABLE cases_2024_01 PARTITION OF cases_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### **Parallel Query Processing:**
Enable for complex queries on multi-core systems:
```ini
# postgresql.conf
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
parallel_tuple_cost = 0.1
parallel_setup_cost = 1000
```

## 📚 **Resources and Further Reading**

### **PostgreSQL Documentation:**
- [Performance Tuning](https://www.postgresql.org/docs/current/runtime-config-query.html)
- [Autovacuum Tuning](https://www.postgresql.org/docs/current/runtime-config-autovacuum.html)
- [Monitoring](https://www.postgresql.org/docs/current/monitoring.html)

### **Tux-Specific Commands:**
- `make help-db` - List all database commands
- `make db-optimize` - Full optimization analysis
- `make db-health` - Quick health check

### **External Tools:**
- **pgAdmin** - GUI database administration
- **pg_stat_statements** - Query performance analysis
- **pgBadger** - Log analysis and reporting

## ✅ **Quick Optimization Checklist**

Before making changes, run this checklist:

- [ ] **Baseline Performance:** Run `make db-optimize` to establish baseline
- [ ] **Backup Database:** Always backup before configuration changes
- [ ] **Test Changes:** Test configuration changes in development first
- [ ] **Monitor Results:** Use `make db-health` to verify improvements
- [ ] **Document Changes:** Keep track of what you changed and why

## 🎯 **Expected Results After Optimization**

With proper optimization, you should see:

- **Query Response Time:** 50-80% improvement for complex queries
- **Memory Usage:** More efficient memory utilization
- **Maintenance:** Faster VACUUM and ANALYZE operations
- **Scalability:** Better performance under load
- **Reliability:** Fewer timeouts and connection issues

---

**Last Updated**: 2025-08-28
**Version**: v0.1.0
**Related Docs**: [Database Lifecycle Guide](database-lifecycle.md), [SETUP.md](../SETUP.md)

*Remember: Database optimization is an iterative process. Start with the immediate actions, monitor results, and gradually implement more advanced optimizations based on your specific usage patterns.*
