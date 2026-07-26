from datetime import datetime, timezone
from jazzy_fish import WordEncoder, Wordlist, Generator, Resolution


def main() -> None:
    """Functional test that ensures the library can be imported and utilized"""

    # Configure a starting epoch for the sequence
    # Alternatively, you can use the UNIX epoch (0), but that will exhaust some of the solution space
    epoch = datetime(2024, 5, 30, tzinfo=timezone.utc).timestamp()

    # Configure the encoder using one of the default wordlists provided by jazzy-fish
    wordlist = Wordlist.load("resources/012_8562fb9", "jazzy_fish")
    encoder = WordEncoder(wordlist, min_phrase_size=4)

    # Configure the generator (single machine, max one value per time unit, millisecond resolution)
    generator = Generator(
        epoch=epoch,  # Define the epoch
        machine_ids=[0],  # Configure the machine id (partition)
        machine_id_bits=0,  # A single machine
        sequence_bits=0,  # Allow a single ID per machine per time unit
        resolution=Resolution.MILLISECOND,  # Generation sequence resets every millisecond
    )

    # Generate a unique keyphrase
    id = generator.next_id()
    encoded = encoder.encode(id)

    assert encoded is not None, f"Encoding ({id}) should have succeeded, missing value"
    assert len(encoded.keyphrase.split("-")) == 4, (
        f"Expected 4 words, got {len(encoded.keyphrase)}"
    )
    assert encoded.abbr is not None, (
        f"Expected abbreviated phrase, got ({encoded.abbr})"
    )

    # Decode a keyphrase
    got = encoder.decode(encoded.keyphrase)
    assert got == id, (
        f"Decoded phrase ({encoded.keyphrase}) should match the original id ({id})"
    )

    # Decode an abbreviation
    got2 = encoder.decode_abbr(encoded.abbr)
    assert got2 == id, (
        f"Decoded abbreviation ({encoded.abbr}) should match the original id ({id})"
    )

    print("OK.")


if __name__ == "__main__":
    main()
