"""
Helpers
=======

Various helper functions and jazzy_fish_tools configurations.
"""

from importlib import resources
import itertools
from pathlib import Path
import shutil
from typing import Iterable, List, Optional, Tuple


MIN_LENGTH: int = 4
MAX_LENGTH: int = 8
MAX_PREFIX_CHARS: int = 6
OUTPUT_PATH: str = "out"
DATABASE: str = f"{OUTPUT_PATH}/dictionary.duckdb"


# generate prefix combinations (MAX_CHARS, k) as the list of all possible prefix positions
# e.g., [0,1] will extract the first 2 letters of the word
# [0,2] will use the first and third letter
# etc.
def generate_all_prefix_combinations(of_length: int) -> List[Tuple[int, ...]]:
    # generate all combinations of prefixes of defined length
    elements: List[int] = list(range(0, MAX_PREFIX_CHARS))
    c = itertools.combinations(elements, of_length)
    return list(c)


def update_resource_lines(name: str, data: Iterable[str]) -> None:
    """Updates a resource file within a package."""
    data_path = str(resources.files(__package__).joinpath(name))

    with open(data_path, "w") as file:
        file.writelines(data)


def reset_location(location: Path, remove_dir=True):
    """Remove any previously generated files near the location"""

    if remove_dir:
        try:
            # Remove any existing databases
            shutil.rmtree(location)
        except FileNotFoundError:
            pass

    # Ensure the output location exists
    location.mkdir(parents=True, exist_ok=True)


def load_ignored_words() -> List[str]:
    """Loads the list of ignored words"""
    ignore_file = "resources/ignored.txt"
    ignore_notice = "resources/ignored_NOTICE.txt"

    words = [
        w.strip()
        for w in read_file(ignore_file, package_name=__package__)
        if not w.strip().startswith("#") and w.strip()
    ]

    # Ensure the ignore list is itself clean
    if len(set(words)) != len(words):
        words = sorted(list(set(words)))
        notice = read_file(ignore_notice, package_name=__package__)
        update_resource_lines(ignore_file, notice + [f"{w}\n" for w in words])
        print(f"Cleaned ignore list {ignore_file}, updated in place")

    return words


def is_letter(word):
    """Returns true if the word contains only a-zA-Z letters"""
    return all(char.isascii() and char.isalpha() for char in word.strip())


def read_lines(file_path: str) -> List[str]:
    """Read all lines from file"""

    with open(file_path, "r") as file:
        return file.readlines()


def read_file(from_path: str, package_name: Optional[str] = None) -> List[str]:
    """Reads words from a file that is either on disk or part of the specified package."""

    # If a package, retrieve path first
    data_path = from_path
    if package_name is not None:
        data_path = str(resources.files(package_name).joinpath(from_path))

    return read_lines(data_path)
