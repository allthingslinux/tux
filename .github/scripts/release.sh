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
  # Handle both "v0.1.0" and " v0.1.0" cases
  local version_no_v="${version}"
  version_no_v="${version_no_v#"${version_no_v%%[![:space:]]*}"}"  # trim leading whitespace first
  version_no_v="${version_no_v#v}"  # then strip 'v' prefix
  version_no_v="${version_no_v%"${version_no_v##*[![:space:]]}"}"  # trim trailing whitespace
  echo "version_no_v=$version_no_v" >> "$GITHUB_OUTPUT"

  # Check if this is a fixed version (contains numbers and dots/dashes) vs a keyword
  # Keywords: major, premajor, minor, preminor, patch, prepatch, prerelease
  # Fixed versions: 0.1.0, 0.1.0-rc.5, 1.2.3-beta.1, etc.
  # A fixed version starts with a digit and contains at least one dot (semver format)
  local is_fixed_version=false
  if [[ "$version_no_v" =~ ^[0-9]+\. ]]; then
    is_fixed_version=true
  fi
  echo "is_fixed_version=$is_fixed_version" >> "$GITHUB_OUTPUT"

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
  echo "Is fixed version: $is_fixed_version"
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

# Manually bump changelog with fixed version
# This is used when we have a fixed version string (e.g., 0.1.0-rc.5)
# instead of a version bump keyword (e.g., prerelease)
bump_changelog_fixed() {
  local version="${1}"
  local changelog="${2:-CHANGELOG.md}"
  local keep_unreleased="${3:-false}"

  # Get current date in ISO 8601 format (YYYY-MM-DD)
  local release_date
  release_date=$(date +%Y-%m-%d)

  # Check if changelog exists
  if [ ! -f "$changelog" ]; then
    echo "Error: Changelog file '$changelog' not found"
    exit 1
  fi

  # Check if Unreleased section exists
  if ! grep -q "^## \[Unreleased\]" "$changelog"; then
    echo "Error: No [Unreleased] section found in $changelog"
    exit 1
  fi

  # Use awk to process the changelog
  # This is more reliable than bash string manipulation
  awk -v version="$version" -v release_date="$release_date" -v keep_unreleased="$keep_unreleased" '
    BEGIN {
      in_unreleased = 0
      unreleased_start = 0
    }
    /^## \[Unreleased\]/ {
      unreleased_start = NR
      in_unreleased = 1
      print "## [" version "] - " release_date
      next
    }
    in_unreleased == 1 && /^## \[/ {
      # Found next version section, end of unreleased
      in_unreleased = 0
      print
      next
    }
    {
      # Print all other lines
      print
    }
    END {
      if (keep_unreleased == "true" && unreleased_start > 0) {
        print ""
        print "## [Unreleased]"
      }
    }
  ' "$changelog" > "${changelog}.tmp" && mv "${changelog}.tmp" "$changelog"

  echo "Bumped changelog to version $version"
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
  bump-changelog-fixed)
    bump_changelog_fixed "$@"
    ;;
  commit-changelog)
    commit_changelog "$@"
    ;;
  *)
    echo "Usage: release.sh {determine-version|determine-version-and-branch|configure-git|bump-changelog-fixed|commit-changelog} [args...]"
    exit 1
    ;;
esac
