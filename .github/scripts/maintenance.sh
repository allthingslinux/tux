#!/usr/bin/env bash
# Maintenance workflow helper scripts
# Usage: maintenance.sh <command> [args...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/shared.sh"

# Generate repository health summary header
health_repository_summary() {
  {
    echo "## Repository Health Check"
    echo "**Date**: $(date)"
    echo ""
  } >> "$GITHUB_STEP_SUMMARY"
}

# Check Docker registry size
registry_size_check() {
  local package_name="${1}"
  local registry_size_warning_gb="${2}"

  echo "Checking registry size..."

  # Get package info to check size
  local package_info
  package_info=$(gh api "user/packages/container/$package_name" 2> /dev/null || echo '{"size_in_bytes": 0}')
  local size_bytes
  size_bytes=$(echo "$package_info" | jq -r '.size_in_bytes // 0')
  local size_gb
  size_gb=$("$SHARED" calculate-size-gb "$size_bytes")
  local size_warning
  size_warning=$("$SHARED" compare-size "$size_gb" "$registry_size_warning_gb")

  {
    echo "size_gb=$size_gb"
    echo "size_warning=$size_warning"
  } >> "$GITHUB_OUTPUT"

  echo "Registry size: ${size_gb}GB"

  # Alert if size is too large
  if [ "$size_warning" = "true" ]; then
    echo "Registry size exceeds ${registry_size_warning_gb}GB: ${size_gb}GB"
  else
    echo "Registry size is acceptable: ${size_gb}GB"
  fi
}

# Clean build cache images older than specified days
clean_build_cache_images() {
  local package_name="${1}"
  local days_old="${2}"

  echo "Cleaning up build cache images..."
  # Delete build cache images older than specified days
  gh api "user/packages/container/$package_name/versions" \
                                                          | jq -r --arg cutoff "$(date -d "${days_old} days ago" -Iseconds)" \
      '.[] | select(.name | contains("buildcache")) | select(.created_at < $cutoff) | .id' \
                                                                                           | xargs -I {} gh api -X DELETE "user/packages/container/$package_name/versions/{}" \
                                                                                     || echo "No build cache images to clean"
}

# Generate registry cleanup summary
registry_cleanup_summary() {
  local size_gb="${1}"
  local size_warning="${2}"
  local default_keep_versions="${3}"
  local build_cache_cleanup_days="${4}"

  {
    echo "## Registry Cleanup Summary"
    echo "- **Registry Size**: ${size_gb}GB"
    echo "- **Cleanup Policy**: Keep ${default_keep_versions} versions, remove untagged"
    echo "- **Build Cache**: Cleaned images older than ${build_cache_cleanup_days} days"
    if [ "$size_warning" = "true" ]; then
      echo "- **Warning**: Registry size exceeds 5GB"
    else
      echo "- **Status**: Registry size is acceptable"
    fi
  } >> "$GITHUB_STEP_SUMMARY"
}

# Check for large files in repository
check_large_files() {
  local size_mb="${1}"

  {
    echo "### Large Files Check"
    echo "Checking for files larger than ${size_mb}MB..."
  } >> "$GITHUB_STEP_SUMMARY"

  local large_files
  large_files=$(find . -type f -size +"${size_mb}M" -not -path "./.git/*" 2> /dev/null || echo "")

  if [ -n "$large_files" ]; then
    {
      echo "**Large files found:**"
      echo '```'
      echo "$large_files"
      echo '```'
    } >> "$GITHUB_STEP_SUMMARY"
  else
    echo "**No large files found**" >> "$GITHUB_STEP_SUMMARY"
  fi
  echo "" >> "$GITHUB_STEP_SUMMARY"
}

# Check for outdated dependencies
check_dependencies() {
  {
    echo "### Dependencies Check"
    echo "Checking for outdated dependencies..."
  } >> "$GITHUB_STEP_SUMMARY"

  if command -v uv > /dev/null 2>&1; then
    local outdated
    outdated=$(uv outdated 2> /dev/null || echo "No outdated dependencies found")
    {
      echo '```'
      echo "$outdated"
      echo '```'
    } >> "$GITHUB_STEP_SUMMARY"
  else
    echo "**uv not available for dependency check**" >> "$GITHUB_STEP_SUMMARY"
  fi
  echo "" >> "$GITHUB_STEP_SUMMARY"
}

# Check repository size
check_repository_size() {
  {
    echo "### Repository Size Analysis"
    local repo_size
    repo_size=$(du -sh . 2> /dev/null | cut -f1 || echo "Unknown")
    echo "**Repository Size**: $repo_size"

    # Check .git size
    local git_size
    git_size=$(du -sh .git 2> /dev/null | cut -f1 || echo "Unknown")
    echo "**Git History Size**: $git_size"
    echo ""
  } >> "$GITHUB_STEP_SUMMARY"
}

# Check stale branches
check_stale_branches() {
  local limit="${1}"

  {
    echo "### Branch Analysis"
    echo "**Recent branches:**"
    echo '```'
    git branch -r --sort=-committerdate | head -"$limit" 2> /dev/null || echo "Could not check branches"
    echo '```'
    echo ""
  } >> "$GITHUB_STEP_SUMMARY"
}

# Check container registry health
check_registry_health() {
  local package_name="${1}"
  local registry_size_warning_gb="${2}"

  {
    echo "### Container Registry Health"
    if command -v gh > /dev/null 2>&1; then
      # Get package info
      local package_info
      package_info=$(gh api "user/packages/container/$package_name" 2> /dev/null || echo '{"size_in_bytes": 0, "version_count": 0}')
      local size_bytes
      size_bytes=$(echo "$package_info" | jq -r '.size_in_bytes // 0')
      local version_count
      version_count=$(echo "$package_info" | jq -r '.version_count // 0')
      local size_gb
      size_gb=$("$SHARED" calculate-size-gb "$size_bytes")
      echo "**Registry Size**: ${size_gb}GB"
      echo "**Version Count**: $version_count"

      local size_warning
      size_warning=$("$SHARED" compare-size "$size_gb" "$registry_size_warning_gb")
      if [ "$size_warning" = "true" ]; then
        echo "**Warning**: Registry size exceeds ${registry_size_warning_gb}GB"
      else
        echo "**Status**: Registry size is acceptable"
      fi
    else
      echo "**GitHub CLI not available for registry check**"
    fi
    echo ""
  } >> "$GITHUB_STEP_SUMMARY"
}

# Check recent activity
check_recent_activity() {
  local since="${1}"
  local limit="${2}"

  {
    echo "### Recent Activity"
    echo "**Recent commits:**"
    echo '```'
    git log --oneline --since="$since" | head -"$limit" 2> /dev/null || echo "Could not check recent commits"
    echo '```'
    echo ""
  } >> "$GITHUB_STEP_SUMMARY"
}

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
  health-repository-summary)
    health_repository_summary "$@"
    ;;
  registry-size-check)
    registry_size_check "$@"
    ;;
  clean-build-cache-images)
    clean_build_cache_images "$@"
    ;;
  registry-cleanup-summary)
    registry_cleanup_summary "$@"
    ;;
  check-large-files)
    check_large_files "$@"
    ;;
  check-dependencies)
    check_dependencies "$@"
    ;;
  check-repository-size)
    check_repository_size "$@"
    ;;
  check-stale-branches)
    check_stale_branches "$@"
    ;;
  check-registry-health)
    check_registry_health "$@"
    ;;
  check-recent-activity)
    check_recent_activity "$@"
    ;;
  *)
    echo "Usage: maintenance.sh {health-repository-summary|registry-size-check|clean-build-cache-images|registry-cleanup-summary|check-large-files|check-dependencies|check-repository-size|check-stale-branches|check-registry-health|check-recent-activity} [args...]"
    exit 1
    ;;
esac
