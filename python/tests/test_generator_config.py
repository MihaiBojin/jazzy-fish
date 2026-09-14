import time
import unittest

from jazzy_fish.generator import Generator, GeneratorException, Resolution


def _generator(**overrides: object) -> Generator:
    kwargs: dict = {
        "epoch": 0.0,
        "resolution": Resolution.MILLISECOND,
        "machine_ids": [0],
        "machine_id_bits": 0,
        "sequence_bits": 0,
    }
    kwargs.update(overrides)
    return Generator(**kwargs)


class TestGeneratorConfiguration(unittest.TestCase):
    def test_machine_id_order_is_the_callers_order(self):
        # list(set(...)) reordered by hash: [10, 5, 1] rotated as [1, 10, 5].
        for machine_ids in ([3, 1, 2], [2, 1, 0], [10, 5, 1], [1, 17, 33]):
            generator = _generator(machine_ids=machine_ids, machine_id_bits=6)
            self.assertEqual(generator.machine_ids, machine_ids)

    def test_duplicate_machine_ids_are_still_removed(self):
        generator = _generator(machine_ids=[2, 1, 2, 1, 0], machine_id_bits=2)
        self.assertEqual(generator.machine_ids, [2, 1, 0])

    def test_rotation_follows_the_callers_order(self):
        generator = _generator(machine_ids=[3, 1, 2], machine_id_bits=2)
        rotation = [generator._next_machine_id() for _ in range(6)]
        self.assertEqual(rotation, [3, 1, 2, 3, 1, 2])

    def test_negative_bit_counts_are_rejected(self):
        # These used to construct fine and fail later with
        # "ValueError: negative shift count" from inside next_id().
        with self.assertRaises(GeneratorException):
            _generator(machine_id_bits=-1)
        with self.assertRaises(GeneratorException):
            _generator(sequence_bits=-1)

    def test_millisecond_epochs_round_trip_exactly(self):
        # int(1.001 * 1000) is 1000, so truncation lost a millisecond for most
        # fractional values. Every whole millisecond must survive the conversion.
        for millis in range(0, 3000):
            generator = _generator(epoch=millis / 1000)
            self.assertEqual(generator.epoch_millis, millis)

    def test_clock_reading_rounds_rather_than_truncates(self):
        generator = _generator(epoch=0.0, resolution=Resolution.MILLISECOND)
        for millis in (1001, 1003, 2007, 123_456_789):
            generator.current_time = lambda m=millis: m / 1000  # type: ignore[misc]
            self.assertEqual(generator._current_time(), millis)

    def test_ids_are_still_unique(self):
        generator = _generator(epoch=time.time(), sequence_bits=12)
        ids = [generator.next_id() for _ in range(5000)]
        self.assertEqual(len(set(ids)), len(ids))


if __name__ == "__main__":
    unittest.main()
