#!/usr/bin/env bash
# Shared utility functions for GitHub Actions scripts
# Usage: shared.sh <command> [args...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Calculate size in GB from bytes
calculate_size_gb() {
  local bytes="${1:-0}"
  python3 -c "print(f'{int(\"$bytes\") / 1024 / 1024 / 1024:.2f}')"
}

# Compare size in GB against threshold
compare_size() {
  local size_gb="${1:-0}"
  local threshold="${2:-${REGISTRY_SIZE_WARNING_GB:-5}}"
  python3 -c "
size = float('$size_gb')
threshold = float('$threshold')
print('true' if size > threshold else 'false')
"
}

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
  calculate-size-gb)
    calculate_size_gb "$@"
    ;;
  compare-size)
    compare_size "$@"
    ;;
  *)
    echo "Usage: shared.sh {calculate-size-gb|compare-size} [args...]"
    exit 1
    ;;
esac
