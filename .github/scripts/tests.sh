#!/usr/bin/env bash
# Tests workflow helper scripts
# Usage: tests.sh <command> [args...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set change detection outputs for tests workflow
set_change_outputs() {
  local python_changed="${1}"
  local tests_changed="${2}"

  {
    echo "python=$python_changed"
    echo "tests=$tests_changed"
  } >>"$GITHUB_OUTPUT"

  # Check if any relevant files changed
  if [[ "$python_changed" == "true" ]] || [[ "$tests_changed" == "true" ]]; then
    echo "any=true" >>"$GITHUB_OUTPUT"
  else
    echo "any=false" >>"$GITHUB_OUTPUT"
  fi
}

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
set-change-outputs)
  set_change_outputs "$@"
  ;;
*)
  echo "Usage: tests.sh {set-change-outputs} [args...]"
  exit 1
  ;;
esac
