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
from pathlib import Path
from typing import List, Optional, NamedTuple


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
        self, name: str, dictionary_words: List[List[str]], verify_checksum: bool = True
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
        if not len(name_parts[0]) or not all(["0" <= c < "9" for c in name_parts[0]]):
            raise ValueError(
                f"Dictionary name must contain the identifying positions for word abbreviations, got: '{name_parts[0]}'"
            )

        self.name = name
        self._abbr_positions = name_parts[0]
        self._abbr_char_positions = [int(c) for c in name_parts[0]]
        self._checksum = name_parts[1]

        # Two base-36 characters identifying this wordlist. Decoding an
        # abbreviation produced by a different wordlist mostly raises, but 0.44%
        # of the time it returned a plausible wrong integer instead.
        #
        # Derived from the whole name rather than a slice of the checksum: the
        # shipped 012_8562fb9 and 024_84f184f share a leading checksum character,
        # so a one-character slice would have collided and protected nothing.
        self.tag = _wordlist_tag(name)

        # Load and cache wordlists
        self._words = [[word.strip() for word in lst] for lst in dictionary_words]
        # Map words to dictionary position
        self._word_positions = [
            {word.strip(): i for i, word in enumerate(lst)} for lst in dictionary_words
        ]
        # Map of word abbreviations to dictionary positions
        self._abbr_to_pos = [
            {self.to_prefix(word.strip()): idx for idx, word in enumerate(lst)}
            for lst in dictionary_words
        ]

        # Check that the provided words match the provided dictionary name
        if verify_checksum:
            checksum = Wordlist.compute_checksum(self._words, self._abbr_positions)
            hash = checksum[:7]
            if self._checksum != hash:
                raise ValueError(
                    f"Checksum validation has failed, expected '{self._checksum}', got '{hash}'"
                )

        # Stores the attributes needed by WordEncoder to fulfill encode/decode requests
        self._radices = [len(lst) for lst in self._words]
        self._max_words_in_phrase = len(self._words)

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
            word_lists (List[str]): Specifies the order in which the words will be loaded.
                                    Defaults to DEFAULT_WORD_ORDER.

        Returns:
            Wordlist: An initialized Wordlist class
        """

        dictionary_name = Path(from_path).name
        words = [
            _read_words(f"{from_path}/{word}.txt", package_name) for word in word_order
        ]

        return Wordlist(name=dictionary_name, dictionary_words=words)

    @staticmethod
    def compute_checksum(wordlists: List[List[str]], position_in_word: str) -> str:
        """Computes a checksum for the specified wordlists and abbreviation position."""

        checksums = [Wordlist.checksum(words) for words in wordlists]
        checksums.sort()
        return aggregate_checksums([position_in_word] + checksums)

    @staticmethod
    def checksum(words: List[str]) -> str:
        """Calculates the SHA-1 checksum of a list of words."""

        sha1 = hashlib.sha1()
        bytes = "\n".join(words).encode("utf-8")
        buffer = io.BytesIO(bytes)
        try:
            while chunk := buffer.read(8192):
                sha1.update(chunk)
        finally:
            buffer.close()

        return sha1.hexdigest()


class KeyPhrase(NamedTuple):
    """Represents a unique key phrase, along with its abbreviated form, and original integer value."""

    id: int
    abbr: str
    keyphrase: str


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
        tag_abbreviations (bool): If true, abbreviations carry a trailing character
                                  identifying the wordlist that produced them, so
                                  decoding one under the wrong wordlist fails
                                  instead of returning a wrong integer.
    """

    def __init__(
        self,
        wordlist: Wordlist,
        min_phrase_size: Optional[int] = None,
        separator: str = "-",
        tag_abbreviations: bool = True,
    ):
        """
        Constructs a new instance of WordEncoder.

        Parameters:
            wordlist (Wordlist): Word list used to map integers to words.
            min_sequence_size (int): What is the minimum sequence that should be returned.
                                    If not provided, it will default to the number
                                    word lists provided.
            separator (str): The separator character used to delimit sequence parts
        """
        self._wordlist = wordlist
        self._max_phrase_size = self._wordlist._max_words_in_phrase

        # If the min_sequence is not provided, default to the maximum available
        if min_phrase_size is None:
            min_phrase_size = self._max_phrase_size

        # Ensure min_sequence_size is valid
        if not (1 <= min_phrase_size <= self._max_phrase_size):
            raise EncoderException(
                f"min_sequence_size must be between 1 and {self._max_phrase_size}"
            )
        self._min_phrase_size = min_phrase_size

        # ensure that any provided split characters are valid
        if not separator or len(separator) > 1:
            raise EncoderException(
                f"You must provide a single character that separates parts of the short identifier: '{separator}' is not valid"
            )
        self.separator = separator
        self.tag_abbreviations = tag_abbreviations

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

        # Validate the input
        if number >= self._abs_max:
            raise EncoderException(
                f"The number ({number}) is too large to be encoded with up to {self._max_phrase_size} words (max: {self._max_values[-1] - 1})"
            )

        # Determine the number of words needed
        words_needed = self._determine_sequence_size(number)
        original_val = number

        # Initialize indexes with -1, to protect against bugs (zeroes would be valid values and could not be distinguished)
        indexes = [-1] * self._max_phrase_size
        boundary = self._max_phrase_size - 1

        # Calculate the corresponding indexes for each word
        for i in range(boundary, boundary - words_needed, -1):
            # Populate the appropriate index, right-to-left
            list_size = self._radices[i]
            indexes[i] = number % list_size

            # Calculate the remaining value to be encoded by the next radix
            number //= list_size

        # Calculate the resulting word sequence
        input = list(
            zip(self._wordlist._words[-words_needed:], indexes[-words_needed:])
        )
        selected_words = [lst[i] for lst, i in input]

        # Calculate the short identifier
        short_sequence = [self._wordlist.to_prefix(word) for word in selected_words]
        abbr = self.separator.join(short_sequence)
        if self.tag_abbreviations:
            abbr += self._wordlist.tag
        keyphrase = self.separator.join(selected_words)

        return KeyPhrase(abbr=abbr, keyphrase=keyphrase, id=original_val)

    def decode(self, keyphrase: str) -> int:
        """
        Decodes a keyphrase to an integer.

        Parameters:
            words (List[str]): The word sequence to decode.

        Returns:
            int: The corresponding integer.
        """

        words = keyphrase.split(self.separator)
        seq_length = len(words)
        if seq_length > self._max_phrase_size:
            raise EncoderException(
                f"The sequence contains more words that can be decoded with up to {self._max_phrase_size} words"
            )

        # Calculate the indices of each specified word
        relevant_positions = self._wordlist._word_positions[-seq_length:]
        indices = [relevant_positions[i][word] for i, word in enumerate(words)]

        # Transform indexes into integers
        result = 0
        relevant_radices = self._radices[-seq_length:]
        for i, index in enumerate(indices):
            list_size = relevant_radices[i]
            result = result * list_size + index

        return result

    def decode_abbr(self, abbr: str) -> int:
        """
        Decodes an abbreviation to an integer.

        Parameters:
            abbr (str): The keyphrase abbreviation to decode.

        Returns:
            int: The corresponding integer.
        """

        if self.tag_abbreviations:
            expected = self._wordlist.tag
            if not abbr.endswith(expected):
                raise EncoderException(
                    f"The abbreviation '{abbr}' was not produced by wordlist "
                    f"'{self._wordlist.name}' (expected it to end with '{expected}')"
                )
            abbr = abbr[: -len(expected)]

        word_abbrs = abbr.split(self.separator)
        if not len(word_abbrs):
            raise EncoderException(
                f"The id ({abbr}) could not be split into words using the provided split character ({self.separator})"
            )
        seq_length = len(word_abbrs)

        # Calculate the indices of each specified word
        relevant_prefixes = self._wordlist._abbr_to_pos[-seq_length:]
        indices = [relevant_prefixes[i][prefix] for i, prefix in enumerate(word_abbrs)]

        # Transform indexes into integers
        result = 0
        relevant_radices = self._radices[-seq_length:]
        for i, index in enumerate(indices):
            list_size = relevant_radices[i]
            result = result * list_size + index

        return result

    @property
    def wordlist_name(self) -> str:
        """The name of the wordlist backing this encoder, for storing alongside ids."""
        return self._wordlist.name

    def get_max(self) -> int:
        """
        Returns the absolute max number that can be encoded by this class.

        Returns:
            int: An integer value that is the upper bound of integers that can be represented with the configured word lists.
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


def _read_words(from_path: str, package_name: Optional[str] = None) -> List[str]:
    """Reads words from a file that is either on disk, or part of the specified package."""

    # Determine input file
    data_path = from_path
    if package_name is not None:
        data_path = str(resources.files(package_name).joinpath(from_path))

    # Read all words from file
    with open(data_path, "r") as file:
        data = [ln.strip() for ln in file]
    return data


_TAG_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
_TAG_LENGTH = 2


def _wordlist_tag(name: str) -> str:
    """Derives a short, stable identifier for a wordlist from its full name."""

    value = int.from_bytes(
        hashlib.sha1(name.encode("utf-8"), usedforsecurity=False).digest()[:8], "big"
    )
    tag = ""
    for _ in range(_TAG_LENGTH):
        value, remainder = divmod(value, len(_TAG_ALPHABET))
        tag = _TAG_ALPHABET[remainder] + tag
    return tag


def aggregate_checksums(checksums: List[str]) -> str:
    """Calculate an aggregate checksum from a list of checksums."""

    sha1 = hashlib.sha1()
    # Sort to ensure consistent order
    for checksum in sorted(checksums):
        sha1.update(checksum.encode("utf-8"))

    return sha1.hexdigest()
