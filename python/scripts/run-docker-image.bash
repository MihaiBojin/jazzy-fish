#!/bin/bash
set -ueo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
readonly DIR

# shellcheck disable=SC1091
source "$DIR/functions.bash"

# Retrieve current git sha
TAG="$(get_image_tag)"
readonly TAG

# Load project name from project manifest
PROJECT_NAME="$(get_project_name)"
readonly PROJECT_NAME

# Run the image.
#
# Deliberately not --env-file .env: that file is what 'make setup' creates and
# what the publishing docs prime you to fill with PyPI tokens, and the entrypoint
# is a wordlist generator that needs none of them. Pass what the container
# actually needs with -e.
docker run \
    -it "$PROJECT_NAME:$TAG" \
    "$@"
