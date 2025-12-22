#!/usr/bin/env bash
# Release workflow helper scripts
# Usage: release.sh <command> [args...]

set -euo pipefail

# shellcheck disable=SC2034
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Trim leading and trailing whitespace from a string
trim_whitespace() {
  local str="${1}"
  str="${str#"${str%%[![:space:]]*}"}"  # trim leading whitespace
  str="${str%"${str##*[![:space:]]}"}"  # trim trailing whitespace
  echo -n "$str"
}

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
  default_branch="$(trim_whitespace "$default_branch")"

  if [ -z "$default_branch" ]; then
    # Try common branch names
    if git show-ref --verify --quiet refs/remotes/origin/main; then
      default_branch="main"
    elif git show-ref --verify --quiet refs/remotes/origin/master; then
      default_branch="master"
    else
      # Fallback: use the first branch we find
      default_branch=$(git branch -r | grep -v HEAD | head -n1 | sed 's/origin\///' | xargs)
      default_branch="$(trim_whitespace "$default_branch")"
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
  # Trim whitespace from parameters
  local version
  version="$(trim_whitespace "${1}")"
  local changelog
  changelog="$(trim_whitespace "${2:-CHANGELOG.md}")"
  local keep_unreleased
  keep_unreleased="$(trim_whitespace "${3:-false}")"

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
  # Keep-a-Changelog format requires:
  # 1. Header (before first ##)
  # 2. ## [Unreleased] (must be first and unique release section)
  # 3. Other version sections
  # 4. Link definitions (must be last)
  awk -v version="$version" -v release_date="$release_date" -v keep_unreleased="$keep_unreleased" '
    BEGIN {
      in_unreleased = 0
      in_links = 0
      header = ""
      new_version_header = ""
      old_version_sections = ""
      links_section = ""
      found_unreleased = 0
      unreleased_content = ""
      in_header = 1
    }
    /^\[.*\]:/ {
      # Start of link definitions section - everything after this is links
      in_links = 1
      in_header = 0
      links_section = links_section $0 "\n"
      next
    }
    in_links == 1 {
      # Collect all link definition lines (including empty lines between them)
      links_section = links_section $0 "\n"
      next
    }
    /^## \[Unreleased\]/ {
      found_unreleased = 1
      in_unreleased = 1
      in_header = 0
      # Store new version header separately (will be output before its content)
      new_version_header = "## [" version "] - " release_date "\n"
      next
    }
    in_unreleased == 1 {
      if (/^## \[/) {
        # Found next version section, end of unreleased
        in_unreleased = 0
        old_version_sections = old_version_sections $0 "\n"
        next
      } else if (/^\[.*\]:/) {
        # Found link definitions, end of unreleased (links come after sections)
        in_unreleased = 0
        in_links = 1
        links_section = links_section $0 "\n"
        next
      } else {
        # Collect unreleased content (will go under new version)
        unreleased_content = unreleased_content $0 "\n"
        next
      }
    }
    /^## \[/ {
      # Other version sections (old versions)
      in_header = 0
      old_version_sections = old_version_sections $0 "\n"
      next
    }
    {
      if (in_header == 1) {
        # Header content (before first ## section)
        header = header $0 "\n"
      } else {
        # Content within version sections (goes to old_version_sections)
        old_version_sections = old_version_sections $0 "\n"
      }
    }
    END {
      # Output header first
      printf "%s", header

      # Add new Unreleased section if requested (must be first release section, right after header)
      if (keep_unreleased == "true" && found_unreleased) {
        printf "## [Unreleased]\n\n"
      }

      # Output new version header, then its content, then old version sections
      if (found_unreleased) {
        printf "%s", new_version_header
        printf "%s", unreleased_content
      }
      printf "%s", old_version_sections

      # Output link definitions last (they must be at the end)
      printf "%s", links_section
    }
  ' "$changelog" > "${changelog}.tmp" && mv "${changelog}.tmp" "$changelog"

  # Update link definitions - add new version link and update Unreleased link
  local repo="${GITHUB_REPOSITORY:-allthingslinux/tux}"
  local tag_prefix="v"

  # Find the previous version from the last released version link (skip [Unreleased])
  # We want the "to" version from the last released version link
  # Example: [0.1.0-rc.4]: ...compare/v0.1.0-rc.3...v0.1.0-rc.4 -> extract "v0.1.0-rc.4"
  # This is more reliable than using [Unreleased] link
  local previous_version
  # Get all version links with compare URLs, skip [Unreleased], get the first one (which is the latest release)
  previous_version=$(grep -E "^\[[0-9]+\.[0-9]+\.[0-9]+.*\]:.*compare.*\.\.\." "$changelog" | head -1 | sed -E 's/.*\.\.\.(v?[0-9]+\.[0-9]+\.[0-9]+.*)/\1/' | sed 's/^v//' || echo "")

  # If that didn't work, fall back to extracting from [Unreleased] link (the "from" version)
  if [[ -z "$previous_version" ]]; then
    previous_version=$(grep -E "^\[Unreleased\]:.*compare.*\.\.\." "$changelog" | head -1 | sed -E 's/.*compare\/(.*)\.\.\..*/\1/' | sed 's/^v//' || echo "")
  fi

  # If still empty, we have a problem - don't use 0.0.0 as it's a special marker
  if [[ -z "$previous_version" ]]; then
    echo "Error: Could not determine previous version from changelog links"
    exit 1
  fi

  # Update Unreleased link to point from new version
  if grep -q "^\[Unreleased\]: " "$changelog"; then
    sed -i "s|^\[Unreleased\]:.*|\[Unreleased\]: https://github.com/${repo}/compare/${tag_prefix}${version}...HEAD|" "$changelog"
  fi

  # Add new version link if it doesn't exist (insert after Unreleased link)
  if ! grep -q "^\[${version}\]: " "$changelog"; then
    if grep -q "^\[Unreleased\]: " "$changelog"; then
      # Insert after Unreleased link
      sed -i "/^\[Unreleased\]: /a\[${version}\]: https://github.com/${repo}/compare/${tag_prefix}${previous_version}...${tag_prefix}${version}" "$changelog"
    else
      # Add at the beginning of links section
      sed -i "/^\[.*\]:/i\[${version}\]: https://github.com/${repo}/compare/${tag_prefix}${previous_version}...${tag_prefix}${version}" "$changelog"
    fi
  fi

  echo "Bumped changelog to version $version"
}

# Commit updated changelog
# Creates a branch and PR if main is protected, otherwise pushes directly
commit_changelog() {
  # Trim whitespace from parameters
  local version
  version="$(trim_whitespace "${1}")"
  local branch
  branch="$(trim_whitespace "${2}")"

  if [ -z "$(git status --porcelain CHANGELOG.md)" ]; then
    echo "No changes to CHANGELOG.md"
    return 0
  fi

  git add CHANGELOG.md
  git commit -m "chore: bump changelog to $version"

  # Try to push directly first
  local push_output
  push_output=$(git push origin "$branch" 2>&1) || true

  if echo "$push_output" | grep -q "protected branch\|GH006"; then
    echo "Branch $branch is protected, creating PR instead..."

    # Create a release branch
    local release_branch="chore/release-${version#v}"
    git checkout -b "$release_branch" || git checkout "$release_branch"
    git push origin "$release_branch" || true

    # Create PR using GitHub API
    local repo="${GITHUB_REPOSITORY:-}"
    if [ -n "$repo" ] && [ -n "${GITHUB_TOKEN:-}" ]; then
      local pr_response
      pr_response=$(curl -s -X POST \
        -H "Authorization: token ${GITHUB_TOKEN}" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/${repo}/pulls" \
        -d "{
          \"title\": \"chore: bump changelog to $version\",
          \"head\": \"$release_branch\",
          \"base\": \"$branch\",
          \"body\": \"Automated changelog update for release $version\\n\\nThis PR updates the changelog after creating release $version.\"
        }" 2>&1) || true

      if echo "$pr_response" | grep -q '"number"'; then
        local pr_number
        pr_number=$(echo "$pr_response" | grep '"number"' | head -1 | sed 's/.*"number": *\([0-9]*\).*/\1/')
        echo "Created PR #${pr_number}: https://github.com/${repo}/pull/${pr_number}"
      else
        echo "Failed to create PR via API. Response: $pr_response"
        echo "Please create PR manually: $release_branch -> $branch"
      fi
    else
      echo "GitHub API credentials not available. Please create PR manually:"
      echo "  Branch: $release_branch -> $branch"
      echo "  Title: chore: bump changelog to $version"
    fi
  else
    echo "Successfully pushed changelog update to $branch"
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
