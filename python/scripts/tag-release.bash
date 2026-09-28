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

# The version is read from the working copy, so an uncommitted bump would tag a
# commit that does not carry it. CI checkouts are clean; this catches the local run.
if rt git::is_dirty; then
    echo "Working directory is dirty, cannot proceed..." >&2
    git status --porcelain >&2
    exit 1
fi

VERSION="$(get_project_version)"
readonly VERSION
TAG="v$VERSION"
readonly TAG
REMOTE="$(rt git::remote)"
readonly REMOTE

# Ask the remote rather than the local clone: a CI checkout may not have
# fetched tags, and the remote is what decides whether the tag is taken.
#
# Exit 2 means the tag is absent. Network and permission failures stop the release.
set +e
git ls-remote --exit-code --tags "$REMOTE" "refs/tags/$TAG" >/dev/null
LS_REMOTE_STATUS=$?
set -e
readonly LS_REMOTE_STATUS
case "$LS_REMOTE_STATUS" in
0)
    echo "Tag $TAG already exists on $REMOTE; nothing to release." >&2
    exit 0
    ;;
2) ;; # The remote has no tag for this version.
*)
    echo "Could not ask $REMOTE about $TAG (git exited $LS_REMOTE_STATUS); refusing to tag." >&2
    exit 1
    ;;
esac

if [ -n "$DRY_RUN" ]; then
    echo "[dry-run] would tag HEAD ($(git rev-parse --short HEAD)) as $TAG" >&2
    echo "$TAG"
    exit 0
fi

rt git::release "$TAG" --push >&2

echo "$TAG"
