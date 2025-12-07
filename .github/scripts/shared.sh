#!/usr/bin/env bash
# Shared utility functions for GitHub Actions scripts
# Usage: shared.sh <command> [args...]

set -euo pipefail

# shellcheck disable=SC2034
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Calculate size in GB from bytes
calculate_size_gb() {
  local bytes="${1:-0}"
  python3 -c "import sys; print(f'{int(sys.argv[1]) / 1024 / 1024 / 1024:.2f}')" "$bytes"
}

# Compare size in GB against threshold
compare_size() {
  local size_gb="${1:-0}"
  local threshold="${2:-${REGISTRY_SIZE_WARNING_GB:-5}}"
  python3 -c "import sys; size = float(sys.argv[1]); threshold = float(sys.argv[2]); print('true' if size > threshold else 'false')" "$size_gb" "$threshold"
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
