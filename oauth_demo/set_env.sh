#!/bin/bash

# This script exports variables from a .env file into the current shell session.
# It is intended for local development.
#
# USAGE:
# source set_env.sh

if [ -f .env ]; then
  # Read the .env file, filter out comments and empty lines, and export the variables.
  export $(grep -vE '^#|^$' .env | xargs)
  echo "Environment variables from .env have been exported to your local shell."
else
  echo "Error: .env file not found in the current directory."
fi
