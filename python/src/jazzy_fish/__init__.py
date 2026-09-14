"""
Jazzy Fish
==========

This package contains the code required by clients who wish to generate jazzy-fish keyphrases.

Modules:
    encoder - Contains the WordEncoder class that can encode integers to [word sequences]
              and decode [word sequences] to integers.
    generator - Contains the Generator and ThreadSafeGenerator classes which can generate unique integer identifiers
                that respect the configured settings and can be later converted to [word sequences] with a WordEncoder.

Usage:

    Import the package and use the provided classes:

    from datetime import datetime, timezone
    from jazzy_fish import WordEncoder, Wordlist, Generator, Resolution

    # Configure a starting epoch for the sequence
    # Alternatively, you can use the UNIX epoch (0), but that will exhaust some of the solution space
    epoch = datetime(2024, 5, 30, tzinfo=timezone.utc).timestamp()

    # Configure the encoder using one of the default wordlists provided by jazzy-fish
    wordlist = Wordlist.load("resources/012_80a1774", "jazzy_fish.encoder")
    encoder = WordEncoder(wordlist, min_phrase_size=4)

    # Configure the generator (single machine, max one value per time unit, millisecond resolution)
    generator = Generator(
        epoch=epoch,        # Define the epoch
        machine_ids=[0],    # Configure the machine id (partition)
        machine_id_bits=0,  # A single machine
        sequence_bits=0,    # Allow a single ID per machine per time unit
        resolution=Resolution.MILLISECOND,  # Generation sequence resets every millisecond
    )

    # Generate a unique keyphrase
    id = generator.next_id()
    encoded = encoder.encode(id)

    # Decode a keyphrase
    got = encoder.decode(encoded.key_phrase)

        # Decode an abbreviation
    got2 = encoder.decode_abbr(encoded.abbr)
"""

from .encoder import KeyPhrase, WordEncoder, Wordlist
from .generator import Generator, Resolution, ThreadSafeGenerator

__all__ = [
    "Generator",
    "KeyPhrase",
    "Resolution",
    "ThreadSafeGenerator",
    "WordEncoder",
    "Wordlist",
]
