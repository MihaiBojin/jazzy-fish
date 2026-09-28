#!/bin/bash
set -ueo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
readonly DIR

# shellcheck disable=SC1091
source "$DIR/functions.bash"

# Load name and version from the project manifest
VERSION="$(get_project_version)"
readonly VERSION

PROJECT_NAME="$(get_project_name)"
readonly PROJECT_NAME

# Waits for an index to serve the version, then installs it once.
#
# A freshly uploaded release takes time to appear on the index that just accepted it, so
# something has to wait. 'rt net::await_url' backs off across about 7.75 minutes and
# returns as soon as the version is there, instead of a fixed sleep that either wastes
# time or fails a publish that worked.
#
# curl rather than a retried 'uv pip install', which is what this replaced: uv caches
# index responses, negative answers included, so a retried install re-reads the cached
# "no such version" in about 2ms and the whole ladder expires without asking the index
# again. '--refresh-package' on the install below is the other half of that, and it was
# missing here.
await_index() {
    rt net::await_url "$1/pypi/$PROJECT_NAME/$VERSION/json"
}

echo "Creating a virtual env..."
VENV="$(mktemp -d)/venv"
readonly VENV
# '--no-project' keeps the env detached from the working tree, so the check
# really does exercise the published artifact rather than the local source.
uv venv --no-project "$VENV"
# 'uv pip' targets this env instead of the project's .venv
export VIRTUAL_ENV="$VENV"

echo "Copying verification script..."
cp "$DIR"/../src/scripts/verify_install.py "$VENV/verify_install.py"

echo "Attempting to install version ($VERSION) in virtualenv ($VENV)..."
await_index "https://pypi.org"
uv pip install --refresh-package "$PROJECT_NAME" "${PROJECT_NAME}[cli]==$VERSION"

pushd "$VENV" >/dev/null 2>&1
"$VENV/bin/python" verify_install.py
popd >/dev/null 2>&1

echo "Virtualenv location: $VENV"
