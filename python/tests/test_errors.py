import unittest

import jazzy_fish
from jazzy_fish.encoder import EncoderException, WordEncoder, Wordlist


class TestErrorContract(unittest.TestCase):
    def setUp(self):
        adverbs = ["absurdly", "busily", "capably"]
        verbs = ["abandoned", "bearded", "checked"]
        adjectives = ["able", "blond", "chubby"]
        nouns = ["apple", "bird", "cat", "dog"]
        self.wordlist = Wordlist(
            "0_NOVERIFY", [adverbs, verbs, adjectives, nouns], verify_checksum=False
        )
        self.encoder = WordEncoder(self.wordlist, min_phrase_size=1)

    def test_unknown_word_raises_encoder_exception(self):
        with self.assertRaises(EncoderException) as ctx:
            self.encoder.decode("absurdly-abandoned-able-NOPE")
        self.assertIn("NOPE", str(ctx.exception))

    def test_unknown_abbreviation_raises_encoder_exception(self):
        with self.assertRaises(EncoderException) as ctx:
            self.encoder.decode_abbr("a-a-a-z")
        self.assertIn("z", str(ctx.exception))

    def test_empty_input_raises_encoder_exception(self):
        with self.assertRaises(EncoderException):
            self.encoder.decode("")
        with self.assertRaises(EncoderException):
            self.encoder.decode_abbr("")

    def test_error_names_the_position_of_the_bad_part(self):
        with self.assertRaises(EncoderException) as ctx:
            self.encoder.decode("NOPE-abandoned-able-apple")
        self.assertIn("position 0", str(ctx.exception))

    def test_exceptions_are_reachable_from_the_package(self):
        # The documented entry point is `from jazzy_fish import ...`; a caller
        # cannot honour the error contract if the types are not exported.
        self.assertTrue(hasattr(jazzy_fish, "EncoderException"))
        self.assertTrue(hasattr(jazzy_fish, "GeneratorException"))
        self.assertIn("EncoderException", jazzy_fish.__all__)
        self.assertIn("GeneratorException", jazzy_fish.__all__)
        self.assertIs(jazzy_fish.EncoderException, EncoderException)

    def test_round_trip_is_unchanged(self):
        for min_phrase_size in (1, 2, 3, 4):
            encoder = WordEncoder(self.wordlist, min_phrase_size=min_phrase_size)
            for number in range(0, encoder.get_max()):
                encoded = encoder.encode(number)
                self.assertEqual(encoder.decode(encoded.keyphrase), number)
                self.assertEqual(encoder.decode_abbr(encoded.abbr), number)


if __name__ == "__main__":
    unittest.main()
