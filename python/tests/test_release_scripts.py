import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.fixture
def release_repo(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Release test")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "release@example.test")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Release test")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "release@example.test")
    monkeypatch.setenv("UV_PYTHON", sys.executable)
    repo = tmp_path / "repo"
    repo.mkdir()
    project = Path(__file__).resolve().parents[1]
    shutil.copytree(project / "scripts", repo / "scripts")
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "release-test"\nversion = "0.4.1"\n'
    )
    monkeypatch.chdir(repo)
    subprocess.run(["git", "init", "--quiet"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "Fixture"], check=True)
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "--quiet", str(remote)], check=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote)], check=True)
    return repo


def image_tag() -> str:
    return subprocess.run(
        [
            "bash",
            "-ueo",
            "pipefail",
            "-c",
            "source scripts/functions.bash; get_image_tag",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_image_tag_uses_highest_release_at_head(release_repo):
    for tag in ("v0.9.0", "v0.10.0", "v0.11.0", "unrelated"):
        subprocess.run(["git", "tag", tag], check=True)
    assert image_tag() == "0.11.0"


@pytest.mark.parametrize("tagged", [False, True])
def test_image_tag_marks_dirty_tree(release_repo, tagged):
    if tagged:
        subprocess.run(["git", "tag", "v0.4.1"], check=True)
    sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True)
    (release_repo / "untracked").touch()
    assert image_tag() == sha.strip() + "-dirty"


def test_image_tag_uses_sha_without_release_tag(release_repo):
    sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True)
    assert image_tag() == sha.strip()


def test_tag_release_dry_run_then_publish_then_noop(release_repo):
    preview = subprocess.run(
        ["scripts/tag-release.bash", "--dry-run"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert preview.stdout == "v0.4.1\n"
    assert subprocess.check_output(["git", "tag"], text=True) == ""
    published = subprocess.run(
        ["scripts/tag-release.bash"], capture_output=True, text=True, check=True
    )
    assert published.stdout == "v0.4.1\n"
    remote = subprocess.check_output(
        ["git", "ls-remote", "--tags", "origin", "refs/tags/v0.4.1^{}"], text=True
    )
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    assert remote.split()[0] == head
    repeated = subprocess.run(
        ["scripts/tag-release.bash"], capture_output=True, text=True, check=True
    )
    assert repeated.stdout == ""


@pytest.mark.parametrize("failure", ["dirty", "unreachable", "local-tag"])
def test_tag_release_refuses_without_publishing(release_repo, failure):
    if failure == "dirty":
        (release_repo / "untracked").touch()
    elif failure == "unreachable":
        subprocess.run(
            ["git", "remote", "set-url", "origin", "missing.git"], check=True
        )
    else:
        subprocess.run(["git", "tag", "v0.4.1"], check=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "--quiet", "-m", "Next commit"],
            check=True,
        )
    result = subprocess.run(
        ["scripts/tag-release.bash"], capture_output=True, text=True
    )
    assert result.returncode != 0
    assert result.stdout == ""
    assert (
        subprocess.check_output(
            ["git", "--git-dir", str(release_repo.parent / "remote.git"), "tag"],
            text=True,
        )
        == ""
    )


def test_tag_release_checks_the_configured_remote(release_repo):
    subprocess.run(["git", "remote", "rename", "origin", "upstream"], check=True)
    subprocess.run(["git", "remote", "add", "origin", "missing.git"], check=True)
    subprocess.run(["git", "config", "checkout.defaultRemote", "upstream"], check=True)
    for expected in ("v0.4.1\n", ""):
        result = subprocess.run(
            ["scripts/tag-release.bash"], capture_output=True, text=True, check=True
        )
        assert result.stdout == expected
