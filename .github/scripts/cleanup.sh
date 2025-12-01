#!/usr/bin/env bash
# Cleanup workflow helper scripts
# Usage: cleanup.sh <command> [args...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/shared.sh"

# Setup cleanup parameters based on cleanup type
setup_cleanup_params() {
  local cleanup_type="${1}"
  local keep_versions_input="${2}"
  local dry_run_input="${3}"
  local standard_keep_versions="${4}"
  local aggressive_keep_versions="${5}"
  local build_cache_only_keep_versions="${6}"

  local keep_versions=""
  local remove_untagged="false"
  local clean_build_cache="false"

  case "$cleanup_type" in
    "standard")
      keep_versions="${keep_versions_input:-$standard_keep_versions}"
      remove_untagged="true"
      clean_build_cache="true"
      ;;
    "aggressive")
      keep_versions="${keep_versions_input:-$aggressive_keep_versions}"
      remove_untagged="true"
      clean_build_cache="true"
      ;;
    "build-cache-only")
      keep_versions="$build_cache_only_keep_versions"
      remove_untagged="false"
      clean_build_cache="true"
      ;;
    *)
      echo "Error: Unknown cleanup type: $cleanup_type" >&2
      exit 1
      ;;
  esac

  {
    echo "keep_versions=$keep_versions"
    echo "remove_untagged=$remove_untagged"
    echo "clean_build_cache=$clean_build_cache"
    echo "cleanup_type=$cleanup_type"
    echo "dry_run=$dry_run_input"
  } >> "$GITHUB_OUTPUT"
}

# Analyze Docker registry and output summary
registry_analysis() {
  local package_type="${1}"
  local package_name="${2}"
  local version_limit="${3}"
  # registry_size_warning_gb is kept for API compatibility but not used in this function
  # shellcheck disable=SC2034
  local registry_size_warning_gb="${4}"

  local size_bytes
  local version_count
  local size_gb

  # Get current registry info
  local package_info
  package_info=$(gh api "user/packages/$package_type/$package_name" 2> /dev/null || echo '{"size_in_bytes": 0, "version_count": 0}')
  size_bytes=$(echo "$package_info" | jq -r '.size_in_bytes // 0')
  version_count=$(echo "$package_info" | jq -r '.version_count // 0')
  size_gb=$("$SHARED" calculate-size-gb "$size_bytes")

  {
    echo "## Registry Analysis"
    echo "**Current Registry Size**: ${size_gb}GB"
    echo "**Current Version Count**: $version_count"
    echo ""
    echo "**Current Versions:**"
    echo '```'
  } >> "$GITHUB_STEP_SUMMARY"

  # List current versions
  gh api "user/packages/$package_type/$package_name/versions" 2> /dev/null \
                                                                          | jq -r '.[] | "\(.name) - \(.created_at) - \(.size_in_bytes) bytes"' \
                                                                        | head -"$version_limit" >> "$GITHUB_STEP_SUMMARY" || echo "Could not list versions" >> "$GITHUB_STEP_SUMMARY"

  {
    echo '```'
    echo ""
  } >> "$GITHUB_STEP_SUMMARY"

  echo "size_gb=$size_gb" >> "$GITHUB_OUTPUT"
  echo "version_count=$version_count" >> "$GITHUB_OUTPUT"
}

# Clean old Docker image versions
clean_old_versions() {
  local package_type="${1}"
  local package_name="${2}"
  local keep_versions="${3}"
  local remove_untagged="${4}"
  local dry_run="${5}"

  {
    echo "## Cleaning Old Versions"
    if [ "$dry_run" = "true" ]; then
      echo "**DRY RUN**: Would keep $keep_versions versions"
      echo "**DRY RUN**: Would remove untagged: $remove_untagged"
    else
      echo "Cleaning old versions..."
      gh api -X DELETE "user/packages/$package_type/$package_name/versions" \
        --field "min-versions-to-keep=$keep_versions" \
        --field "delete-only-untagged-versions=$remove_untagged" \
                                                                 || echo "Cleanup completed or no versions to clean"
    fi
    echo ""
  } >> "$GITHUB_STEP_SUMMARY"
}

# Clean build cache images older than specified days
clean_build_cache() {
  local package_type="${1}"
  local package_name="${2}"
  local days_old="${3}"
  local dry_run="${4}"

  echo "## Cleaning Build Cache" >> "$GITHUB_STEP_SUMMARY"

  # Find build cache images older than specified days
  local cutoff_date
  cutoff_date=$(date -d "${days_old} days ago" -Iseconds)
  local build_cache_images
  build_cache_images=$(gh api "user/packages/$package_type/$package_name/versions" 2> /dev/null \
                                                                                               | jq -r --arg cutoff "$cutoff_date" '.[] | select(.name | contains("buildcache")) | select(.created_at < $cutoff) | .id' || echo "")

  if [ -n "$build_cache_images" ]; then
    {
      echo "**Found build cache images to clean:**"
      echo '```'
      echo "$build_cache_images"
      echo '```'
    } >> "$GITHUB_STEP_SUMMARY"

    if [ "$dry_run" = "true" ]; then
      echo "**DRY RUN**: Would delete these build cache images" >> "$GITHUB_STEP_SUMMARY"
    else
      echo "$build_cache_images" | xargs -I {} gh api -X DELETE "user/packages/$package_type/$package_name/versions/{}" \
                                                                                                                        || echo "Build cache cleanup completed" >> "$GITHUB_STEP_SUMMARY"
    fi
  else
    echo "**No build cache images to clean**" >> "$GITHUB_STEP_SUMMARY"
  fi
  echo "" >> "$GITHUB_STEP_SUMMARY"
}

# Generate cleanup summary
cleanup_summary() {
  local cleanup_type="${1}"
  local keep_versions="${2}"
  local remove_untagged="${3}"
  local clean_build_cache="${4}"
  local dry_run="${5}"
  # default_keep_versions is kept for API compatibility but not used in this function
  # shellcheck disable=SC2034
  local default_keep_versions="${6}"
  local build_cache_cleanup_days="${7}"

  {
    echo "## Cleanup Summary"
    echo "**Cleanup Type**: $cleanup_type"
    echo "**Versions Kept**: $keep_versions"
    echo "**Untagged Removed**: $remove_untagged"
    echo "**Build Cache Cleaned**: $clean_build_cache (older than ${build_cache_cleanup_days} days)"
    echo "**Dry Run**: $dry_run"
    echo ""
    if [ "$dry_run" = "false" ]; then
      echo "**Status**: Cleanup completed successfully"
    else
      echo "**Status**: Dry run completed - no changes made"
    fi
  } >> "$GITHUB_STEP_SUMMARY"
}

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
  setup-cleanup-params)
    setup_cleanup_params "$@"
    ;;
  registry-analysis)
    registry_analysis "$@"
    ;;
  clean-old-versions)
    clean_old_versions "$@"
    ;;
  clean-build-cache)
    clean_build_cache "$@"
    ;;
  cleanup-summary)
    cleanup_summary "$@"
    ;;
  *)
    echo "Usage: cleanup.sh {setup-cleanup-params|registry-analysis|clean-old-versions|clean-build-cache|cleanup-summary} [args...]"
    exit 1
    ;;
esac
