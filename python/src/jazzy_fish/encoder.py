"""
Encoder
=======

Contains the WordEncoder class that encodes integers to keyphrases and decodes keyphrases and keyphrase abbreviations to integers.

Classes:
    EncoderException - Raised when a WordEncoder is misconfigured.
    KeyPhrase - Represents an encoded keyphrase, along with its prefix short form, and original integer value.
    WordEncoder - Encodes integer identifiers into key phrases and decodes key phrases and abbreviated phrases into integers.
    Wordlist - Represents a wordlist used by a WordEncoder to generate key phrases.
"""

import hashlib
from importlib import resources
import io
import time
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple


# Specifies a default order for constructed sentences.
DEFAULT_WORD_ORDER: List[str] = ["adverb", "verb", "adjective", "noun"]


class Wordlist:
    """Represents a wordlist used by a WordEncoder to generate key phrases.

    Parameters:
        name (str): The name of the underlying dictionary.
        dictionary_words (List[List[str]]): Words defined in the specified dictionary.
        verify_checksum (bool): If true, will verify that the name and checksum of the provided wordlist matches its contents
    """

    def __init__(
        self,
        name: str,
        dictionary_words: List[List[str]],
        verify_checksum: bool = True,
        word_order: Optional[List[str]] = None,
    ):
        """
        Constructs a new instance of Wordlist.

        Parameters:
            name (str): The name of the underlying dictionary.
            dictionary_words (List[List[str]]): Words defined in the specified dictionary.
            verify_checksum (bool): If true, will verify that the name and checksum of the provided wordlist matches its contents.
        """

        # Determine the dictionary's name and checksum
        name_parts = name.split("_")
        if len(name_parts) != 2:
            raise ValueError(
                f"Dictionary name is invalid ({name}), should match '[prefix]_[checksum]'"
            )
        if not len(name_parts[0]) or not all([c.isdigit() for c in name_parts[0]]):
            raise ValueError(
                f"Dictionary name must contain the identifying positions for word abbreviations, got: '{name_parts[0]}'"
            )

        self.name = name
        self.tag = _wordlist_tag(name)
        self.word_order = list(word_order) if word_order else None
        self._abbr_positions = name_parts[0]
        self._abbr_char_positions = [int(c) for c in name_parts[0]]
        self._checksum = name_parts[1]

        # Load and cache wordlists
        self._words = [[word.strip() for word in lst] for lst in dictionary_words]

        # Every guarantee below is one the encoding depends on and nothing else
        # enforces. A dict comprehension over colliding keys keeps the last index
        # silently, so an unvalidated wordlist decodes to the wrong integer rather
        # than failing.
        self._validate_words()

        # Map words to dictionary position
        self._word_positions = [
            {word: i for i, word in enumerate(lst)} for lst in self._words
        ]
        # Abbreviations, in list order. Building this costs nothing: the same
        # prefixes are computed for _abbr_to_pos below and were previously thrown
        # away as dict keys, leaving encode() to recompute them on every call.
        self._prefixes = [[self.to_prefix(word) for word in lst] for lst in self._words]
        # Map of word abbreviations to dictionary positions
        self._abbr_to_pos = [
            {prefix: idx for idx, prefix in enumerate(lst)} for lst in self._prefixes
        ]

        # Check that the provided words match the provided dictionary name.
        # The digests are hashed in list order, so a permuted word_order changes
        # the aggregate and is caught here rather than silently producing a
        # different encoding for every integer.
        if verify_checksum:
            checksum = Wordlist.compute_checksum(self._words, self._abbr_positions)
            hash = checksum[:7]
            if self._checksum != hash:
                order = (
                    f" (loaded with word order {self.word_order})"
                    if self.word_order and self.word_order != DEFAULT_WORD_ORDER
                    else ""
                )
                raise ValueError(
                    f"Checksum validation has failed, expected '{self._checksum}', got '{hash}'{order}"
                )

        # Stores the attributes needed by WordEncoder to fulfill encode/decode requests
        self._radices = [len(lst) for lst in self._words]
        self._max_words_in_phrase = len(self._words)

    def _validate_words(self) -> None:
        """Rejects wordlists that cannot round-trip through encode/decode."""

        required_length = max(self._abbr_char_positions) + 1

        for list_index, words in enumerate(self._words):
            if not words:
                raise ValueError(f"Word list {list_index} is empty")

            seen: dict[str, int] = {}
            prefixes: dict[str, str] = {}
            for position, word in enumerate(words):
                if not word:
                    raise ValueError(
                        f"Word list {list_index} contains an empty word; "
                        "blank lines are not valid entries"
                    )
                if len(word) < required_length:
                    raise ValueError(
                        f"Word '{word}' in list {list_index} is {len(word)} characters, "
                        f"but abbreviation positions '{self._abbr_positions}' need at least {required_length}"
                    )
                if word in seen:
                    raise ValueError(
                        f"Word '{word}' appears more than once in list {list_index} "
                        f"(positions {seen[word]} and {position})"
                    )
                seen[word] = position

                prefix = self.to_prefix(word)
                if prefix in prefixes:
                    raise ValueError(
                        f"Words '{prefixes[prefix]}' and '{word}' in list {list_index} "
                        f"share the abbreviation '{prefix}'; abbreviations must be unique"
                    )
                prefixes[prefix] = word

    def to_prefix(self, word: str) -> str:
        """Abbreviates a word, based on the configured positions"""
        return "".join([word[i] for i in self._abbr_char_positions])

    @staticmethod
    def load(
        from_path: str,
        package_name: Optional[str] = None,
        word_order: List[str] = DEFAULT_WORD_ORDER,
    ):
        """
        Given a path, load all words in the wordlist in the specified order.

        Parameters:
            from_path (str): Specifies a directory that contains a wordlist.
            package_name (Optional[str]): If specified, the path will be loaded from a package.
            word_order (List[str]): Specifies the order in which the words will be loaded.
                                    Defaults to DEFAULT_WORD_ORDER.

        Returns:
            Wordlist: An initialized Wordlist class
        """

        dictionary_name = Path(from_path).name
        words = [
            _read_words(f"{from_path}/{word}.txt", package_name) for word in word_order
        ]

        return Wordlist(
            name=dictionary_name, dictionary_words=words, word_order=word_order
        )

    @staticmethod
    def compute_checksum(wordlists: List[List[str]], position_in_word: str) -> str:
        """
        Computes a checksum for the specified wordlists and abbreviation positions.

        The per-list digests are hashed in list order, not sorted, because the
        order of the word lists decides what every integer encodes to. Sorting
        them made the checksum blind to the one thing it exists to pin down.
        """

        checksums = [Wordlist.checksum(words) for words in wordlists]
        return aggregate_checksums([position_in_word] + checksums)

    @staticmethod
    def checksum(words: List[str]) -> str:
        """Calculates the SHA-1 checksum of a list of words."""

        sha1 = hashlib.sha1(usedforsecurity=False)
        bytes = "\n".join(words).encode("utf-8")
        buffer = io.BytesIO(bytes)
        try:
            while chunk := buffer.read(8192):
                sha1.update(chunk)
        finally:
            buffer.close()

        return sha1.hexdigest()


class KeyPhrase(NamedTuple):
    """An integer with its keyphrase, plain abbreviation, and tagged abbreviation."""

    id: int
    abbr: str
    keyphrase: str
    verified_abbr: str


class EncoderException(Exception):
    """
    Raised when a WordEncoder is misconfigured.
    """

    pass


class WordEncoder:
    """
    Encodes integers to keyphrases and decodes keyphrases and keyphrase abbreviations to integers.

    Attributes:
        wordlist (Wordlist): Word list used to map integers to words.
        min_phrase_size (int): What is the minimum sequence that should be returned.
                               If not provided, it will default to the wordlist size.
        separator (str): The separator character used to delimit keyphrase and abbreviation parts
                         (e.g., "niftier-engine", or "nif-eng")
    """

    def __init__(
        self,
        wordlist: Wordlist,
        min_phrase_size: Optional[int] = None,
        separator: str = "-",
    ):
        """
        Constructs a new instance of WordEncoder.

        Parameters:
            wordlist (Wordlist): Word list used to map integers to words.
            min_phrase_size (int): What is the minimum sequence that should be returned.
                                   If not provided, it will default to the number
                                   of word lists provided.
            separator (str): The separator character used to delimit sequence parts
        """
        self._wordlist = wordlist
        self._max_phrase_size = self._wordlist._max_words_in_phrase

        # If min_phrase_size is not provided, default to the maximum available
        if min_phrase_size is None:
            min_phrase_size = self._max_phrase_size

        # Ensure min_phrase_size is valid
        if not (1 <= min_phrase_size <= self._max_phrase_size):
            raise EncoderException(
                f"min_phrase_size must be between 1 and {self._max_phrase_size}"
            )
        self._min_phrase_size = min_phrase_size

        # ensure that any provided split characters are valid
        if not separator or len(separator) > 1:
            raise EncoderException(
                f"You must provide a single character that separates parts of the short identifier: '{separator}' is not valid"
            )
        self.separator = separator

        # cache other needed values
        self._radices = self._wordlist._radices
        self._max_values = self._compute_max_values()
        self._abs_max = self._max_values[-1]

    def encode(self, number: int) -> KeyPhrase:
        """
        Encodes an integer to a [word sequence].

        Parameters:
            number (int): The integer to encode.

        Returns:
            KeyPhrase: The resulting keyphrase.
        """

        # Validate the input.
        # The lower bound matters as much as the upper one: Python's modulo returns a
        # non-negative remainder, so a negative input would encode as some other number.
        if number < 0:
            raise EncoderException(
                f"The number ({number}) is negative; only values in [0, {self._abs_max - 1}] can be encoded"
            )
        if number >= self._abs_max:
            raise EncoderException(
                f"The number ({number}) is too large to be encoded with up to {self._max_phrase_size} words (max: {self._max_values[-1] - 1})"
            )

        # Determine the number of words needed
        words_needed = self._determine_sequence_size(number)
        original_val = number

        # Walk the radices right-to-left, collecting the word and its abbreviation
        # for each position. Both lists come out reversed and are flipped once at
        # the end, which avoids allocating a full-width index list per call.
        words = self._wordlist._words
        prefixes = self._wordlist._prefixes
        selected_words = []
        short_sequence = []

        boundary = self._max_phrase_size - 1
        for i in range(boundary, boundary - words_needed, -1):
            list_size = self._radices[i]
            index = number % list_size
            selected_words.append(words[i][index])
            short_sequence.append(prefixes[i][index])

            # Calculate the remaining value to be encoded by the next radix
            number //= list_size

        selected_words.reverse()
        short_sequence.reverse()

        abbr = self.separator.join(short_sequence)
        keyphrase = self.separator.join(selected_words)

        return KeyPhrase(
            abbr=abbr,
            keyphrase=keyphrase,
            id=original_val,
            verified_abbr=abbr + self._wordlist.tag,
        )

    def decode(self, keyphrase: str) -> int:
        """
        Decodes a keyphrase or either abbreviation form to an integer.

        Only tagged abbreviations check the wordlist tag. Full words take
        precedence when a custom wordlist also permits an abbreviation reading.

        Parameters:
            keyphrase (str): The keyphrase or abbreviation to decode.

        Returns:
            int: The corresponding integer.
        """

        words = keyphrase.split(self.separator)
        seq_length = len(words)
        try:
            if seq_length > self._max_phrase_size:
                raise EncoderException(
                    f"The sequence contains more words than can be decoded with up to {self._max_phrase_size} words"
                )
            if seq_length < self._min_phrase_size:
                raise EncoderException(
                    f"The phrase contains {seq_length} word(s), but this encoder never emits fewer than {self._min_phrase_size}"
                )

            return self._to_int(words, self._wordlist._word_positions, "word")
        except EncoderException:
            if self._is_abbreviation(keyphrase) or self._is_abbreviation(
                keyphrase[:-_TAG_LENGTH]
            ):
                return self.decode_abbr(keyphrase)
            raise

    def decode_abbr(self, abbr: str) -> int:
        """
        Decodes a plain or tagged abbreviation to an integer.

        A supplied tag must match this wordlist. Untagged input relies on the
        caller choosing the correct wordlist.

        Parameters:
            abbr (str): The keyphrase abbreviation to decode.

        Returns:
            int: The corresponding integer.
        """

        if not self._is_abbreviation(abbr) and self._is_abbreviation(
            abbr[:-_TAG_LENGTH]
        ):
            if abbr[-_TAG_LENGTH:] != self._wordlist.tag:
                raise EncoderException(
                    f"The abbreviation '{abbr}' has a wordlist tag that does not match '{self.wordlist_name}' "
                    f"(expected '{self._wordlist.tag}')"
                )
            abbr = abbr[:-_TAG_LENGTH]

        word_abbrs = abbr.split(self.separator)
        seq_length = len(word_abbrs)
        if seq_length > self._max_phrase_size:
            raise EncoderException(
                f"The abbreviation contains more parts than can be decoded with up to {self._max_phrase_size} words"
            )
        if seq_length < self._min_phrase_size:
            raise EncoderException(
                f"The abbreviation contains {seq_length} part(s), but this encoder never emits fewer than {self._min_phrase_size}"
            )

        return self._to_int(word_abbrs, self._wordlist._abbr_to_pos, "abbreviation")

    def _is_abbreviation(self, value: str) -> bool:
        """Checks whether every part is a known abbreviation at its position."""
        parts = value.split(self.separator)
        if not self._min_phrase_size <= len(parts) <= self._max_phrase_size:
            return False
        positions = self._wordlist._abbr_to_pos[-len(parts) :]
        return all(part in position for part, position in zip(parts, positions))

    @property
    def wordlist_name(self) -> str:
        """The wordlist name to persist alongside identifiers."""
        return self._wordlist.name

    def _to_int(
        self, parts: List[str], positions: List[Dict[str, int]], what: str
    ) -> int:
        """
        Converts a list of words (or abbreviations) to the integer they encode.

        The lists are mixed-radix digits, most significant first, so the value is
        accumulated with Horner's method against the trailing radices.
        """

        seq_length = len(parts)
        relevant_positions = positions[-seq_length:]
        relevant_radices = self._radices[-seq_length:]

        result = 0
        for i, part in enumerate(parts):
            try:
                index = relevant_positions[i][part]
            except KeyError:
                raise EncoderException(
                    f"'{part}' is not a known {what} at position {i} of the phrase"
                ) from None
            result = result * relevant_radices[i] + index

        return result

    def get_max(self) -> int:
        """
        Returns the absolute max number that can be encoded by this class.

        Returns:
            int: The exclusive upper bound; the largest encodable value is this minus one.
        """
        return self._abs_max

    def _compute_max_values(self) -> List[int]:
        # Compute the maximum encodable values
        # The resulting indices are reversed compared to the list of words (first element represents last word)
        max_values = [1] * (self._max_phrase_size + 1)
        for i in range(1, (self._max_phrase_size + 1)):
            # With each added word we can represent (W) x (W-1) integers
            max_values[i] = max_values[i - 1] * self._radices[self._max_phrase_size - i]
        return max_values

    def _determine_sequence_size(self, number: int) -> int:
        # Determine the number of words needed to encode the result
        words_needed = self._min_phrase_size
        boundary = self._max_phrase_size + 1
        for i in range(self._min_phrase_size, boundary):
            words_needed = i
            if self._max_values[i] > number:
                break
        return words_needed


def check_capacity(
    generator: "object",
    encoder: "WordEncoder",
    min_lifetime_days: float = 3650.0,
) -> None:
    """
    Raises unless the generator's identifiers stay encodable for the given period.

    A Generator and a WordEncoder are designed to compose, but neither knows the
    other's limits: machine and sequence bits shift the time component left, so
    every bit halves how long the identifiers fit. A configuration that outgrows
    its wordlist fails at encode() in production rather than at startup.

    Parameters:
        generator: A Generator whose identifiers will be encoded.
        encoder (WordEncoder): The encoder that will encode them.
        min_lifetime_days (float): How long the pair must keep working.

    Raises:
        EncoderException: If the generator outgrows the encoder within the period.
    """

    import datetime

    capacity = encoder.get_max()
    horizon = time.time() + min_lifetime_days * 86400
    largest = generator.max_id_at(horizon)  # type: ignore[attr-defined]

    if largest >= capacity:
        exhausted = generator.exhausts_at(capacity)  # type: ignore[attr-defined]
        when = datetime.datetime.fromtimestamp(
            exhausted, tz=datetime.timezone.utc
        ).date()
        raise EncoderException(
            f"This generator outgrows the encoder on {when}, sooner than the "
            f"{min_lifetime_days:,.0f} days required. Its identifiers reach "
            f"{largest:,} against a capacity of {capacity:,}. Use a larger wordlist, "
            f"a coarser resolution, fewer machine/sequence bits, or a later epoch."
        )


def _read_words(from_path: str, package_name: Optional[str] = None) -> List[str]:
    """Reads words from a file that is either on disk, or part of the specified package."""

    # Determine input file
    data_path = from_path
    if package_name is not None:
        data_path = str(resources.files(package_name).joinpath(from_path))

    # Read all words from file
    with open(data_path, "r", encoding="utf-8") as file:
        data = [ln.strip() for ln in file]
    return data


_TAG_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
_TAG_LENGTH = 2


def _wordlist_tag(name: str) -> str:
    """Derives a two-character base-36 tag from the full wordlist name."""
    value = int.from_bytes(
        hashlib.sha1(name.encode("utf-8"), usedforsecurity=False).digest()[:8], "big"
    )
    tag = ""
    for _ in range(_TAG_LENGTH):
        value, remainder = divmod(value, len(_TAG_ALPHABET))
        tag = _TAG_ALPHABET[remainder] + tag
    return tag


def aggregate_checksums(checksums: List[str]) -> str:
    """
    Calculate an aggregate checksum from a list of checksums.

    The order given is the order hashed. Callers are responsible for passing the
    parts in a defined order; for a wordlist that is the abbreviation positions
    followed by the per-list digests in word-list order.
    """

    sha1 = hashlib.sha1(usedforsecurity=False)
    for checksum in checksums:
        sha1.update(checksum.encode("utf-8"))

    return sha1.hexdigest()
