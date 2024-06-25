#!/bin/bash

# Check if the description argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <description>"
  exit 1
fi

# Get the description from the first argument
description=$1

# Define the timestamp format
timestamp=$(date +"%Y%m%d%H%M%S")

# Combine timestamp and description
dir_name="${timestamp}_${description}"

# Create the directory
mkdir -p "../prisma/migrations/${dir_name}"

# Navigate to the directory
cd "../prisma/migrations/${dir_name}"

# Create an empty migration.sql file
touch migration.sql

echo "Migration directory created: ../prisma/migrations/${dir_name}"
