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

# Function to get a single tag at the current HEAD, for naming things.
# A commit can carry several tags; take the first so callers always get one line.
#
# Restricted to 'v*', which the listing this replaced was not: a release commit
# can carry tags that are not releases, and git orders them by refname, so an
# unfiltered list hands back the wrong one first.
#
# 'rt git::tags_at_head' is the same list with the 'v' left on, when every tag
# matters.
get_tag_at_head() {
    git tag --list 'v*' --points-at HEAD | sed 's/^v//' | head -n 1
}

# Extracts the project name as configured in 'pyproject.toml'
# '--no-project' keeps this usable before the environment has been synced.
get_project_name() {
    local dir
    dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
    uv run --no-project python -c "import tomllib; print(tomllib.load(open('$dir/../pyproject.toml','rb'))['project']['name'])"
}

# Extracts the project version as configured in 'pyproject.toml'
get_project_version() {
    local dir
    dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
    uv run --no-project python -c "import tomllib; print(tomllib.load(open('$dir/../pyproject.toml','rb'))['project']['version'])"
}

# Names the image: the tag at HEAD when the working directory is clean,
# otherwise the short SHA (with a -dirty suffix).
get_image_tag() {
    if [ -z "$(is_dirty)" ]; then
        local gittag
        gittag="$(get_tag_at_head)"
        if [ -n "$gittag" ]; then
            echo "$gittag"
            return
        fi
    fi
    get_git_sha
}
