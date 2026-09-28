#!/bin/bash

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

# A dirty tree uses its SHA; a clean tree uses its highest release or SHA.
get_image_tag() {
    if rt git::is_dirty; then
        rt git::head_sha
    else
        local version
        version="$(rt git::version_or_sha)" || return
        echo "${version#v}"
    fi
}
