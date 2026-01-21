#!/usr/bin/env bash
# Local Docker build script for Tux
# Builds Docker image with version baked in from git tags or manual override
#
# Usage:
#   ./scripts/docker-build.sh                    # Auto-detect version from git
#   ./scripts/docker-build.sh 1.2.3              # Use specific version
#   ./scripts/docker-build.sh --target dev       # Build dev target
#   ./scripts/docker-build.sh --tag my-tag       # Custom image tag

set -euo pipefail

# Default values
TARGET="production"
IMAGE_TAG="tux:latest"
VERSION=""
GIT_SHA=""
BUILD_DATE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --target)
      TARGET="$2"
      shift 2
      ;;
    --tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    --version)
      VERSION="$2"
      shift 2
      ;;
    --help|-h)
      cat << EOF
Local Docker build script for Tux

Usage:
  $0 [OPTIONS] [VERSION]

Arguments:
  VERSION              Version to bake into image (default: auto-detect from git)

Options:
  --target TARGET      Docker build target (default: production)
                       Options: production, dev
  --tag TAG           Docker image tag (default: tux:latest)
  --version VERSION    Explicit version (overrides auto-detection)
  --help, -h          Show this help message

Examples:
  $0                                    # Auto-detect version from git
  $0 1.2.3                              # Use version 1.2.3
  $0 --target dev --tag tux:dev        # Build dev target with custom tag
  $0 --version \$(git describe --tags)  # Use git describe output

Version Detection Priority:
  1. --version flag or VERSION argument
  2. git describe --tags --always (removes 'v' prefix)
  3. git rev-parse --short HEAD (short commit SHA)
  4. "dev" (fallback)

EOF
      exit 0
      ;;
    -*)
      echo "Error: Unknown option $1" >&2
      echo "Use --help for usage information" >&2
      exit 1
      ;;
    *)
      if [ -z "$VERSION" ]; then
        VERSION="$1"
      else
        echo "Error: Multiple version arguments provided" >&2
        exit 1
      fi
      shift
      ;;
  esac
done

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Function to detect version from git
detect_version() {
  local version=""

  # Try git describe first (tags)
  if command -v git >/dev/null 2>&1 && [ -d .git ]; then
    if git describe --tags --exact-match >/dev/null 2>&1; then
      # Exact tag match
      version=$(git describe --tags --exact-match 2>/dev/null | sed 's/^v//')
    elif git describe --tags >/dev/null 2>&1; then
      # Nearest tag
      version=$(git describe --tags 2>/dev/null | sed 's/^v//')
    elif git rev-parse --short HEAD >/dev/null 2>&1; then
      # Fallback to short commit SHA
      version="dev-$(git rev-parse --short HEAD 2>/dev/null)"
    fi
  fi

  # Final fallback
  echo "${version:-dev}"
}

# Function to get git SHA
get_git_sha() {
  if command -v git >/dev/null 2>&1 && [ -d .git ]; then
    git rev-parse HEAD 2>/dev/null || echo ""
  else
    echo ""
  fi
}

# Function to generate build date
get_build_date() {
  date -u +'%Y-%m-%dT%H:%M:%SZ'
}

# Detect version if not provided
if [ -z "$VERSION" ]; then
  echo "Detecting version from git..."
  VERSION=$(detect_version)
fi

# Get git SHA
GIT_SHA=$(get_git_sha)

# Get build date
BUILD_DATE=$(get_build_date)

# Validate version
if [ -z "$VERSION" ]; then
  echo "Error: Could not determine version" >&2
  exit 1
fi

# Display build information
echo "Building Tux Docker Image"
echo "Version:     $VERSION"
echo "Target:      $TARGET"
echo "Tag:         $IMAGE_TAG"
if [ -n "$GIT_SHA" ]; then
  echo "Git SHA:     ${GIT_SHA:0:7}"
fi
echo "Build Date:  $BUILD_DATE"
echo ""

# Build the image
echo "Building Docker image..."
docker build \
  --target "$TARGET" \
  --tag "$IMAGE_TAG" \
  --build-arg VERSION="$VERSION" \
  --build-arg GIT_SHA="$GIT_SHA" \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  --file Containerfile \
  .

# Verify version was baked in
echo ""
echo "Verifying version in image..."
IMAGE_VERSION=$(docker run --rm "$IMAGE_TAG" cat /app/VERSION 2>/dev/null || echo "")
if [ -n "$IMAGE_VERSION" ]; then
  if [ "$IMAGE_VERSION" = "$VERSION" ]; then
    echo "Version verified: $IMAGE_VERSION"
  else
    echo "Warning: Version mismatch: expected '$VERSION', found '$IMAGE_VERSION'"
  fi
else
  echo "Warning: Could not read version from image"
fi

echo ""
echo "Build complete!"
echo "Image: $IMAGE_TAG"
echo ""
echo "To run with Docker Compose:"
echo "  TUX_IMAGE=${IMAGE_TAG%%:*} TUX_IMAGE_TAG=${IMAGE_TAG##*:} docker compose --profile production up -d"
echo ""
echo "To run directly:"
echo "  docker run --rm $IMAGE_TAG"
