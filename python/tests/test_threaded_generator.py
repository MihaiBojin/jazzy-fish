from concurrent.futures import ThreadPoolExecutor
import threading
import time
import unittest

from jazzy_fish.generator import Generator, GeneratorException, Resolution


class TestThreadedGenerator(unittest.TestCase):
    def test_default_groups_assign_six_simultaneous_callers_distinct_machine_ids(self):
        generator = Generator.threadsafe(0, Resolution.SECOND, list(range(6)), 3, 20)
        generator.current_time = lambda: 5
        barrier = threading.Barrier(6)

        def worker() -> int:
            barrier.wait(timeout=10)
            return generator.next_id()

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(worker) for _ in range(6)]
            identifiers = [future.result(timeout=10) for future in futures]

        self.assertEqual(len(set(identifiers)), 6)
        self.assertEqual(
            {(identifier >> 20) & 7 for identifier in identifiers}, set(range(6))
        )

    def test_explicit_group_count_partitions_machine_ids_in_caller_order(self):
        generator = Generator.threadsafe(
            0, Resolution.SECOND, [3, 1, 2, 0], 2, 4, threads=2
        )
        generator.current_time = lambda: 5
        barrier = threading.Barrier(2)

        def worker() -> list[int]:
            barrier.wait(timeout=10)
            return [(generator.next_id() >> 4) & 3 for _ in range(2)]

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(worker) for _ in range(2)]
            machine_sequences = [future.result(timeout=10) for future in futures]

        self.assertCountEqual(machine_sequences, [[3, 2], [1, 0]])

    def test_group_count_must_be_a_positive_integer(self):
        for count in (0, -1, 1.5, "2", True, None):
            with self.subTest(count=count):
                with self.assertRaises(GeneratorException):
                    Generator.threadsafe(
                        0,
                        Resolution.SECOND,
                        [0, 1],
                        1,
                        4,
                        threads=count,  # type: ignore[arg-type]
                    )

    def test_group_count_cannot_exceed_distinct_machine_ids(self):
        with self.assertRaises(GeneratorException):
            Generator.threadsafe(0, Resolution.SECOND, [0, 0, 1], 1, 4, threads=3)

    def test_machine_id_bit_width_is_still_validated(self):
        with self.assertRaises(GeneratorException):
            Generator.threadsafe(0, Resolution.SECOND, [0, 4], 2, 4, threads=2)

    def test_oversubscribed_callers_share_groups_without_duplicate_ids(self):
        generator = Generator.threadsafe(0, Resolution.SECOND, [0, 1], 1, 16, threads=2)

        def clock() -> float:
            time.sleep(0)
            return 5

        generator.current_time = clock
        barrier = threading.Barrier(12)

        def worker() -> list[int]:
            barrier.wait(timeout=10)
            return [generator.next_id() for _ in range(100)]

        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = [executor.submit(worker) for _ in range(12)]
            identifiers = [
                value for future in futures for value in future.result(timeout=10)
            ]

        self.assertEqual(len(identifiers), 1200)
        self.assertEqual(len(set(identifiers)), 1200)
        self.assertEqual({(identifier >> 16) & 1 for identifier in identifiers}, {0, 1})

    def test_replacement_threads_keep_group_sequence_state(self):
        generator = Generator.threadsafe(0, Resolution.SECOND, [0, 1], 1, 10, threads=2)
        generator.current_time = lambda: 5

        def wave() -> list[int]:
            barrier = threading.Barrier(2)

            def worker() -> list[int]:
                barrier.wait(timeout=10)
                return [generator.next_id() for _ in range(100)]

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(worker) for _ in range(2)]
                return [
                    value for future in futures for value in future.result(timeout=10)
                ]

        identifiers = wave() + wave()
        self.assertEqual(len(set(identifiers)), 400)
        for machine_id in (0, 1):
            sequences = sorted(
                identifier & 1023
                for identifier in identifiers
                if (identifier >> 10) & 1 == machine_id
            )
            self.assertEqual(sequences, list(range(200)))

    def test_clock_reassignment_reaches_every_group(self):
        generator = Generator.threadsafe(0, Resolution.SECOND, [0, 1], 1, 4, threads=2)
        generator.current_time = lambda: 5
        self.assertEqual(generator.next_id(), 160)

        with ThreadPoolExecutor(max_workers=1) as executor:
            self.assertEqual(executor.submit(generator.next_id).result(timeout=10), 176)
            generator.current_time = lambda: 7
            other = executor.submit(generator.next_id).result(timeout=10)

        self.assertEqual(generator.next_id(), 224)
        self.assertEqual(other, 240)

    def test_resolution_reassignment_reaches_every_group_and_capacity(self):
        generator = Generator.threadsafe(0, Resolution.SECOND, [0, 1], 1, 2, threads=2)
        generator.current_time = lambda: 5
        self.assertEqual(generator.next_id(), 40)

        with ThreadPoolExecutor(max_workers=1) as executor:
            self.assertEqual(executor.submit(generator.next_id).result(timeout=10), 44)
            generator.resolution = Resolution.MILLISECOND
            other = executor.submit(generator.next_id).result(timeout=10)

        self.assertEqual(generator.next_id(), 40000)
        self.assertEqual(other, 40004)
        self.assertEqual(generator.max_id_at(5), 40007)
        self.assertEqual(generator.exhausts_at(32), 0.004)

    def test_clock_attribute_error_propagates_once_per_call(self):
        generator = Generator.threadsafe(0, Resolution.SECOND, [0, 1], 1, 4, threads=2)
        calls = 0

        def clock() -> float:
            nonlocal calls
            calls += 1
            raise AttributeError("clock failed")

        generator.current_time = clock
        for expected_calls in (1, 2):
            with self.assertRaisesRegex(AttributeError, "clock failed"):
                generator.next_id()
            self.assertEqual(calls, expected_calls)


if __name__ == "__main__":
    unittest.main()
