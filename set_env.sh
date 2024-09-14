#!/bin/bash

# Function to print usage instructions
usage() {
  echo "Usage: $0 {dev|prod}"
  exit 1
}

# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
  usage
fi

# Set the environment based on the argument
TUX_ENV=$1

# Determine which .env file to source
if [ "$TUX_ENV" == "prod" ]; then
  ENV_FILE=".env.prod"
elif [ "$TUX_ENV" == "dev" ]; then
  ENV_FILE=".env.dev"
else
  usage
fi

# Check if the environment file exists
if [ ! -f "$ENV_FILE" ]; then
  echo "Environment file $ENV_FILE does not exist!"
  exit 1
fi

# Backup existing .env file if it exists
if [ -f ".env" ]; then
  cp .env .env.bak
  echo "Existing .env file backed up to .env.bak"
fi

# Function to add or replace environment variables in the .env file
add_or_replace_var() {
  local var_name
  var_name=$(echo "$1" | cut -d '=' -f 1)
  local var_value
  var_value=$(echo "$1" | cut -d '=' -f 2-)

  # Escape special characters except for '/'
  var_value=${var_value//&/\\&}

  # Properly quote the value if not already quoted
  if [[ $var_value != \"*\" ]]; then
    var_value="\"$var_value\""
  fi

  # If the variable already exists, replace it
  if grep -q "^$var_name=" .env; then
    sed -i "s|^$var_name=.*|$var_name=$var_value|" .env
  else
    echo "$var_name=$var_value" >>.env
  fi
}

# Set the environment at the top
add_or_replace_var "TUX_ENV=$TUX_ENV"

# Parse the environment file and export variables
while IFS= read -r line; do
  # Ignore comments and empty lines
  if [[ ! "$line" =~ ^# && "$line" =~ .*=.* ]]; then
    # Export the variable
    eval "export $line"
    add_or_replace_var "$line"
  fi
done <"$ENV_FILE"

# Optionally: Export additional dynamically computed variables
DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:${POSTGRES_PORT}/${POSTGRES_DB}"

add_or_replace_var "DATABASE_URL=$DATABASE_URL"

# Print the environment variables for verification
echo "Environment ($TUX_ENV) variables updated in .env file:"
cat .env
