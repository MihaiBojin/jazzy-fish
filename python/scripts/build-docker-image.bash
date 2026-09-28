#!/bin/bash
set -ueo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
readonly DIR

# shellcheck disable=SC1091
source "$DIR/functions.bash"

# The image tag only names the image; the package version comes from
# pyproject.toml during the build, so nothing here rewrites it.
TAG="$(get_image_tag)"
readonly TAG

# Load project name from project manifest
PROJECT_NAME="$(get_project_name)"
readonly PROJECT_NAME

# Build the image
echo "Building $PROJECT_NAME:$TAG..."
docker build \
    -t "$PROJECT_NAME:$TAG" \
    "$DIR/.."
