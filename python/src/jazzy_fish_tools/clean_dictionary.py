"""
Clean Dictionary
==============

Given a dictionary as an input directory, clean every list of word parts by removing invalid, non ASCII, non alpha words,
and inappropriate words (as defined by the `ignored.txt` list).

"""

import argparse
from pathlib import Path
import shutil
import time
from typing import List, Optional, Set
from jazzy_fish_tools import helpers


def _clean(file: Path, ignored: Optional[Set[str]] = None) -> List[str]:
    """Cleans the specified file by removing non-alpha characters and excluding any words specified as ignored"""

    ignored = ignored if ignored is not None else set()

    # Read all words from the input file
    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # Remove words that contain non-alpha characters
    lines = list(filter(helpers.is_letter, lines))
    # Convert all words to lowercase
    lines = list(map(lambda w: w.lower(), lines))
    # Remove ignored words
    lines = list(filter(lambda w: w.strip() not in ignored, lines))
    # Ensure deterministic behavior later down the line
    lines.sort()

    return lines


def clean_dictionary(dictionary_dir: str, backup_original: bool = False) -> None:
    """Process all word parts found in the specified dictionary"""

    # Load ignores
    ignored: Set[str] = set()
    ignored.update(helpers.load_ignored_words())

    # Find all files containing list of words, in the directory
    directory = Path(dictionary_dir)
    files = [f for f in directory.iterdir() if f.is_file()]

    # Process all files
    for file in files:
        # clean the file
        lines = _clean(file, ignored)

        # make a backup of the original file, if requested
        if backup_original:
            now = int(time.time())
            backup = f"{file}.{now}"
            shutil.copy(file, backup)
            print(f"Stored a backup at: {backup}")

        # update the original file
        with open(file, "w", encoding="utf-8") as f:
            f.writelines(lines)
            print(f"Cleaned list in dictionary: {file}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean all lists of words found in a dictionary"
    )
    parser.add_argument("dir", help="Path to the dictionary dir.")
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Write a timestamped copy of each file before overwriting it.",
    )
    args = parser.parse_args()

    clean_dictionary(args.dir, backup_original=args.backup)


if __name__ == "__main__":
    main()
