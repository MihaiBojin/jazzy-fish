from datetime import datetime, timezone
import unittest

from jazzy_fish.encoder import WordEncoder, Wordlist
from jazzy_fish.generator import Generator, Resolution


class TestIntegrationGenerateSequence(unittest.TestCase):
    def test_can_generate(self):
        # ARRANGE
        epoch = datetime(2024, 5, 30, tzinfo=timezone.utc).timestamp()

        # Configure the generator
        generator = Generator(
            epoch=epoch,
            machine_ids=[0],
            machine_id_bits=0,
            sequence_bits=0,
            resolution=Resolution.MILLISECOND,
        )

        # Configure the encoder
        wordlist = Wordlist.load("resources/012_80a1774", "jazzy_fish")
        encoder = WordEncoder(wordlist, min_phrase_size=4)

        # ACT
        id = generator.next_id()
        encoded = encoder.encode(id)

        # ASSERT
        self.assertEqual(len(encoded.keyphrase.split(encoder.separator)), 4)

        got = encoder.decode(encoded.keyphrase)
        self.assertEqual(got, id)

        got2 = encoder.decode_abbr(encoded.abbr)
        self.assertEqual(got2, id)


if __name__ == "__main__":
    unittest.main()
