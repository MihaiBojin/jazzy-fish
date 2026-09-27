"""
Generate Wordlists
==================

Generates combinations of word parts of varied prefix lengths to help the user choose the best configuration
for their use-case.

"""

import argparse
from functools import reduce
from math import prod
from pathlib import Path
import random
from jazzy_fish import encoder
import time
from typing import List, Tuple

from jazzy_fish_tools.helpers import (
    MAX_LENGTH,
    MIN_LENGTH,
    OUTPUT_PATH,
    generate_all_prefix_combinations,
    is_letter,
    load_ignored_words,
    reset_location,
)

# Set to true to only analyze real prefixes (01, 012, 0123, etc.)
ONLY_SEQ_PREFIXES = False

# Defines the prefix length variations to consider when generating combinations
PREFIX_LENGTHS: Tuple[int, ...] = (2, 3, 4, 5, 6)

# The allowed word parts that must match file names in a dictionary directory
ALLOWED_WORD_PARTS: Tuple[str, ...] = ("adverb", "adjective", "verb", "noun")


def _load_words(directory: Path) -> dict[str, List[str]]:
    """Read valid words, assigning duplicates to the first file by name."""
    words: dict[str, List[str]] = {part: [] for part in ALLOWED_WORD_PARTS}
    seen = set(load_ignored_words())
    for file in sorted(path for path in directory.iterdir() if path.is_file()):
        part = file.stem
        if part not in ALLOWED_WORD_PARTS:
            raise ValueError(
                f"All files in a dictionary dir must match one of the ALLOWED_WORD_PARTS; {part} is invalid"
            )
        with file.open(encoding="utf-8") as source:
            for line in source:
                word = line.strip()
                if not MIN_LENGTH <= len(word) <= MAX_LENGTH:
                    continue
                if not is_letter(word) or word in seen:
                    continue
                seen.add(word)
                words[part].append(word)

    # Prefix exclusions apply across every word part and position combination.
    prefixes = {
        word[:length]
        for entries in words.values()
        for word in entries
        for length in range(MIN_LENGTH, len(word))
    }
    return {
        part: [word for word in entries if word not in prefixes]
        for part, entries in words.items()
    }


def _select_words(words: List[str], positions: Tuple[int, ...]) -> List[str]:
    """Select the alphabetically first word for each abbreviation."""
    selected: dict[str, str] = {}
    for word in words:
        if len(word) <= positions[-1]:
            continue
        abbreviation = "".join(word[position] for position in positions)
        if abbreviation not in selected or word < selected[abbreviation]:
            selected[abbreviation] = word
    return sorted(selected.values())


def main() -> None:
    # Define the input dictionary
    parser = argparse.ArgumentParser(description="Specify the dictionary directory")
    parser.add_argument("dir", help="Path to the dictionary directory.")
    args = parser.parse_args()

    reset_location(Path(OUTPUT_PATH))
    start_time = time.time()
    words = _load_words(Path(args.dir))

    print("Generating final word lists...")
    for prefix_length in PREFIX_LENGTHS:
        for char_positions in generate_all_prefix_combinations(prefix_length):
            # Skip non-sequential prefixes, if needed
            is_prefix = char_positions == tuple(range(0, prefix_length))
            if ONLY_SEQ_PREFIXES and not is_prefix:
                continue

            position_in_word = "".join([str(c) for c in char_positions])

            # Generate an output location for the wordlist, ensuring it exists
            wordlist_out_dir = f"{OUTPUT_PATH}/processed/{position_in_word}"
            reset_location(Path(wordlist_out_dir), remove_dir=False)

            wordlist_files: List[str] = list()
            stats: List[Tuple[str, int]] = list()

            # Note: this code assumes that the four word parts are always specified and will only process these, not other names
            for word_part in ALLOWED_WORD_PARTS:
                word_size = f"[{MIN_LENGTH}, {MAX_LENGTH}]"
                print(
                    f"Generating {position_in_word}, word type '{word_part}', word length {word_size}..."
                )

                selected_words = _select_words(words[word_part], char_positions)

                # Store the selected words
                outfile = f"{wordlist_out_dir}/{word_part}.txt"
                with open(outfile, "w", encoding="utf-8") as out:
                    out.write("\n".join(selected_words))
                print(f"Saved '{outfile}'\n")

                # Store the wordlists and stats
                wordlist_files.append(outfile)
                stats.append((word_part, len(selected_words)))

            # Generate stats, choosing the top 2/3/4 word parts by total choices
            print(f"Storing stats for 2/3/4 words for {position_in_word}...\n")
            ordered = sorted(stats, key=lambda x: x[1])

            for take in (2, 3, 4):
                selected = [f[0] for f in ordered[-take:]]
                _save_stats(
                    dict(stats), position_in_word, is_prefix, selected, wordlist_files
                )

            # Generate checksums
            checksums = list()
            checksum_file = list()
            for f in wordlist_files:
                # Compute checksum by reading each wordfile
                with open(f, "r") as wfile:
                    words_in_file = [ln.strip() for ln in wfile]
                checksum = encoder.Wordlist.checksum(words_in_file)

                # Store checksums
                checksums.append(checksum)
                checksum_file.append(f"{checksum}  {Path(f).name}")

            # Compute the aggregated checksum that accounts for the abbrevation position
            agg_checksum = encoder.aggregate_checksums([position_in_word] + checksums)

            # Generate the checksum file
            outfile = f"{wordlist_out_dir}/checksums.sha1"
            with open(outfile, "w") as out:
                # The first checksum will represent the aggregate checksum for all wordlists
                out.write(f"{agg_checksum}\n")
                for checksum in sorted(checksum_file):
                    out.write(f"{checksum}\n")

            # Rename the output wordlist dir to include the abbreviated aggregated checksum
            renamed = f"{OUTPUT_PATH}/processed/{position_in_word}_{agg_checksum[:7]}"
            Path(wordlist_out_dir).rename(renamed)

    end_time = time.time()
    print(f"\nGenerated word lists in: {end_time - start_time:.2f} seconds")


def _save_stats(
    word_counts: dict[str, int],
    position_in_word: str,
    is_prefix: bool,
    word_parts: List[str],
    wordlist_files: List[str],
):
    """Store statistics about the selected words"""

    parts = ", ".join([f"'{w}'" for w in word_parts])
    counts = [
        (part, word_counts[part]) for part in sorted(word_parts) if word_counts[part]
    ]
    # Floating-point multiplication preserves existing statistics rounding.
    total = int(prod((count for _, count in counts), start=1.0)) if counts else 0
    data = [f"{position_in_word:10s} {part:12s} {count:,d}\n" for part, count in counts]
    data.append(f"{'Total':10s} {'':12s} {total:,d}\n")

    outfile = f"{OUTPUT_PATH}/processed/{position_in_word}/stats_{len(word_parts)}.txt"
    with open(outfile, "w") as out:
        years_s = total / 31536000
        years_ms = total / 31536000000

        t = "SEQ" if is_prefix else "RND"
        out.write(
            f"Result: [{years_s: 12,.0f} years at 1/s ] [{total: 22,.0f}] ({parts:42s}) for prefix: '{position_in_word:6s}' [{t}]\n\n"
            f"Result: [{years_ms: 12,.0f} years at 1/ms] [{total: 22,.0f}] ({parts:42s}) for prefix: '{position_in_word:6s}' [{t}]\n\n"
        )
        out.writelines(data)
        out.write(f"Years at 1/s            {years_s:,.2f}\n")
        out.write(f"Years at 1/ms           {years_ms:,.3f}\n")
        out.write("\n")
        out.write("Sample words:\n")

        words = _generate_sample_words(
            wordlist_files=wordlist_files,
            position_in_word=position_in_word,
            min_phrase_size=len(word_parts),
            # The stats describe these word parts, so the samples must too.
            template=" ".join(
                part for part in ALLOWED_WORD_PARTS if part in word_parts
            ),
        )
        out.writelines(words)


def _generate_sample_words(
    wordlist_files: List[str],
    position_in_word: str,
    min_phrase_size: int,
    how_many: int = 50,
    template: str = "adverb verb adjective noun",
) -> List[str]:
    """Generate sample words to give the user an idea of what to expect"""
    # Read all the words
    words = dict()
    for f in wordlist_files:
        word_part = Path(f).stem
        with open(f, "r", encoding="utf-8") as file:
            words[word_part] = file.readlines()

    # Initialize the encoder with the designated template
    ordered = [words[part] for part in template.split(" ")]
    wordlist = encoder.Wordlist(
        f"{position_in_word}_NOVERIFY", ordered, verify_checksum=False
    )
    e = encoder.WordEncoder(wordlist=wordlist, min_phrase_size=min_phrase_size)

    # Generate words
    word_size = f"[{MIN_LENGTH}, {MAX_LENGTH}]"
    print(
        f"Generating sample words for '{position_in_word}', {min_phrase_size} words, word size {word_size}..."
    )

    # Determine the minimum value represented by the desired word size (i.e., W*W)
    sizes = [len(o) for o in ordered[-min_phrase_size + 1 :]]
    min_for_desired_word_size = reduce(lambda x, y: x * y, sizes)

    # Determine the maximum value represented by the desired word size (i.e., W*W*W - 1)
    sizes = [len(o) for o in ordered[-min_phrase_size:]]
    max_for_desired_word_size = reduce(lambda x, y: x * y, sizes) - 1

    # Seeded so a regenerated wordlist produces the same stats file: an unseeded
    # sample made every run report a diff.
    rng = random.Random(f"{position_in_word}/{min_phrase_size}")

    results: List[str] = list()
    for _ in range(0, how_many):
        val = rng.randint(min_for_desired_word_size, max_for_desired_word_size)
        encoded = e.encode(val)
        results.append(f"- {encoded.keyphrase} ({encoded.abbr})\n")

    return results


if __name__ == "__main__":
    main()
