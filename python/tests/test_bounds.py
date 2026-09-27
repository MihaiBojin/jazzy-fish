import unittest

from jazzy_fish.encoder import EncoderException, WordEncoder, Wordlist


class TestBounds(unittest.TestCase):
    def setUp(self):
        adverbs = ["absurdly", "busily", "capably"]
        verbs = ["abandoned", "bearded", "checked"]
        adjectives = ["able", "blond", "chubby"]
        nouns = ["apple", "bird", "cat", "dog"]
        self.wordlist = Wordlist(
            "0_NOVERIFY", [adverbs, verbs, adjectives, nouns], verify_checksum=False
        )

    def test_encode_rejects_negative_numbers(self):
        encoder = WordEncoder(self.wordlist, min_phrase_size=1)
        for number in (-1, -5, -108):
            with self.assertRaises(EncoderException, msg=f"encode({number})"):
                encoder.encode(number)

    def test_encode_accepts_the_whole_valid_range(self):
        encoder = WordEncoder(self.wordlist, min_phrase_size=1)
        for number in (0, 1, encoder.get_max() - 1):
            self.assertIsNotNone(encoder.encode(number))

    def test_encode_rejects_the_exclusive_upper_bound(self):
        encoder = WordEncoder(self.wordlist, min_phrase_size=1)
        with self.assertRaises(EncoderException):
            encoder.encode(encoder.get_max())

    def test_decode_rejects_phrases_shorter_than_the_encoder_emits(self):
        encoder = WordEncoder(self.wordlist, min_phrase_size=4)

        # Without a lower bound these decode to a plausible but wrong value:
        # "dog" would return 3, aliasing the full four-word phrase for 3.
        with self.assertRaises(EncoderException):
            encoder.decode("dog")
        with self.assertRaises(EncoderException):
            encoder.decode("able-apple")

    def test_decode_abbr_rejects_abbreviations_shorter_than_the_encoder_emits(self):
        encoder = WordEncoder(self.wordlist, min_phrase_size=4)
        with self.assertRaises(EncoderException):
            encoder.decode_abbr("d")
        with self.assertRaises(EncoderException):
            encoder.decode_abbr("a-a")

    def test_decode_abbr_rejects_too_many_parts(self):
        encoder = WordEncoder(self.wordlist, min_phrase_size=1)
        with self.assertRaises(EncoderException):
            encoder.decode_abbr("a-a-a-a-a")

    def test_round_trip_still_works_at_every_min_phrase_size(self):
        for min_phrase_size in (1, 2, 3, 4):
            encoder = WordEncoder(self.wordlist, min_phrase_size=min_phrase_size)
            for number in range(0, encoder.get_max()):
                encoded = encoder.encode(number)
                self.assertEqual(encoder.decode(encoded.keyphrase), number)
                self.assertEqual(encoder.decode_abbr(encoded.abbr), number)


if __name__ == "__main__":
    unittest.main()
