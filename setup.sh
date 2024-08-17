#!/bin/bash

# Colors for formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Welcome to the Tux Discord Bot Setup Script${NC}"

# Check for prerequisites
echo -e "${YELLOW}Checking for prerequisites...${NC}"

check_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo >&2 "${RED}$1 is required but not installed. Aborting.${NC}"
    exit 1
  }

  echo -e "${GREEN}$1 is installed.${NC}"
}

check_command git
check_command python3.12
check_command poetry

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
poetry install || {
  echo >&2 "${RED}Failed to install dependencies. Aborting.${NC}"
  exit 1
}

# Activate the virtual environment
echo -e "${YELLOW}Activating the virtual environment...${NC}"
poetry shell || {
  echo >&2 "${RED}Failed to activate virtual environment. Aborting.${NC}"
  exit 1
}

# Install pre-commit hooks
echo -e "${YELLOW}Installing pre-commit hooks...${NC}"
pre-commit install || {
  echo >&2 "${RED}Failed to install pre-commit hooks. Aborting.${NC}"
  exit 1
}

# Generate the Prisma client
echo -e "${YELLOW}Generating the Prisma client...${NC}"
prisma generate || {
  echo >&2 "${RED}Failed to generate Prisma client. Aborting.${NC}"
  exit 1
}

# Copy and configure .env file
echo -e "${YELLOW}Configuring environment variables...${NC}"
cp .env.example .env
echo -e "${GREEN}.env file created. Please fill in the required values.${NC}"

# Copy and configure settings.json file
echo -e "${YELLOW}Configuring settings.json...${NC}"
cp config/settings.json.example config/settings.json
echo -e "${GREEN}settings.json file created. Please fill in the required values.${NC}"

# Prompt the user for the development prefix and Discord ID
read -rp "Enter the desired development prefix (default: ~): " dev_prefix
dev_prefix=${dev_prefix:-~}
read -rp "Enter your Discord ID: " discord_id

# Update settings.json with the provided values using sed
sed -i "s/\"DEV\": \"[^\"]*\"/\"DEV\": \"$dev_prefix\"/" config/settings.json
sed -i "s/\"BOT_OWNER\": [0-9]*/\"BOT_OWNER\": $discord_id/" config/settings.json

echo -e "${GREEN}Setup completed successfully!${NC}"
