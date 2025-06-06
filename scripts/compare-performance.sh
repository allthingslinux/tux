#!/bin/bash

# Docker Performance Comparison Script
# Analyzes performance trends and generates reports

set -e

echo "📊 Docker Performance Analysis"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
HISTORY_DIR="performance-history"
LOGS_DIR="logs"
REPORTS_DIR="performance-reports"

# Create directories
mkdir -p "$REPORTS_DIR"

# Get current timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

log() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

metric() {
    echo -e "${BLUE}📊 $1${NC}"
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    error "jq is required for performance analysis"
    echo "Install with: sudo apt-get install jq -y"
    exit 1
fi

# Check for performance data
if [ ! -d "$HISTORY_DIR" ] || [ -z "$(ls -A $HISTORY_DIR 2>/dev/null)" ]; then
    warning "No performance history found in $HISTORY_DIR"
    echo "Run ./scripts/test-docker.sh first to generate performance data"
    
    # Check for recent test data
    if [ -d "$LOGS_DIR" ] && ls $LOGS_DIR/docker-metrics-*.json &> /dev/null; then
        log "Found recent test data in $LOGS_DIR"
        echo "Copying to performance history..."
        cp $LOGS_DIR/docker-metrics-*.json "$HISTORY_DIR/" 2>/dev/null || true
    else
        exit 1
    fi
fi

log "Analyzing performance data..."

# Generate performance trends report
TRENDS_REPORT="$REPORTS_DIR/performance-trends-$TIMESTAMP.md"

cat > "$TRENDS_REPORT" << 'EOF'
# Docker Performance Trends Report

This report analyzes Docker build and runtime performance over time.

## Summary

EOF

# Count data points
DATA_COUNT=$(ls -1 $HISTORY_DIR/docker-metrics-*.json 2>/dev/null | wc -l)
echo "**Data Points:** $DATA_COUNT" >> "$TRENDS_REPORT"
echo "**Generated:** $(date -Iseconds)" >> "$TRENDS_REPORT"
echo "" >> "$TRENDS_REPORT"

if [ "$DATA_COUNT" -eq 0 ]; then
    error "No valid metrics files found"
    exit 1
fi

metric "Found $DATA_COUNT performance data points"

# Build Performance Analysis
echo "## Build Performance Trends" >> "$TRENDS_REPORT"
echo "" >> "$TRENDS_REPORT"
echo "| Date | Dev Build (ms) | Prod Build (ms) | Dev Size (MB) | Prod Size (MB) |" >> "$TRENDS_REPORT"
echo "|------|---------------|----------------|---------------|----------------|" >> "$TRENDS_REPORT"

# Collect all metrics for analysis
temp_file=$(mktemp)

for file in $(ls -t $HISTORY_DIR/docker-metrics-*.json); do
    timestamp=$(jq -r '.timestamp // "N/A"' "$file")
    dev_build=$(jq -r '.performance.development_build.value // "N/A"' "$file")
    prod_build=$(jq -r '.performance.production_build.value // "N/A"' "$file")
    dev_size=$(jq -r '.performance.dev_image_size_mb.value // "N/A"' "$file")
    prod_size=$(jq -r '.performance.prod_image_size_mb.value // "N/A"' "$file")
    
    # Format timestamp for display
    display_date=$(date -d "$timestamp" "+%m/%d %H:%M" 2>/dev/null || echo "$timestamp")
    
    echo "| $display_date | $dev_build | $prod_build | $dev_size | $prod_size |" >> "$TRENDS_REPORT"
    
    # Store data for statistics
    echo "$timestamp,$dev_build,$prod_build,$dev_size,$prod_size" >> "$temp_file"
done

# Calculate statistics
echo "" >> "$TRENDS_REPORT"
echo "## Performance Statistics" >> "$TRENDS_REPORT"
echo "" >> "$TRENDS_REPORT"

log "Calculating performance statistics..."

# Latest metrics
latest_file=$(ls -t $HISTORY_DIR/docker-metrics-*.json | head -1)
latest_prod_build=$(jq -r '.performance.production_build.value // 0' "$latest_file")
latest_prod_size=$(jq -r '.performance.prod_image_size_mb.value // 0' "$latest_file")
latest_startup=$(jq -r '.performance.container_startup.value // 0' "$latest_file")
latest_memory=$(jq -r '.performance.memory_usage_mb.value // 0' "$latest_file")

echo "### Current Performance" >> "$TRENDS_REPORT"
echo "- **Production Build Time:** ${latest_prod_build} ms" >> "$TRENDS_REPORT"
echo "- **Production Image Size:** ${latest_prod_size} MB" >> "$TRENDS_REPORT"
echo "- **Container Startup:** ${latest_startup} ms" >> "$TRENDS_REPORT"
echo "- **Memory Usage:** ${latest_memory} MB" >> "$TRENDS_REPORT"
echo "" >> "$TRENDS_REPORT"

# Calculate averages if we have multiple data points
if [ "$DATA_COUNT" -gt 1 ]; then
    echo "### Historical Averages" >> "$TRENDS_REPORT"
    
    # Calculate averages for production builds
    avg_prod_build=$(awk -F',' 'NR>1 && $3!="N/A" {sum+=$3; count++} END {if(count>0) print int(sum/count); else print "N/A"}' "$temp_file")
    avg_prod_size=$(awk -F',' 'NR>1 && $5!="N/A" {sum+=$5; count++} END {if(count>0) printf "%.1f", sum/count; else print "N/A"}' "$temp_file")
    
    echo "- **Average Production Build:** ${avg_prod_build} ms" >> "$TRENDS_REPORT"
    echo "- **Average Production Size:** ${avg_prod_size} MB" >> "$TRENDS_REPORT"
    
    # Performance comparison
    if [ "$avg_prod_build" != "N/A" ] && [ "$latest_prod_build" -ne 0 ]; then
        if [ "$latest_prod_build" -lt "$avg_prod_build" ]; then
            improvement=$((avg_prod_build - latest_prod_build))
            echo "- **Build Performance:** ✅ ${improvement}ms faster than average" >> "$TRENDS_REPORT"
        else
            regression=$((latest_prod_build - avg_prod_build))
            echo "- **Build Performance:** ⚠️ ${regression}ms slower than average" >> "$TRENDS_REPORT"
        fi
    fi
    
    echo "" >> "$TRENDS_REPORT"
fi

# Performance Recommendations
echo "## Performance Recommendations" >> "$TRENDS_REPORT"
echo "" >> "$TRENDS_REPORT"

# Check against benchmarks
if [ "$latest_prod_build" -gt 180000 ]; then
    echo "- ❌ **Build Time:** Exceeds 3-minute target (${latest_prod_build}ms)" >> "$TRENDS_REPORT"
    echo "  - Consider optimizing Dockerfile layers" >> "$TRENDS_REPORT"
    echo "  - Review build cache efficiency" >> "$TRENDS_REPORT"
elif [ "$latest_prod_build" -gt 120000 ]; then
    echo "- ⚠️ **Build Time:** Approaching 2-minute warning (${latest_prod_build}ms)" >> "$TRENDS_REPORT"
else
    echo "- ✅ **Build Time:** Within acceptable range (${latest_prod_build}ms)" >> "$TRENDS_REPORT"
fi

prod_size_int=${latest_prod_size%.*}
if [ "$prod_size_int" -gt 1000 ]; then
    echo "- ❌ **Image Size:** Exceeds 1GB target (${latest_prod_size}MB)" >> "$TRENDS_REPORT"
    echo "  - Review multi-stage build optimization" >> "$TRENDS_REPORT"
    echo "  - Consider using alpine base images" >> "$TRENDS_REPORT"
elif [ "$prod_size_int" -gt 800 ]; then
    echo "- ⚠️ **Image Size:** Approaching 800MB warning (${latest_prod_size}MB)" >> "$TRENDS_REPORT"
else
    echo "- ✅ **Image Size:** Within acceptable range (${latest_prod_size}MB)" >> "$TRENDS_REPORT"
fi

if [ "$latest_startup" -gt 5000 ]; then
    echo "- ❌ **Startup Time:** Exceeds 5-second target (${latest_startup}ms)" >> "$TRENDS_REPORT"
    echo "  - Review application initialization" >> "$TRENDS_REPORT"
    echo "  - Consider optimizing dependencies" >> "$TRENDS_REPORT"
else
    echo "- ✅ **Startup Time:** Within acceptable range (${latest_startup}ms)" >> "$TRENDS_REPORT"
fi

memory_int=${latest_memory%.*}
if [ "$memory_int" -gt 512 ]; then
    echo "- ⚠️ **Memory Usage:** Above production target (${latest_memory}MB)" >> "$TRENDS_REPORT"
    echo "  - Monitor for memory leaks" >> "$TRENDS_REPORT"
    echo "  - Review memory-intensive operations" >> "$TRENDS_REPORT"
else
    echo "- ✅ **Memory Usage:** Within production limits (${latest_memory}MB)" >> "$TRENDS_REPORT"
fi

# Cleanup temp file
rm -f "$temp_file"

# Generate CSV export for further analysis
CSV_EXPORT="$REPORTS_DIR/performance-data-$TIMESTAMP.csv"
echo "timestamp,dev_build_ms,prod_build_ms,dev_size_mb,prod_size_mb,startup_ms,memory_mb,layers_dev,layers_prod" > "$CSV_EXPORT"

for file in $(ls -t $HISTORY_DIR/docker-metrics-*.json); do
    timestamp=$(jq -r '.timestamp // ""' "$file")
    dev_build=$(jq -r '.performance.development_build.value // ""' "$file")
    prod_build=$(jq -r '.performance.production_build.value // ""' "$file")
    dev_size=$(jq -r '.performance.dev_image_size_mb.value // ""' "$file")
    prod_size=$(jq -r '.performance.prod_image_size_mb.value // ""' "$file")
    startup=$(jq -r '.performance.container_startup.value // ""' "$file")
    memory=$(jq -r '.performance.memory_usage_mb.value // ""' "$file")
    layers_dev=$(jq -r '.performance.dev_layers.value // ""' "$file")
    layers_prod=$(jq -r '.performance.prod_layers.value // ""' "$file")
    
    echo "$timestamp,$dev_build,$prod_build,$dev_size,$prod_size,$startup,$memory,$layers_dev,$layers_prod" >> "$CSV_EXPORT"
done

# Generate performance charts (if gnuplot is available)
if command -v gnuplot &> /dev/null && [ "$DATA_COUNT" -gt 2 ]; then
    log "Generating performance charts..."
    
    CHART_SCRIPT="$REPORTS_DIR/generate-charts-$TIMESTAMP.gp"
    cat > "$CHART_SCRIPT" << EOF
set terminal png size 800,600
set output '$REPORTS_DIR/build-performance-$TIMESTAMP.png'
set title 'Docker Build Performance Over Time'
set xlabel 'Time'
set ylabel 'Build Time (ms)'
set datafile separator ','
set timefmt '%Y-%m-%dT%H:%M:%S'
set xdata time
set format x '%m/%d'
set grid
plot '$CSV_EXPORT' using 1:3 with lines title 'Production Build' lw 2, \\
     '$CSV_EXPORT' using 1:2 with lines title 'Development Build' lw 2

set output '$REPORTS_DIR/image-size-$TIMESTAMP.png'
set title 'Docker Image Size Over Time'
set ylabel 'Image Size (MB)'
plot '$CSV_EXPORT' using 1:5 with lines title 'Production Size' lw 2, \\
     '$CSV_EXPORT' using 1:4 with lines title 'Development Size' lw 2
EOF
    
    gnuplot "$CHART_SCRIPT" 2>/dev/null || warning "Chart generation failed"
fi

# Display results
echo ""
success "Performance analysis complete!"
echo ""
metric "Reports generated:"
echo "  📊 Trends Report: $TRENDS_REPORT"
echo "  📈 CSV Export: $CSV_EXPORT"

if [ -f "$REPORTS_DIR/build-performance-$TIMESTAMP.png" ]; then
    echo "  📈 Performance Charts: $REPORTS_DIR/*-$TIMESTAMP.png"
fi

echo ""
echo "🔍 Performance Summary:"
echo "======================"
cat "$TRENDS_REPORT" | grep -A 10 "### Current Performance"

echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Review full report: cat $TRENDS_REPORT"
echo "2. Monitor trends: watch -n 30 ./scripts/compare-performance.sh"
echo "3. Set up alerts: add thresholds to CI/CD pipeline"
echo "4. Optimize bottlenecks: focus on red metrics"
echo ""

# Return appropriate exit code based on performance
if [ "$latest_prod_build" -gt 300000 ] || [ "$prod_size_int" -gt 2000 ] || [ "$latest_startup" -gt 10000 ]; then
    warning "Performance thresholds exceeded - consider optimization"
    exit 2
else
    success "Performance within acceptable ranges"
    exit 0
fi 