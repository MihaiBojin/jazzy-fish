import resource
import time
import unittest

from jazzy_fish.generator import Generator, GeneratorException, Resolution


def _cpu_seconds() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime


class TestGeneratorWaiting(unittest.TestCase):
    def test_future_epoch_is_rejected(self):
        # Previously next_id() spun at 100% CPU until wall-clock reached the epoch:
        # an epoch one hour out meant an hour of spinning, with no error.
        with self.assertRaises(GeneratorException) as ctx:
            Generator(
                epoch=time.time() + 3600,
                resolution=Resolution.MILLISECOND,
                machine_ids=[0],
                machine_id_bits=0,
                sequence_bits=0,
            )
        self.assertIn("future", str(ctx.exception))

    def test_current_epoch_is_accepted(self):
        generator = Generator(
            epoch=time.time(),
            resolution=Resolution.MILLISECOND,
            machine_ids=[0],
            machine_id_bits=0,
            sequence_bits=0,
        )
        self.assertIsInstance(generator.next_id(), int)

    def test_exhausted_sequence_waits_without_burning_a_core(self):
        # sequence_bits=0 means one id per time unit, so the second call must wait
        # out the rest of the second. That wait used to be a hot spin.
        generator = Generator(
            epoch=time.time(),
            resolution=Resolution.SECOND,
            machine_ids=[0],
            machine_id_bits=0,
            sequence_bits=0,
        )
        generator.next_id()

        cpu_before = _cpu_seconds()
        wall_before = time.monotonic()
        generator.next_id()
        wall_elapsed = time.monotonic() - wall_before
        cpu_elapsed = _cpu_seconds() - cpu_before

        self.assertGreater(wall_elapsed, 0.05, "should actually have waited")
        # A spin burns ~100% of a core; sleeping burns almost none.
        self.assertLess(
            cpu_elapsed,
            wall_elapsed * 0.5,
            f"used {cpu_elapsed:.3f}s CPU over {wall_elapsed:.3f}s wall",
        )

    def test_ids_stay_unique_and_increasing_across_a_wait(self):
        generator = Generator(
            epoch=time.time(),
            resolution=Resolution.MILLISECOND,
            machine_ids=[0],
            machine_id_bits=0,
            sequence_bits=1,
        )
        ids = [generator.next_id() for _ in range(24)]
        self.assertEqual(len(set(ids)), len(ids))
        for previous, current in zip(ids, ids[1:]):
            self.assertGreater(current, previous)


if __name__ == "__main__":
    unittest.main()
