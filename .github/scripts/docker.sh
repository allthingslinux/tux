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

# Validate build configuration
validate_build_config() {
  local git_sha="${1}"

  # Validate that required build args are available
  if [ -z "$git_sha" ]; then
    echo "Error: GIT_SHA is required"
    exit 1
  fi
  echo "✓ Build configuration validated"
}

# Calculate SOURCE_DATE_EPOCH for reproducible builds
calculate_source_date_epoch() {
  local commit_timestamp="${1:-}"
  local repo_created_at="${2:-}"

  # Calculate SOURCE_DATE_EPOCH for reproducible builds
  # Priority: commit timestamp > repository creation date > current time
  # Note: Input timestamps are ISO 8601 strings (e.g., 2025-01-01T12:34:56Z) from GitHub context
  local source_date_epoch
  if [ -n "$commit_timestamp" ]; then
    # Parse ISO 8601 timestamp string to Unix epoch (seconds)
    source_date_epoch=$(date -d "$commit_timestamp" +%s)
  elif [ -n "$repo_created_at" ]; then
    # Parse ISO 8601 timestamp string to Unix epoch (seconds)
    source_date_epoch=$(date -d "$repo_created_at" +%s)
  else
    # Fallback to current time
    source_date_epoch=$(date +%s)
  fi
  echo "epoch=$source_date_epoch" >> "$GITHUB_OUTPUT"
  echo "SOURCE_DATE_EPOCH=$source_date_epoch"
}

# Generate BUILD_DATE in ISO 8601 format
generate_build_date() {
  date -u +'%Y-%m-%dT%H:%M:%SZ'
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
  validate-build-config)
    validate_build_config "$@"
    ;;
  calculate-source-date-epoch)
    calculate_source_date_epoch "$@"
    ;;
  generate-build-date)
    generate_build_date "$@"
    ;;
  *)
    echo "Usage: docker.sh {generate-pr-version|generate-release-version|validate-build-config|calculate-source-date-epoch|generate-build-date} [args...]"
    exit 1
    ;;
esac
