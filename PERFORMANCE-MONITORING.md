# Docker Performance Monitoring System

## 🚀 Quick Start

```bash
# Run comprehensive performance test
./scripts/test-docker.sh

# Monitor live container performance  
./scripts/monitor-resources.sh tux-dev 60 5

# Analyze performance trends
./scripts/compare-performance.sh
```

## 📊 Features Added

### 1. **Enhanced Test Script** (`scripts/test-docker.sh`)

- **Comprehensive timing**: All operations timed with millisecond precision
- **Image size tracking**: Development and production image sizes
- **Memory usage monitoring**: Container memory consumption
- **Layer analysis**: Count and optimize Docker layers
- **Security scan timing**: Track vulnerability scan performance
- **JSON metrics export**: Structured data for analysis
- **Performance baselines**: Automated pass/fail thresholds

### 2. **Resource Monitoring** (`scripts/monitor-resources.sh`)

- **Real-time monitoring**: Live CPU, memory, network, and I/O stats
- **Configurable duration**: Monitor for custom time periods
- **CSV data export**: Time-series data for analysis
- **Performance reports**: Automated analysis and recommendations
- **Threshold alerts**: Warnings when limits exceeded
- **Chart generation**: Visual performance graphs (with gnuplot)

### 3. **Performance Analysis** (`scripts/compare-performance.sh`)

- **Trend analysis**: Track performance over time
- **Historical comparison**: Compare current vs. average performance
- **Regression detection**: Identify performance degradation
- **Recommendations**: Actionable optimization suggestions
- **Multiple export formats**: Markdown reports, CSV data, PNG charts

### 4. **CI/CD Integration** (`.github/workflows/docker-test.yml`)

- **Automated performance testing**: Run on every push/PR
- **Performance thresholds**: Fail builds if performance regresses
- **Artifact collection**: Store performance data and reports
- **PR comments**: Automatic performance feedback on pull requests
- **Nightly monitoring**: Track long-term performance trends
- **Security scan integration**: Vulnerability detection with timing

## 📈 Performance Metrics Tracked

| Metric | Description | Target | Critical |
|--------|-------------|--------|----------|
| **Development Build** | Time to build dev image | < 120s | > 300s |
| **Production Build** | Time to build prod image | < 180s | > 300s |
| **Container Startup** | Time to container ready | < 5s | > 10s |
| **Image Size (Dev)** | Development image size | < 2GB | > 4GB |
| **Image Size (Prod)** | Production image size | < 1GB | > 2GB |
| **Memory Usage** | Runtime memory consumption | < 512MB | > 1GB |
| **Prisma Generation** | Client generation time | < 30s | > 60s |
| **Security Scan** | Vulnerability scan time | < 60s | > 120s |
| **Temp File Ops** | File I/O performance | < 2s | > 5s |
| **Layer Count** | Docker layers optimization | < 25 | > 40 |

## 🗂️ File Structure

```
logs/                           # Performance data
├── docker-test-YYYYMMDD-HHMMSS.log       # Detailed test logs
├── docker-metrics-YYYYMMDD-HHMMSS.json   # JSON performance data
├── resource-monitor-YYYYMMDD-HHMMSS.csv  # Resource monitoring CSV
└── resource-report-YYYYMMDD-HHMMSS.txt   # Resource analysis report

performance-history/            # Historical performance data
└── docker-metrics-*.json      # Archived metrics for trend analysis

performance-reports/            # Generated reports
├── performance-trends-YYYYMMDD-HHMMSS.md # Trend analysis report
├── performance-data-YYYYMMDD-HHMMSS.csv  # Aggregated CSV data
└── build-performance-YYYYMMDD-HHMMSS.png # Performance charts

scripts/                        # Performance tools
├── test-docker.sh             # Main performance test script
├── compare-performance.sh     # Trend analysis script
└── monitor-resources.sh       # Real-time monitoring script
```

## 📊 JSON Metrics Format

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "performance": {
    "development_build": {"value": 95420, "unit": "ms"},
    "production_build": {"value": 142350, "unit": "ms"},
    "container_startup": {"value": 2150, "unit": "ms"},
    "prisma_generation": {"value": 18600, "unit": "ms"},
    "dev_image_size_mb": {"value": 1850.5, "unit": "MB"},
    "prod_image_size_mb": {"value": 920.3, "unit": "MB"},
    "memory_usage_mb": {"value": 285.7, "unit": "MB"},
    "temp_file_ops": {"value": 1250, "unit": "ms"},
    "security_scan": {"value": 45200, "unit": "ms"},
    "dev_layers": {"value": 24, "unit": "count"},
    "prod_layers": {"value": 18, "unit": "count"}
  },
  "summary": {
    "total_tests": 12,
    "timestamp": "2024-01-15T10:35:00Z",
    "log_file": "logs/docker-test-20240115-103000.log"
  }
}
```

## 🔧 Usage Examples

### Basic Performance Test

```bash
# Quick validation (all tests with timing)
./scripts/test-docker.sh

# View latest results
cat logs/docker-test-*.log | tail -20
```

### Resource Monitoring

```bash
# Monitor development container for 2 minutes
./scripts/monitor-resources.sh tux-dev 120 5

# Monitor production container for 5 minutes
./scripts/monitor-resources.sh tux 300 10

# Quick 30-second check
./scripts/monitor-resources.sh tux-dev 30
```

### Performance Analysis

```bash
# Analyze trends (requires previous test data)
./scripts/compare-performance.sh

# View specific metrics
jq '.performance.production_build' logs/docker-metrics-*.json

# Export to CSV for Excel analysis
jq -r '[.timestamp, .performance.production_build.value, .performance.prod_image_size_mb.value] | @csv' logs/docker-metrics-*.json > my-performance.csv
```

### CI/CD Integration

```bash
# Local CI simulation
.github/workflows/docker-test.yml # Runs automatically on push

# Manual trigger
gh workflow run "Docker Performance Testing"
```

## 🎯 Performance Optimization Workflow

1. **Baseline Measurement**

   ```bash
   ./scripts/test-docker.sh  # Establish baseline
   ```

2. **Make Changes**
   - Modify Dockerfile, dependencies, or configuration
   - Test changes in development environment

3. **Performance Validation**

   ```bash
   ./scripts/test-docker.sh  # Measure impact
   ./scripts/compare-performance.sh  # Compare vs baseline
   ```

4. **Continuous Monitoring**

   ```bash
   # During development
   ./scripts/monitor-resources.sh tux-dev 300
   
   # In production (ongoing)
   watch -n 60 'docker stats tux --no-stream'
   ```

5. **Trend Analysis**

   ```bash
   # Weekly performance review
   ./scripts/compare-performance.sh
   cat performance-reports/performance-trends-*.md
   ```

## 🚨 Alert Thresholds

### Warning Levels

- **Build Time > 2 minutes**: Consider optimization
- **Image Size > 800MB**: Review dependencies  
- **Memory Usage > 256MB**: Monitor for leaks
- **Startup Time > 3 seconds**: Check initialization

### Critical Levels

- **Build Time > 5 minutes**: Immediate optimization required
- **Image Size > 2GB**: Major cleanup needed
- **Memory Usage > 1GB**: Memory leak investigation
- **Startup Time > 10 seconds**: Architecture review

## 📊 Dashboard Commands

```bash
# Real-time performance dashboard
watch -n 5 './scripts/test-docker.sh && ./scripts/compare-performance.sh'

# Quick metrics view
jq '.performance | to_entries[] | "\(.key): \(.value.value) \(.value.unit)"' logs/docker-metrics-*.json | tail -10

# Performance score calculation
jq '.performance.production_build.value + (.performance.prod_image_size_mb.value * 1000) + .performance.container_startup.value' logs/docker-metrics-*.json
```

## 🔮 Future Enhancements

- **Grafana Integration**: Real-time dashboards
- **Prometheus Metrics**: Time-series monitoring
- **Slack/Discord Alerts**: Performance regression notifications
- **A/B Testing**: Compare Docker configurations
- **Automated Optimization**: Performance tuning suggestions
- **Cost Analysis**: Resource usage cost calculations

---

**Next Steps**: Run `./scripts/test-docker.sh` to establish your performance baseline! 🚀
