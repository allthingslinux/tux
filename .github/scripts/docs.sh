#!/usr/bin/env bash
# Docs workflow helper scripts
# Usage: docs.sh <command> [args...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set change detection outputs for docs workflow
set_change_outputs() {
  local docs_changed="${1}"
  local code_changed="${2}"

  echo "docs=$docs_changed" >>"$GITHUB_OUTPUT"
  echo "code=$code_changed" >>"$GITHUB_OUTPUT"

  # Check if any relevant files changed
  if [[ "$docs_changed" == "true" ]] || [[ "$code_changed" == "true" ]]; then
    echo "any=true" >>"$GITHUB_OUTPUT"
  else
    echo "any=false" >>"$GITHUB_OUTPUT"
  fi
}

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
set-change-outputs)
  set_change_outputs "$@"
  ;;
prepare-coverage)
  prepare_coverage "$@"
  ;;
*)
  echo "Usage: docs.sh {set-change-outputs|prepare-coverage} [args...]"
  exit 1
  ;;
esac
