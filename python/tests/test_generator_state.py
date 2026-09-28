from concurrent.futures import ThreadPoolExecutor
from itertools import chain, repeat
import time
import unittest
from unittest.mock import patch

from jazzy_fish.generator import Generator, Resolution, ThreadSafeGenerator


class TestGeneratorState(unittest.TestCase):
    @patch("jazzy_fish.generator.time.sleep")
    def test_clock_boundaries(self, sleep):
        cases = [
            ("same_unit", 2, [5, 5, 5, 5], [20, 21, 22, 23]),
            ("new_unit", 2, [5, 5, 6], [20, 21, 24]),
            ("exhausted_sequence", 1, [5, 5, 5, 5, 6], [10, 11, 12]),
            ("clock_rollback", 2, [5, 4, 5, 6], [20, 24]),
            ("zero_bits", 0, [5, 5, 6], [5, 6]),
        ]
        for cls in (Generator, ThreadSafeGenerator):
            for name, bits, clock, expected in cases:
                with self.subTest(generator=cls.__name__, case=name):
                    generator = cls(0, Resolution.SECOND, [0], 0, bits)
                    generator.current_time = chain(clock, repeat(clock[-1])).__next__
                    self.assertEqual([generator.next_id() for _ in expected], expected)

    def test_round_robin_tracks_each_machine_sequence(self):
        for cls in (Generator, ThreadSafeGenerator):
            with self.subTest(generator=cls.__name__):
                generator = cls(0, Resolution.SECOND, [0, 1], 1, 2)
                generator.current_time = lambda: 5
                self.assertEqual(
                    [generator.next_id() for _ in range(8)],
                    [40, 44, 41, 45, 42, 46, 43, 47],
                )

    @patch("jazzy_fish.generator.time.sleep")
    def test_zero_sequence_bits_wait_per_machine(self, sleep):
        for cls in (Generator, ThreadSafeGenerator):
            with self.subTest(generator=cls.__name__):
                generator = cls(0, Resolution.SECOND, [0, 1], 1, 0)
                generator.current_time = chain([5, 5, 5], repeat(6)).__next__
                self.assertEqual(
                    [generator.next_id() for _ in range(4)], [10, 11, 12, 13]
                )

    def test_clock_can_be_replaced_after_generation(self):
        for cls in (Generator, ThreadSafeGenerator):
            with self.subTest(generator=cls.__name__):
                generator = cls(0, Resolution.SECOND, [0], 0, 2)
                generator.current_time = lambda: 5
                self.assertEqual(generator.next_id(), 20)
                generator.current_time = lambda: 7
                self.assertEqual(generator.next_id(), 28)

    def test_resolution_assignment_updates_generation_and_capacity(self):
        for cls in (Generator, ThreadSafeGenerator):
            with self.subTest(generator=cls.__name__):
                generator = cls(0, Resolution.SECOND, [0], 0, 2)
                generator.resolution = Resolution.MINUTE
                generator.current_time = lambda: 120
                self.assertEqual(generator.next_id(), 8)
                self.assertEqual(generator.max_id_at(120), 11)
                self.assertEqual(generator.exhausts_at(16), 240)

    def test_machine_ids_partition_the_identifier_space(self):
        generators = [
            Generator(0, Resolution.SECOND, [machine], 1, 2) for machine in (0, 1)
        ]
        for generator in generators:
            generator.current_time = lambda: 5
        values = [g.next_id() for g in generators for _ in range(4)]
        self.assertEqual(sorted(values), list(range(40, 48)))

    def test_machine_list_can_include_another_configured_machine(self):
        for cls in (Generator, ThreadSafeGenerator):
            with self.subTest(generator=cls.__name__):
                generator = cls(0, Resolution.SECOND, [0], 1, 2)
                generator.current_time = lambda: 5
                self.assertEqual(generator.next_id(), 40)
                generator.machine_ids.append(1)
                self.assertEqual(generator.next_id(), 41)
                self.assertEqual(generator.next_id(), 44)

    def test_shared_generator_serializes_a_clock_that_releases_the_gil(self):
        generator = ThreadSafeGenerator(0, Resolution.SECOND, [0], 0, 16)

        def clock():
            time.sleep(0)
            return 5

        generator.current_time = clock

        def collect():
            return [generator.next_id() for _ in range(1000)]

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(collect) for _ in range(4)]
            values = [value for future in futures for value in future.result()]
        self.assertEqual(sorted(values), list(range(327680, 331680)))


if __name__ == "__main__":
    unittest.main()
