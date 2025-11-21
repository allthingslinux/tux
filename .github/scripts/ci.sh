#!/usr/bin/env bash
# CI workflow helper scripts
# Usage: ci.sh <command> [args...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set change detection outputs for CI workflow
set_change_outputs() {
  local python_changed="${1}"
  local markdown_changed="${2}"
  local shell_changed="${3}"
  local workflow_changed="${4}"
  local docker_changed="${5}"
  local yaml_changed="${6}"

  {
    echo "python=$python_changed"
    echo "markdown=$markdown_changed"
    echo "shell=$shell_changed"
    echo "workflows=$workflow_changed"
    echo "docker=$docker_changed"
    echo "yaml=$yaml_changed"
  } >>"$GITHUB_OUTPUT"

  # Check if any files changed
  if [[ "$python_changed" == "true" ]] ||
    [[ "$markdown_changed" == "true" ]] ||
    [[ "$shell_changed" == "true" ]] ||
    [[ "$workflow_changed" == "true" ]] ||
    [[ "$docker_changed" == "true" ]] ||
    [[ "$yaml_changed" == "true" ]]; then
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
  echo "Usage: ci.sh {set-change-outputs} [args...]"
  exit 1
  ;;
esac
