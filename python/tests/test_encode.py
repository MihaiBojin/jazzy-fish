import unittest

from jazzy_fish.encoder import WordEncoder, EncoderException, Wordlist


class TestEncode(unittest.TestCase):
    def setUp(self):
        # Define word lists
        adverbs = ["absurdly", "busily", "capably"]
        verbs = ["abandoned", "bearded", "checked"]
        adjectives = ["able", "blond", "chubby"]
        nouns = ["apple", "bird", "cat", "dog"]
        words = [adverbs, verbs, adjectives, nouns]
        self.wordlist = Wordlist("0_NOVERIFY", words, verify_checksum=False)

    def test_should_fail(self):
        encoder = WordEncoder(self.wordlist, min_phrase_size=1)

        with self.assertRaises(EncoderException):
            more_than_available = encoder.get_max() + 1
            encoder.encode(more_than_available)

    def test_expected_results(self):
        test_cases = [
            (23, 1, "bearded-chubby-dog"),
            (24, 1, "checked-able-apple"),
            (107, 1, "capably-checked-chubby-dog"),
            (12, 1, "bearded-able-apple"),
            (4, 1, "blond-apple"),
        ]

        for num, min_seq, expected in test_cases:
            result = WordEncoder(self.wordlist, min_phrase_size=min_seq).encode(num)
            got = result.keyphrase
            prefix = result.abbr
            msg = f"Error {num:3} (min_words={min_seq:1}); expected: '{expected:30}', got: '{got:30}', prefix: '{prefix:>4}'"
            self.assertEqual(got, expected, msg=msg)

    def test_can_encode_all_values(self):
        solution_space = range(
            0,
            WordEncoder(self.wordlist, min_phrase_size=1).get_max(),
        )
        test_cases = (
            [(i, 1) for i in solution_space]
            + [(i, 2) for i in solution_space]
            + [(i, 3) for i in solution_space]
            + [(i, 4) for i in solution_space]
        )

        for num, min_seq in test_cases:
            encoded = WordEncoder(self.wordlist, min_phrase_size=min_seq).encode(num)
            self.assertIsNotNone(encoded)

            got = encoded.keyphrase
            prefix = encoded.abbr
            msg = f"Encoded '{num:3}' (min_words={min_seq:1}), got: '{got:30}', prefix: '{prefix:>4}'"
            print(msg)


if __name__ == "__main__":
    unittest.main()
