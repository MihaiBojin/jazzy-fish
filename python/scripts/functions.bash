#!/bin/bash

# Function to check if the working directory is dirty
is_dirty() {
    if [ -n "$(git status --porcelain)" ]; then
        echo "-dirty"
    else
        echo ""
    fi
}

# Function to get the current Git short SHA
get_git_sha() {
    # Get the current Git short SHA
    GIT_SHA=$(git rev-parse --short HEAD)

    echo "${GIT_SHA}$(is_dirty)"
}

# Function to list every tag pointing at the current HEAD, 'v' prefix removed,
# one per line. '--points-at' rather than '--contains': the latter lists every
# tag whose history includes HEAD, so checking out an older release returned
# that tag plus all later ones.
get_tags_at_head() {
    git tag --points-at HEAD | sed 's/^v//'
}

# Function to get a single tag at the current HEAD, for naming things.
# A commit can carry several tags; take the first so callers always get one
# line. Use get_tags_at_head when every tag matters.
get_tag_at_head() {
    get_tags_at_head | head -n 1
}

# Extracts the project name as configured in 'pyproject.toml'
# '--no-project' keeps this usable before the environment has been synced.
get_project_name() {
    dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
    uv run --no-project python -c "import tomllib; print(tomllib.load(open('$dir/../pyproject.toml','rb'))['project']['name'])"
}

# Extracts the project version as configured in 'pyproject.toml'
get_project_version() {
    dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
    uv run --no-project python -c "import tomllib; print(tomllib.load(open('$dir/../pyproject.toml','rb'))['project']['version'])"
}
