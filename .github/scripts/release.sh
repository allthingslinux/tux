#!/usr/bin/env bash
# Release workflow helper scripts
# Usage: release.sh <command> [args...]

set -euo pipefail

# shellcheck disable=SC2034
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Determine version from event or tag
determine_version() {
  local event_name="${1}"
  local input_version="${2:-}"

  local version
  if [ "$event_name" = "workflow_dispatch" ]; then
    version="$input_version"
  else
    version="${GITHUB_REF#refs/tags/}"
  fi

  echo "version=$version" >> "$GITHUB_OUTPUT"

  # Check if this is a prerelease (contains alpha, beta, rc)
  if [[ $version =~ (alpha|beta|rc)   ]]; then
    echo "is_prerelease=true" >> "$GITHUB_OUTPUT"
  else
    echo "is_prerelease=false" >> "$GITHUB_OUTPUT"
  fi

  echo "Release version: $version"
}

# Determine version without v prefix and default branch
determine_version_and_branch() {
  local version="${1}"

  # Strip 'v' prefix if present (semver format doesn't include it)
  local version_no_v="${version#v}"
  echo "version_no_v=$version_no_v" >> "$GITHUB_OUTPUT"

  # Determine target branch for committing changelog
  # Try to find the default branch, fallback to common branch names
  local default_branch
  default_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2> /dev/null | sed 's@^refs/remotes/origin/@@' || echo "")

  if [ -z "$default_branch" ]; then
    # Try common branch names
    if git show-ref --verify --quiet refs/remotes/origin/main; then
      default_branch="main"
    elif git show-ref --verify --quiet refs/remotes/origin/master; then
      default_branch="master"
    else
      # Fallback: use the first branch we find
      default_branch=$(git branch -r | grep -v HEAD | head -n1 | sed 's/origin\///' | xargs)
    fi
  fi

  echo "branch=$default_branch" >> "$GITHUB_OUTPUT"
  echo "Version (no v): $version_no_v"
  echo "Target branch: $default_branch"

  # Checkout the branch (not the tag) so we can commit changelog updates
  git checkout "$default_branch" || git checkout -b "$default_branch"
  git pull origin "$default_branch" || true
}

# Configure git for GitHub Actions
configure_git() {
  git config user.name "github-actions[bot]"
  git config user.email "github-actions[bot]@users.noreply.github.com"
}

# Commit updated changelog
commit_changelog() {
  local version="${1}"
  local branch="${2}"

  if [ -n "$(git status --porcelain CHANGELOG.md)" ]; then
    git add CHANGELOG.md
    git commit -m "chore: bump changelog to $version"
    git push origin "$branch"
  else
    echo "No changes to CHANGELOG.md"
  fi
}

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
  determine-version)
    determine_version "$@"
    ;;
  determine-version-and-branch)
    determine_version_and_branch "$@"
    ;;
  configure-git)
    configure_git "$@"
    ;;
  commit-changelog)
    commit_changelog "$@"
    ;;
  *)
    echo "Usage: release.sh {determine-version|determine-version-and-branch|configure-git|commit-changelog} [args...]"
    exit 1
    ;;
esac
