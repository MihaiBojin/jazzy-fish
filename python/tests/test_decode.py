import unittest

from jazzy_fish.encoder import WordEncoder, EncoderException, Wordlist


class TestDecode(unittest.TestCase):
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

        for expected, min_seq, words in test_cases:
            encoder = WordEncoder(self.wordlist, min_phrase_size=min_seq)

            # words can be decoded to their corresponding value
            got = encoder.decode(words)
            msg = f"Error {words:30} (min_words={min_seq:1}); expected: '{expected:3}', got: '{got:3}'"
            self.assertEqual(got, expected, msg=msg)

            # short ID sequences can be decoded to their corresponding value
            encoded = encoder.encode(expected)
            got2 = encoder.decode_abbr(encoded.abbr)
            msg2 = f"Error {encoded.abbr:30} (min_words={min_seq:1}); expected: '{expected:3}', got: '{got2:3}'"
            self.assertEqual(got2, expected, msg2)

    def test_can_encode_and_decode_all_values(self):
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

        for expected, min_words in test_cases:
            encoder = WordEncoder(self.wordlist, min_phrase_size=min_words)
            encoded = encoder.encode(expected)
            encoded_str = encoded.keyphrase
            self.assertIsNotNone(encoded)

            got = encoder.decode(encoded.keyphrase)
            msg = f"Encoded '{expected:3}' (min_words={min_words:1}), got: '{encoded_str:30}', then decoded back to '{got:3}'"
            self.assertEqual(got, expected, msg)

            got2 = encoder.decode_abbr(encoded.abbr)
            msg2 = f"Encoded '{expected:3}' (min_words={min_words:1}), got: '{encoded.abbr:30}', then decoded back to '{got2:3}'"
            self.assertEqual(got2, expected, msg2)


if __name__ == "__main__":
    unittest.main()
