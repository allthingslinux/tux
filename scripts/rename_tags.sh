#!/bin/bash

# Script to rename git tags to proper semver format
# Changes v0.1.0rc1 -> v0.1.0-rc.1

echo "Renaming git tags to proper semver format..."

# Map of old tags to new tags
declare -A tag_mapping=(
    ["v0.1.0rc1"]="v0.1.0-rc.1"
    ["v0.1.0rc2"]="v0.1.0-rc.2"
    ["v0.1.0rc3"]="v0.1.0-rc.3"
    ["v0.1.0rc4"]="v0.1.0-rc.4"
)

# Process each tag
for old_tag in "${!tag_mapping[@]}"; do
    new_tag="${tag_mapping[$old_tag]}"

    echo "Processing: $old_tag -> $new_tag"

    # Check if old tag exists
    if git rev-parse "$old_tag" >/dev/null 2>&1; then
        # Get the commit hash for the old tag
        commit_hash=$(git rev-parse "$old_tag")

        # Create new tag with proper semver format
        git tag "$new_tag" "$commit_hash"

        # Delete the old tag (local only)
        git tag -d "$old_tag"

        echo "  ✓ Renamed $old_tag -> $new_tag"
    else
        echo "  ⚠ Tag $old_tag not found, skipping"
    fi
done

echo ""
echo "Tag renaming complete!"
echo ""
echo "To push the changes to remote:"
echo "  git push origin --tags --force"
echo "  git push origin --delete v0.1.0rc1 v0.1.0rc2 v0.1.0rc3 v0.1.0rc4"
echo ""
echo "Note: Use --force carefully as it rewrites history!"
