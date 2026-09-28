import sys
from concurrent.futures import ThreadPoolExecutor
import time
import unittest
import warnings
from typing import List

from jazzy_fish.generator import Generator, Resolution, ThreadSafeGenerator


def _collect(generator: Generator, threads: int, per_thread: int) -> List[int]:
    def worker() -> List[int]:
        return [generator.next_id() for _ in range(per_thread)]

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(worker) for _ in range(threads)]
        return [value for future in futures for value in future.result()]


class TestGeneratorConcurrency(unittest.TestCase):
    def test_thread_safe_generator_does_not_emit_duplicates_under_threads(self):
        generator = ThreadSafeGenerator(
            epoch=time.time(),
            resolution=Resolution.MILLISECOND,
            machine_ids=[0],
            machine_id_bits=0,
            sequence_bits=22,
        )
        ids = _collect(generator, threads=8, per_thread=25_000)
        self.assertEqual(len(ids), 200_000)
        self.assertEqual(len(set(ids)), len(ids))

    def test_thread_safe_generator_handles_a_short_switch_interval(self):
        previous = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        try:
            generator = ThreadSafeGenerator(
                epoch=time.time(),
                resolution=Resolution.MILLISECOND,
                machine_ids=[0],
                machine_id_bits=0,
                sequence_bits=22,
            )
            ids = _collect(generator, threads=8, per_thread=5_000)
            self.assertEqual(len(ids), 40_000)
            self.assertEqual(len(set(ids)), len(ids))
        finally:
            sys.setswitchinterval(previous)

    def test_thread_safe_generator_has_no_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            generator = ThreadSafeGenerator(
                epoch=time.time(),
                resolution=Resolution.MILLISECOND,
                machine_ids=[0],
                machine_id_bits=0,
                sequence_bits=10,
            )
        self.assertFalse(
            any(issubclass(w.category, DeprecationWarning) for w in caught)
        )
        self.assertIsInstance(generator.next_id(), int)
        self.assertIsInstance(generator, Generator)


if __name__ == "__main__":
    unittest.main()
