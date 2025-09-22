#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Install toml-cli if not already installed
if ! command -v toml > /dev/null; then
    echo "toml-cli not found, installing..."
    pip install toml-cli
fi

# Get the current version from pyproject.toml
current_version=$(toml get --toml-path pyproject.toml project.version)

# Split the version into major, minor, and patch
IFS='.' read -r major minor patch <<< "$current_version"

# Increment the patch version
new_patch=$((patch + 1))
new_version="$major.$minor.$new_patch"

echo "Bumping version from $current_version to $new_version"

# Update the version in pyproject.toml using toml-cli
toml set --toml-path pyproject.toml project.version "$new_version"

# Debug: Print pyproject.toml after update
echo "--- pyproject.toml content after version bump ---"
cat pyproject.toml
echo "--------------------------------------------------"

# Clean up old build artifacts and metadata
echo "Cleaning up old build artifacts and metadata..."
rm -rf dist/*
rm -rf build/*
rm -rf jsontoggle.egg-info/
rm -rf .mypy_cache/
rm -rf .ruff_cache/

echo "Building package with uv build..."
uv build

echo "Publishing package with uv publish..."
uv publish

echo "Successfully published version $new_version to PyPI."

