from datetime import datetime, timezone
import time
from typing import List
import unittest
import concurrent.futures

from jazzy_fish.generator import (
    Generator,
    GeneratorException,
    Resolution,
)


class TestGenerator(unittest.TestCase):
    def test_generate_id(self):
        epoch = datetime(2024, 5, 30, tzinfo=timezone.utc).timestamp()

        generator = Generator(
            epoch=epoch,
            machine_ids=[1],
            machine_id_bits=3,
            sequence_bits=1,
            resolution=Resolution.MILLISECOND,
        )

        self.assertGreater(generator.next_id(), 3295599666)

    def test_ids_are_increasing(self):
        epoch = datetime(2024, 5, 30, tzinfo=timezone.utc).timestamp()
        batch_size = 1000

        generator = Generator(
            epoch=epoch,
            machine_ids=[1],
            machine_id_bits=3,
            sequence_bits=1,
            resolution=Resolution.MILLISECOND,
        )

        results = list()
        for i in range(0, batch_size):
            results.append(generator.next_id())

        for i in range(1, batch_size):
            self.assertGreater(results[i], results[i - 1])

    def test_generator_is_threadsafe(self):
        result = parameterized_generator(
            num_threads=10, batch_size=1000, machine_ids=[0]
        )

        # Check for uniqueness of the generated IDs
        unique_ids = set(result)
        self.assertEqual(len(unique_ids), len(result))

    def test_generator_does_not_overlap_machines(self):
        result1 = parameterized_generator(
            num_threads=10, batch_size=1000, machine_ids=[0], machine_id_bits=1
        )
        result2 = parameterized_generator(
            num_threads=10, batch_size=1000, machine_ids=[1], machine_id_bits=1
        )
        all_results = result1 + result2

        # Check for uniqueness of the generated IDs
        unique_ids = set(all_results)
        self.assertEqual(len(unique_ids), len(all_results))

    def test_guarded_machine_id(self):
        with self.assertRaises(GeneratorException):
            Generator(
                epoch=datetime.now(tz=timezone.utc).timestamp(),
                machine_ids=[2],  # Invalid, since 2^1-1 = 1; 2>1
                machine_id_bits=1,
                sequence_bits=1,
                resolution=Resolution.SECOND,
            )

    def test_single_machine_id(self):
        result = parameterized_generator(
            num_threads=10, batch_size=100, machine_ids=[0], machine_id_bits=0
        )

        # Check for uniqueness of the generated IDs
        unique_ids = set(result)
        self.assertEqual(len(unique_ids), len(result))

    def test_single_sequence(self):
        result = parameterized_generator(
            num_threads=10, batch_size=100, machine_ids=[0], sequence_bits=0
        )

        # Check for uniqueness of the generated IDs
        unique_ids = set(result)
        self.assertEqual(len(unique_ids), len(result))


def generate_ids(generator, num_ids):
    ids = []
    for _ in range(num_ids):
        ids.append(generator.next_id())
    return ids


def parameterized_generator(
    num_threads,
    batch_size,
    machine_ids=[0],
    machine_id_bits=1,
    sequence_bits=1,
    resolution=Resolution.MILLISECOND,
) -> List[int]:
    epoch = time.time()

    generator = Generator(
        epoch=epoch,
        machine_ids=machine_ids,
        machine_id_bits=machine_id_bits,
        sequence_bits=sequence_bits,
        resolution=resolution,
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(generate_ids, generator, batch_size)
            for _ in range(num_threads)
        ]

        all_ids = []
        for future in concurrent.futures.as_completed(futures):
            all_ids.extend(future.result())
        return all_ids


if __name__ == "__main__":
    unittest.main()
