#!/bin/bash
set -ueo pipefail

# Tags HEAD with the version in pyproject.toml, unless that tag already exists.
#
# Run on every push to main: pushes that do not change the version find their
# tag already present and do nothing, so only a merged version bump creates a
# release.
#
# Writes the created tag to stdout and nothing at all when there was nothing to
# do, so a caller can branch on it. All commentary goes to stderr.
#
# Pass --dry-run to skip creating and pushing the tag.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
readonly DIR

# shellcheck disable=SC1091
source "$DIR/functions.bash"

DRY_RUN=""
while [[ "$#" -gt 0 ]]; do
    case $1 in
    --dry-run)
        DRY_RUN="yes"
        ;;
    *)
        echo "Error: unsupported argument $1" >&2
        exit 1
        ;;
    esac
    shift
done
readonly DRY_RUN

VERSION="$(get_project_version)"
readonly VERSION
TAG="v$VERSION"
readonly TAG

# Ask the remote rather than the local clone: a CI checkout may not have
# fetched tags, and the remote is what decides whether the tag is taken.
if git ls-remote --exit-code --tags origin "refs/tags/$TAG" >/dev/null 2>&1; then
    echo "Tag $TAG already exists on origin; nothing to release." >&2
    exit 0
fi

if [ -n "$DRY_RUN" ]; then
    echo "[dry-run] would tag HEAD ($(git rev-parse --short HEAD)) as $TAG" >&2
    echo "$TAG"
    exit 0
fi

echo "Tagging HEAD ($(git rev-parse --short HEAD)) as $TAG..." >&2
git tag -a "$TAG" -m "Release $VERSION"
git push origin "$TAG" >&2

echo "$TAG"
