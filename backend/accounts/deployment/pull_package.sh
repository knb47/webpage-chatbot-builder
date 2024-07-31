#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Replace this URL with the correct one for your repo
GITHUB_REPO_URL="https://github.com/knb47/chapp-skeleton.git"
REPO_NAME="chapp-skeleton"
ZIP_FILE_NAME="deployment_package.zip"
SUBDIR="aws_lambda"

SCRIPT_DIR=$(dirname "$(realpath "$0")")
DEPLOYMENT_DIRECTORY="$SCRIPT_DIR"

echo "Script directory: $SCRIPT_DIR"
echo "Deployment directory: $DEPLOYMENT_DIRECTORY"

# Remove any existing deployment_package.zip
if [ -f "$DEPLOYMENT_DIRECTORY/$ZIP_FILE_NAME" ]; then
    echo "Removing existing $ZIP_FILE_NAME..."
    rm "$DEPLOYMENT_DIRECTORY/$ZIP_FILE_NAME"
fi

# Remove any existing chapp-skeleton directory
if [ -d "$DEPLOYMENT_DIRECTORY/$REPO_NAME" ]; then
    echo "Removing existing $REPO_NAME directory..."
    rm -rf "$DEPLOYMENT_DIRECTORY/$REPO_NAME"
fi

# Clone the repository with Git LFS
echo "Cloning repository from $GITHUB_REPO_URL..."
CLONE_DIR="$DEPLOYMENT_DIRECTORY/$REPO_NAME"

if git clone "$GITHUB_REPO_URL" "$CLONE_DIR"; then
    echo "Repository cloned to $CLONE_DIR"

    cd "$CLONE_DIR"

    # Ensure Git LFS is installed and initialized
    git lfs install
    git lfs pull

    # Find the .zip file in the aws_lambda subdirectory of the cloned directory
    ZIP_FILE_PATH="$CLONE_DIR/$SUBDIR/$ZIP_FILE_NAME"

    if [ -f "$ZIP_FILE_PATH" ]; then
        echo "Found $ZIP_FILE_NAME at $ZIP_FILE_PATH"

        # Move the .zip file to the deployment directory
        mv "$ZIP_FILE_PATH" "$DEPLOYMENT_DIRECTORY"
        echo "$ZIP_FILE_NAME moved to $DEPLOYMENT_DIRECTORY"

        # Verify the ZIP file integrity
        OUTPUT_FILE="$DEPLOYMENT_DIRECTORY/$ZIP_FILE_NAME"
        if unzip -t "$OUTPUT_FILE" > /dev/null; then
            echo "ZIP file integrity verified."
        else
            echo "Error: The ZIP file is corrupted or invalid."
            exit 1
        fi

        # Clean up by deleting the cloned repository
        cd ..
        rm -rf "$CLONE_DIR"
        echo "Cloned repository deleted."
    else
        echo "Error: $ZIP_FILE_NAME not found in the cloned repository."
        exit 1
    fi
else
    echo "Error: Failed to clone the repository."
    exit 1
fi