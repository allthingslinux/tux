#!/usr/bin/env bash
# Docs workflow helper scripts
# Usage: docs.sh <command> [args...]

set -euo pipefail

# shellcheck disable=SC2034
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prepare coverage reports for MkDocs
prepare_coverage() {
  echo "Preparing coverage reports for mkdocs-coverage plugin..."

  if [ -d "htmlcov" ] && [ "$(ls -A htmlcov)" ]; then
    cp -r htmlcov docs/
    echo "Copied htmlcov from tests workflow to docs/htmlcov for mkdocs-coverage plugin"
  else
    echo "ERROR: Coverage data not found after tests workflow completed"
    exit 1
  fi
}

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
  prepare-coverage)
    prepare_coverage "$@"
    ;;
  *)
    echo "Usage: docs.sh {prepare-coverage} [args...]"
    exit 1
    ;;
esac
