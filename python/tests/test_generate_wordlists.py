import hashlib
import os
from pathlib import Path
import subprocess
import sys

import pytest

from jazzy_fish_tools.generate_wordlists import _save_stats, _select_words


@pytest.fixture
def dictionary(tmp_path: Path) -> Path:
    directory = tmp_path / "dictionary"
    directory.mkdir()
    (directory / "notes").mkdir()
    words = {
        "verb": ["wxyzabcd", "efghijkl"],
        "noun": ["opqrstuv", "ghijklmn", "aaaaaa", "aaaa"],
        "adverb": ["yzabcdef", "qrstuvwx", "abcdefgh"],
        "adjective": [
            "ijklmnop",
            "abcdefgh",
            "aaaacccc",
            "aaaabbbb",
            "aaaabbbb",
            "aaaa",
            "",
            "abc",
            "abcdefghi",
            "can't",
            "élans",
            "anal",
        ],
    }
    for part, entries in words.items():
        (directory / f"{part}.txt").write_text(
            "\n".join(entries) + "\n", encoding="utf-8"
        )
    return directory


@pytest.mark.parametrize(
    "sequential,file_count,digest",
    [
        (
            False,
            456,
            "9dc89829535161fca862edaf96fa205959f057faf12fb9adad7543510a9ec449",
        ),
        (True, 40, "68281648148d77ad76263e4f87d127a06728ffc2b69a5c7dc386b5172371b3d3"),
    ],
)
def test_generated_files_match_duckdb_without_installed_dependencies(
    dictionary: Path, tmp_path: Path, sequential: bool, file_count: int, digest: str
) -> None:
    source = Path(__file__).resolve().parents[1] / "src"
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "-c",
            "from jazzy_fish_tools import generate_wordlists as g; "
            f"g.ONLY_SEQ_PREFIXES = {sequential}; g.main()",
            str(dictionary),
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(source)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "out/dictionary.duckdb").exists()

    output = tmp_path / "out/processed"
    files = sorted(path for path in output.rglob("*") if path.is_file())
    assert len(files) == file_count

    # Captured from b73013f's DuckDB generator. The digest covers filenames,
    # wordlists, checksums, statistics, and all seeded sample phrases.
    actual = hashlib.sha256()
    for path in files:
        actual.update(
            path.relative_to(output).as_posix().encode()
            + b"\0"
            + path.read_text(encoding="utf-8").encode()
            + b"\0"
        )
    assert actual.hexdigest() == digest

    selected = output / "01_e672eed"
    assert (selected / "adjective.txt").read_text() == "aaaabbbb\nabcdefgh\nijklmnop"
    assert (selected / "adverb.txt").read_text() == "qrstuvwx\nyzabcdef"
    assert (selected / "noun.txt").read_text() == "aaaaaa\nghijklmn\nopqrstuv"
    assert (selected / "verb.txt").read_text() == "efghijkl\nwxyzabcd"


@pytest.mark.parametrize(
    "words,positions,expected",
    [
        ([], (0, 1), []),
        (["noon", "apple", "abacus"], (0, 5), ["abacus"]),
        (["abuse", "abandon", "abacus"], (0, 2), ["abacus", "abuse"]),
        (["abacus", "ABACUS"], (0, 2), ["ABACUS", "abacus"]),
    ],
)
def test_selected_words_respect_positions_and_order(
    words: list[str], positions: tuple[int, ...], expected: list[str]
) -> None:
    assert _select_words(words, positions) == expected


def test_large_capacity_preserves_statistics_rounding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    output = tmp_path / "out/processed/012345"
    output.mkdir(parents=True)
    parts = ["adverb", "adjective", "verb", "noun"]
    files = []
    for part, prefix in zip(parts, ("aa", "bb", "cc", "dd")):
        words = [
            prefix
            + "".join(chr(97 + (index // 26**digit) % 26) for digit in (3, 2, 1, 0))
            for index in range(10_001)
        ]
        path = output / f"{part}.txt"
        path.write_text("\n".join(words), encoding="utf-8")
        files.append(str(path))

    _save_stats(dict.fromkeys(parts, 10_001), "012345", True, parts, files)

    total_line = next(
        line
        for line in (output / "stats_4.txt").read_text().splitlines()
        if line.startswith("Total")
    )
    # DuckDB 1.5.5's PRODUCT returns DOUBLE, including this rounded total.
    assert total_line.split() == ["Total", "10,004,000,600,040,000"]
