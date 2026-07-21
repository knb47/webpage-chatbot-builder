#!/bin/bash
# Fetch the chat-engine source and BUILD deployment_package.zip from it.
#
# The engine repo (chapp-skeleton) does not commit build artifacts; its
# scripts/build_lambda_zip.sh produces the zip inside Docker. This script:
#   1. locates the engine source — $CHAPP_SRC if set (local dev checkout),
#      otherwise a fresh shallow clone of the GitHub repo;
#   2. runs the engine's own build script;
#   3. copies the resulting zip next to this script, where
#      aws_utils/deploy_lambda.py expects it.
#
# Requirements: Docker (the build runs in a python:3.10 container).

set -e

GITHUB_REPO_URL="${CHAPP_REPO_URL:-https://github.com/knb47/chapp-skeleton.git}"
ZIP_FILE_NAME="deployment_package.zip"

SCRIPT_DIR=$(dirname "$(realpath "$0")")
DEPLOYMENT_DIRECTORY="$SCRIPT_DIR"

CLEANUP_CLONE=0
if [ -n "$CHAPP_SRC" ] && [ -d "$CHAPP_SRC" ]; then
    echo "Using local engine source: $CHAPP_SRC"
    ENGINE_DIR="$CHAPP_SRC"
else
    ENGINE_DIR="$DEPLOYMENT_DIRECTORY/chapp-skeleton"
    rm -rf "$ENGINE_DIR"
    echo "Cloning engine from $GITHUB_REPO_URL ..."
    git clone --depth 1 "$GITHUB_REPO_URL" "$ENGINE_DIR"
    CLEANUP_CLONE=1
fi

# Build the zip with the engine's own Dockerized build script.
bash "$ENGINE_DIR/scripts/build_lambda_zip.sh"

BUILT_ZIP="$ENGINE_DIR/aws_lambda/$ZIP_FILE_NAME"
if [ ! -f "$BUILT_ZIP" ]; then
    echo "Error: build did not produce $BUILT_ZIP"
    exit 1
fi

cp -f "$BUILT_ZIP" "$DEPLOYMENT_DIRECTORY/$ZIP_FILE_NAME"
echo "Engine package ready: $DEPLOYMENT_DIRECTORY/$ZIP_FILE_NAME"

if [ "$CLEANUP_CLONE" = "1" ]; then
    rm -rf "$ENGINE_DIR"
    echo "Removed temporary clone."
fi
