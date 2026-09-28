import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


class TestBenchmarkCLI(unittest.TestCase):
    def test_metadata_without_load_average_or_known_cpu_count(self):
        functions = runpy.run_path(str(ROOT / "benchmarks/pr99/benchmark.py"))
        metadata = functions["runtime_metadata"]
        with patch.dict(
            metadata.__globals__, {"os": SimpleNamespace(cpu_count=lambda: None)}
        ):
            result = metadata()
        self.assertEqual(result["available_cpus"], 1)
        self.assertIsNone(result["load_average"])

    def test_private_workers_can_use_more_than_sixteen_machine_ids(self):
        functions = runpy.run_path(str(ROOT / "benchmarks/pr99/benchmark.py"))
        result = functions["execute"](
            {
                "revision": "file:" + str(ROOT / "python/src/jazzy_fish/generator.py"),
                "kind": "correctness",
                "profile": "threaded",
                "variant": "private",
                "threads": 17,
                "machine_id_bits": 5,
                "calls": 1700,
                "worker_thread": True,
            }
        )
        self.assertEqual(result["duplicates"], 0)
        self.assertEqual(result["configuration"]["machine_id_bits"], 5)

    def test_run_from_another_directory_records_comparison_and_correctness(self):
        with tempfile.TemporaryDirectory(prefix="jazzy benchmark ") as directory:
            output = Path(directory) / "results"
            command = [
                sys.executable,
                str(ROOT / "benchmarks/run.py"),
                "--python",
                sys.executable,
                "--threads",
                "2",
                "--repeats",
                "1",
                "--calls",
                "1000",
                "--correctness-calls",
                "1000",
                "--baseline",
                str(ROOT / "benchmarks/refactor/snapshots/baseline.py.txt"),
                "--output",
                str(output),
            ]
            completed = subprocess.run(
                command, cwd=directory, capture_output=True, text=True, timeout=60
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            rows = [
                json.loads(line)
                for line in (output / "results.jsonl").read_text().splitlines()
            ]
            self.assertEqual(
                {row["implementation"] for row in rows}, {"baseline", "current"}
            )
            self.assertEqual({row["threads"] for row in rows}, {1, 2})
            self.assertTrue(
                any(
                    row["variant"] == "factory"
                    for row in rows
                    if row["implementation"] == "current"
                )
            )
            self.assertFalse(
                any(
                    row["variant"] == "factory"
                    for row in rows
                    if row["implementation"] == "baseline"
                )
            )
            checked = [row for row in rows if row["kind"] == "correctness"]
            self.assertTrue(checked)
            self.assertTrue(all(row["duplicates"] == 0 for row in checked))
            self.assertTrue(all(row["within_worker_decreases"] == 0 for row in checked))
            report = (output / "README.md").read_text()
            self.assertIn("Baseline", report)
            self.assertIn("Current", report)
            self.assertIn("GIL", report)
            self.assertIn("sample", report)
            self.assertTrue((output / "summary.json").is_file())
            self.assertTrue((output / "snapshots/current.py.txt").is_file())

            repeated = subprocess.run(
                command, cwd=directory, capture_output=True, text=True, timeout=10
            )
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("already exists", repeated.stderr)


if __name__ == "__main__":
    unittest.main()
