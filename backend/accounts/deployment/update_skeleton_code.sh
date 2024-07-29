#!/bin/bash

# Static arguments
GITHUB_REPO_URL="https://github.com/knb47/chapp-skeleton.git"
SCRIPT_DIR=$(dirname "$0")
DESTINATION_DIRECTORY="$SCRIPT_DIR/app_skeleton_code"

# Check if the destination directory exists
if [ -d "$DESTINATION_DIRECTORY" ]; then
    echo "Directory $DESTINATION_DIRECTORY exists. Pulling updates..."
    cd "$DESTINATION_DIRECTORY"
    git pull
else
    # Clone the GitHub repository to the specified directory
    echo "Cloning repository from $GITHUB_REPO_URL to $DESTINATION_DIRECTORY..."
    git clone $GITHUB_REPO_URL $DESTINATION_DIRECTORY

    # Check if the clone operation was successful
    if [ $? -eq 0 ]; then
        echo "Repository successfully cloned to $DESTINATION_DIRECTORY."
    else
        echo "Failed to clone repository."
        exit 1
    fi
fi