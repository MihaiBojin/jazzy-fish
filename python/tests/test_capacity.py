import time
import unittest
from datetime import datetime, timezone

from jazzy_fish.encoder import EncoderException, WordEncoder, Wordlist, check_capacity
from jazzy_fish.generator import Generator, Resolution

EPOCH_2024 = datetime(2024, 5, 30, tzinfo=timezone.utc).timestamp()


def _encoder(name: str = "012_8562fb9") -> WordEncoder:
    return WordEncoder(Wordlist.load(f"resources/{name}", "jazzy_fish"), 4)


def _generator(**overrides: object) -> Generator:
    kwargs: dict = {
        "epoch": EPOCH_2024,
        "resolution": Resolution.MILLISECOND,
        "machine_ids": [0],
        "machine_id_bits": 0,
        "sequence_bits": 0,
    }
    kwargs.update(overrides)
    return Generator(**kwargs)


class TestCapacity(unittest.TestCase):
    def test_the_documented_configuration_passes(self):
        check_capacity(_generator(), _encoder())

    def test_bits_shorten_the_lifetime_until_it_fails(self):
        # Every machine/sequence bit halves the runway. The configuration used in
        # test_generator.py exhausts 012_8562fb9 in 2026.
        with self.assertRaises(EncoderException) as ctx:
            check_capacity(
                _generator(machine_id_bits=3, sequence_bits=1, machine_ids=[1]),
                _encoder(),
            )
        self.assertIn("outgrows", str(ctx.exception))

    def test_unix_epoch_with_the_default_wordlist_is_already_past(self):
        # Millisecond time since 1970 outgrew this wordlist in 2008.
        with self.assertRaises(EncoderException):
            check_capacity(_generator(epoch=0.0), _encoder())

    def test_a_larger_wordlist_rescues_the_same_configuration(self):
        check_capacity(_generator(epoch=0.0), _encoder("01234_f233650"))

    def test_a_coarser_resolution_rescues_the_same_configuration(self):
        check_capacity(_generator(epoch=0.0, resolution=Resolution.SECOND), _encoder())

    def test_exhausts_at_matches_the_arithmetic(self):
        generator = _generator(machine_id_bits=3, sequence_bits=1, machine_ids=[1])
        capacity = _encoder().get_max()
        exhausted = generator.exhausts_at(capacity)
        expected = (generator.epoch_millis + (capacity >> 4)) / 1000
        self.assertAlmostEqual(exhausted, expected, places=3)

    def test_max_id_at_bounds_the_real_generator(self):
        generator = _generator(sequence_bits=8)
        now = time.time()
        self.assertLessEqual(generator.next_id(), generator.max_id_at(now + 1))


if __name__ == "__main__":
    unittest.main()
