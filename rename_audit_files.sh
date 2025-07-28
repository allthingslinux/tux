#!/bin/bash

# Navigate to audit directory and rename files with sequential prefixes
# based on creation time (oldest = 01_, newest = highest number)

counter=1
ls -tr audit/*.md audit/*.py audit/*.yml audit/*.json 2>/dev/null | while read file; do
    if [ -f "$file" ]; then
        dir=$(dirname "$file")
        basename=$(basename "$file")

        # Create new name with zero-padded counter
        new_name=$(printf "%02d_%s" $counter "$basename")

        echo "Renaming: $basename -> $new_name"
        mv "$file" "$dir/$new_name"

        counter=$((counter + 1))
    fi
done
