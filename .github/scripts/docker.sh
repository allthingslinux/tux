#!/usr/bin/env bash
# Docker workflow helper scripts
# Usage: docker.sh <command> [args...]

set -euo pipefail

# shellcheck disable=SC2034
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Generate PR version for Docker builds
generate_pr_version() {
  local pr_number="${1}"
  local sha="${2}"
  local sha_prefix_length="${3:-7}"

  # Generate git describe format for PR builds to match VERSIONING.md expectations
  local pr_version
  pr_version="pr-${pr_number}-$(echo "$sha" | cut -c1-"${sha_prefix_length}")"
  echo "version=$pr_version" >> "$GITHUB_OUTPUT"
  echo "Generated PR version: $pr_version"
}

# Generate release version for Docker builds
generate_release_version() {
  local github_ref="${1}"
  local sha_prefix_length="${2}"

  # Generate git describe format for release builds to match VERSIONING.md expectations
  # This ensures the VERSION file contains the exact format expected by __init__.py
  local tag_version="${github_ref#refs/tags/}"
  local clean_version="${tag_version#v}" # Remove 'v' prefix if present
  local release_version="$clean_version"
  echo "version=$release_version" >> "$GITHUB_OUTPUT"
  echo "Generated release version: $release_version"
}

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
  generate-pr-version)
    generate_pr_version "$@"
    ;;
  generate-release-version)
    generate_release_version "$@"
    ;;
  *)
    echo "Usage: docker.sh {generate-pr-version|generate-release-version} [args...]"
    exit 1
    ;;
esac
