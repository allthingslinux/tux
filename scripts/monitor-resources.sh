#!/bin/bash

# Docker Resource Monitoring Script
# Monitor container performance in real-time

set -e

CONTAINER_NAME=${1:-"tux-dev"}
DURATION=${2:-60}
INTERVAL=${3:-5}

echo "🔍 Docker Resource Monitor"
echo "=========================="
echo "Container: $CONTAINER_NAME"
echo "Duration: ${DURATION}s"
echo "Interval: ${INTERVAL}s"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Create logs directory
mkdir -p logs

# Log file with timestamp
LOG_FILE="logs/resource-monitor-$(date +%Y%m%d-%H%M%S).csv"
REPORT_FILE="logs/resource-report-$(date +%Y%m%d-%H%M%S).txt"

log() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

metric() {
    echo -e "${BLUE}📊 $1${NC}"
}

# Check if container exists
if ! docker ps -a | grep -q "$CONTAINER_NAME"; then
    error "Container '$CONTAINER_NAME' not found"
fi

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    warning "Container '$CONTAINER_NAME' is not running"
    echo "Starting container..."
    
    # Try to start the container
    if docker start "$CONTAINER_NAME" &>/dev/null; then
        success "Container started"
        sleep 2
    else
        error "Failed to start container"
    fi
fi

log "Starting resource monitoring..."
log "Output file: $LOG_FILE"

# Create CSV header
echo "timestamp,cpu_percent,memory_usage,memory_limit,memory_percent,network_input,network_output,block_input,block_output,pids" > "$LOG_FILE"

# Initialize counters for statistics
total_samples=0
cpu_sum=0
memory_sum=0
network_in_sum=0
network_out_sum=0

# Start monitoring
for i in $(seq 1 $((DURATION/INTERVAL))); do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Get container stats
    stats_output=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}" "$CONTAINER_NAME" 2>/dev/null)
    
    if [ -n "$stats_output" ]; then
        # Parse the stats
        IFS=',' read -r cpu_percent mem_usage mem_percent net_io block_io pids <<< "$stats_output"
        
        # Extract memory usage and limit
        memory_usage=$(echo "$mem_usage" | sed 's/MiB.*//' | sed 's/[^0-9.]//g')
        memory_limit=$(echo "$mem_usage" | sed 's/.*\///' | sed 's/MiB//' | sed 's/[^0-9.]//g')
        
        # Extract network I/O
        network_input=$(echo "$net_io" | sed 's/\/.*//' | sed 's/[^0-9.]//g')
        network_output=$(echo "$net_io" | sed 's/.*\///' | sed 's/[^0-9.]//g')
        
        # Extract block I/O
        block_input=$(echo "$block_io" | sed 's/\/.*//' | sed 's/[^0-9.]//g')
        block_output=$(echo "$block_io" | sed 's/.*\///' | sed 's/[^0-9.]//g')
        
        # Clean up percentages
        cpu_clean=$(echo "$cpu_percent" | sed 's/%//')
        mem_percent_clean=$(echo "$mem_percent" | sed 's/%//')
        
        # Write to CSV
        echo "$timestamp,$cpu_clean,$memory_usage,$memory_limit,$mem_percent_clean,$network_input,$network_output,$block_input,$block_output,$pids" >> "$LOG_FILE"
        
        # Display real-time stats
        printf "\r\033[K📊 CPU: %6s | Memory: %6s/%6s MiB (%5s) | Net I/O: %8s/%8s | PIDs: %3s" \
            "$cpu_percent" "$memory_usage" "$memory_limit" "$mem_percent" "$network_input" "$network_output" "$pids"
        
        # Update statistics
        if [[ "$cpu_clean" =~ ^[0-9.]+$ ]]; then
            cpu_sum=$(echo "$cpu_sum + $cpu_clean" | bc -l)
        fi
        if [[ "$memory_usage" =~ ^[0-9.]+$ ]]; then
            memory_sum=$(echo "$memory_sum + $memory_usage" | bc -l)
        fi
        if [[ "$network_input" =~ ^[0-9.]+$ ]]; then
            network_in_sum=$(echo "$network_in_sum + $network_input" | bc -l)
        fi
        if [[ "$network_output" =~ ^[0-9.]+$ ]]; then
            network_out_sum=$(echo "$network_out_sum + $network_output" | bc -l)
        fi
        
        total_samples=$((total_samples + 1))
    else
        warning "Failed to get stats for container $CONTAINER_NAME"
    fi
    
    sleep "$INTERVAL"
done

echo ""
echo ""
log "Monitoring completed. Generating report..."

# Calculate averages
if [ "$total_samples" -gt 0 ]; then
    avg_cpu=$(echo "scale=2; $cpu_sum / $total_samples" | bc -l)
    avg_memory=$(echo "scale=2; $memory_sum / $total_samples" | bc -l)
    avg_network_in=$(echo "scale=2; $network_in_sum / $total_samples" | bc -l)
    avg_network_out=$(echo "scale=2; $network_out_sum / $total_samples" | bc -l)
else
    avg_cpu="0"
    avg_memory="0"
    avg_network_in="0"
    avg_network_out="0"
fi

# Generate report
cat > "$REPORT_FILE" << EOF
# Docker Resource Monitoring Report

**Container:** $CONTAINER_NAME
**Duration:** ${DURATION}s (${total_samples} samples)
**Generated:** $(date -Iseconds)

## Performance Summary

### Average Resource Usage
- **CPU Usage:** ${avg_cpu}%
- **Memory Usage:** ${avg_memory} MiB
- **Network Input:** ${avg_network_in} B
- **Network Output:** ${avg_network_out} B

### Resource Analysis
EOF

# Analyze performance against thresholds
if [ "$(echo "$avg_cpu > 80" | bc -l)" -eq 1 ]; then
    echo "- ❌ **High CPU Usage:** Average ${avg_cpu}% exceeds 80% threshold" >> "$REPORT_FILE"
    echo "  - Consider optimizing CPU-intensive operations" >> "$REPORT_FILE"
elif [ "$(echo "$avg_cpu > 50" | bc -l)" -eq 1 ]; then
    echo "- ⚠️ **Moderate CPU Usage:** Average ${avg_cpu}% approaching high usage" >> "$REPORT_FILE"
else
    echo "- ✅ **CPU Usage:** Average ${avg_cpu}% within normal range" >> "$REPORT_FILE"
fi

if [ "$(echo "$avg_memory > 400" | bc -l)" -eq 1 ]; then
    echo "- ❌ **High Memory Usage:** Average ${avg_memory}MiB exceeds 400MiB threshold" >> "$REPORT_FILE"
    echo "  - Monitor for memory leaks or optimize memory usage" >> "$REPORT_FILE"
elif [ "$(echo "$avg_memory > 256" | bc -l)" -eq 1 ]; then
    echo "- ⚠️ **Moderate Memory Usage:** Average ${avg_memory}MiB approaching limits" >> "$REPORT_FILE"
else
    echo "- ✅ **Memory Usage:** Average ${avg_memory}MiB within normal range" >> "$REPORT_FILE"
fi

# Get peak values from CSV
if [ -f "$LOG_FILE" ] && [ "$total_samples" -gt 0 ]; then
    peak_cpu=$(tail -n +2 "$LOG_FILE" | cut -d',' -f2 | sort -n | tail -1)
    peak_memory=$(tail -n +2 "$LOG_FILE" | cut -d',' -f3 | sort -n | tail -1)
    
    echo "" >> "$REPORT_FILE"
    echo "### Peak Usage" >> "$REPORT_FILE"
    echo "- **Peak CPU:** ${peak_cpu}%" >> "$REPORT_FILE"
    echo "- **Peak Memory:** ${peak_memory} MiB" >> "$REPORT_FILE"
fi

# Add CSV data location
echo "" >> "$REPORT_FILE"
echo "## Data Files" >> "$REPORT_FILE"
echo "- **CSV Data:** $LOG_FILE" >> "$REPORT_FILE"
echo "- **Report:** $REPORT_FILE" >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"
echo "## Analysis Commands" >> "$REPORT_FILE"
echo "\`\`\`bash" >> "$REPORT_FILE"
echo "# View peak CPU usage" >> "$REPORT_FILE"
echo "tail -n +2 $LOG_FILE | cut -d',' -f2 | sort -n | tail -5" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "# View peak memory usage" >> "$REPORT_FILE"
echo "tail -n +2 $LOG_FILE | cut -d',' -f3 | sort -n | tail -5" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "# Plot CPU over time (if gnuplot available)" >> "$REPORT_FILE"
echo "gnuplot -e \"set terminal dumb; set datafile separator ','; plot '$LOG_FILE' using 2 with lines title 'CPU %'\"" >> "$REPORT_FILE"
echo "\`\`\`" >> "$REPORT_FILE"

# Display summary
echo ""
success "Resource monitoring completed!"
echo ""
metric "Performance Summary:"
echo "  📊 Average CPU: ${avg_cpu}%"
echo "  💾 Average Memory: ${avg_memory} MiB"
echo "  🌐 Network I/O: ${avg_network_in}B in, ${avg_network_out}B out"
echo "  📋 Total Samples: $total_samples"

echo ""
echo "📁 Generated Files:"
echo "  📈 CSV Data: $LOG_FILE"
echo "  📊 Report: $REPORT_FILE"

echo ""
echo "🔍 Analysis:"
cat "$REPORT_FILE" | grep -A 20 "### Average Resource Usage"

# Generate simple chart if gnuplot is available
if command -v gnuplot &> /dev/null && [ "$total_samples" -gt 5 ]; then
    log "Generating performance chart..."
    
    chart_file="logs/resource-chart-$(date +%Y%m%d-%H%M%S).png"
    gnuplot << EOF
set terminal png size 800,400
set output '$chart_file'
set title 'Container Resource Usage Over Time'
set xlabel 'Sample'
set ylabel 'Usage'
set datafile separator ','
set key outside
set grid
plot '$LOG_FILE' using 0:2 with lines title 'CPU %' lw 2, \
     '$LOG_FILE' using 0:(\$3/10) with lines title 'Memory (MiB/10)' lw 2
EOF
    
    if [ -f "$chart_file" ]; then
        echo "  📈 Chart: $chart_file"
    fi
fi

echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Review detailed report: cat $REPORT_FILE"
echo "2. Analyze CSV data: cat $LOG_FILE"
echo "3. Monitor continuously: watch -n 5 'docker stats $CONTAINER_NAME --no-stream'"
echo "4. Set up alerts if thresholds exceeded"
echo ""

# Return appropriate exit code based on performance
if [ "$(echo "$avg_cpu > 80" | bc -l)" -eq 1 ] || [ "$(echo "$avg_memory > 400" | bc -l)" -eq 1 ]; then
    warning "Resource usage exceeded thresholds - consider optimization"
    exit 2
else
    success "Resource usage within acceptable ranges"
    exit 0
fi 