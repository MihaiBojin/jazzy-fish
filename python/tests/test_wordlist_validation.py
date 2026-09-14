import unittest

from jazzy_fish.encoder import Wordlist


class TestWordlistValidation(unittest.TestCase):
    ADVERBS = ["absurdly", "busily", "capably"]

    def _build(self, name: str, nouns: list) -> Wordlist:
        return Wordlist(name, [self.ADVERBS, nouns], verify_checksum=False)

    def test_rejects_duplicate_words(self):
        # A dict comprehension keeps the last index, so encode(2) produced "cat"
        # and decode("cat") returned 3.
        with self.assertRaises(ValueError) as ctx:
            self._build("0_NOVERIFY", ["apple", "bird", "cat", "cat"])
        self.assertIn("more than once", str(ctx.exception))

    def test_rejects_colliding_abbreviations(self):
        # "cat" and "cattle" both abbreviate to "cat" under positions 012.
        with self.assertRaises(ValueError) as ctx:
            self._build("012_NOVERIFY", ["apples", "birdie", "cat", "cattle"])
        self.assertIn("share the abbreviation", str(ctx.exception))

    def test_rejects_words_shorter_than_the_abbreviation_positions(self):
        with self.assertRaises(ValueError) as ctx:
            self._build("0123_NOVERIFY", ["ox", "birdie", "cattle"])
        self.assertIn("at least 4", str(ctx.exception))

    def test_rejects_empty_words(self):
        # _read_words keeps blank lines, so this is reachable from a real file.
        with self.assertRaises(ValueError) as ctx:
            self._build("0_NOVERIFY", ["apple", "", "bird"])
        self.assertIn("empty word", str(ctx.exception))

    def test_rejects_an_empty_word_list(self):
        with self.assertRaises(ValueError):
            self._build("0_NOVERIFY", [])

    def test_accepts_abbreviation_position_nine(self):
        # The check read '"0" <= c < "9"', so position 9 was rejected.
        long_words = ["abcdefghij", "klmnopqrst"]
        self.assertIsNotNone(
            Wordlist("9_NOVERIFY", [long_words], verify_checksum=False)
        )

    def test_shipped_wordlists_still_validate(self):
        for name in ("012_8562fb9", "024_84f184f", "01234_f233650"):
            self.assertIsNotNone(Wordlist.load(f"resources/{name}", "jazzy_fish"))


if __name__ == "__main__":
    unittest.main()
