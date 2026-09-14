import sys
import threading
import time
import unittest
import warnings
from typing import List

from jazzy_fish.generator import Generator, Resolution, ThreadSafeGenerator


def _collect(generator: Generator, threads: int, per_thread: int) -> List[int]:
    collected: List[List[int]] = []
    lock = threading.Lock()

    def worker() -> None:
        ids = [generator.next_id() for _ in range(per_thread)]
        with lock:
            collected.append(ids)

    workers = [threading.Thread(target=worker) for _ in range(threads)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    return [i for batch in collected for i in batch]


class TestGeneratorConcurrency(unittest.TestCase):
    def test_generator_does_not_emit_duplicates_under_threads(self):
        # Before the lock moved into Generator this produced roughly 0.2% duplicates
        # at the default switch interval, and 43% at a short one.
        generator = Generator(
            epoch=time.time(),
            resolution=Resolution.MILLISECOND,
            machine_ids=[0],
            machine_id_bits=0,
            sequence_bits=22,
        )
        ids = _collect(generator, threads=8, per_thread=25_000)
        self.assertEqual(len(set(ids)), len(ids))

    def test_generator_does_not_emit_duplicates_at_a_short_switch_interval(self):
        # A short switch interval preempts threads mid-call, which is what made the
        # race reproducible in the first place.
        previous = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        try:
            generator = Generator(
                epoch=time.time(),
                resolution=Resolution.MILLISECOND,
                machine_ids=[0],
                machine_id_bits=0,
                sequence_bits=22,
            )
            ids = _collect(generator, threads=8, per_thread=5_000)
            self.assertEqual(len(set(ids)), len(ids))
        finally:
            sys.setswitchinterval(previous)

    def test_thread_safe_generator_still_works_and_warns(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            generator = ThreadSafeGenerator(
                epoch=time.time(),
                resolution=Resolution.MILLISECOND,
                machine_ids=[0],
                machine_id_bits=0,
                sequence_bits=10,
            )
        self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))
        self.assertIsInstance(generator.next_id(), int)
        self.assertIsInstance(generator, Generator)


if __name__ == "__main__":
    unittest.main()
