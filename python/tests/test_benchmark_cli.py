import json
from contextlib import contextmanager, redirect_stdout
from io import StringIO
import os
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
        functions = runpy.run_path(str(ROOT / "benchmarks/benchmark.py"))
        metadata = functions["runtime_metadata"]
        with patch.dict(
            metadata.__globals__, {"os": SimpleNamespace(cpu_count=lambda: None)}
        ):
            result = metadata()
        self.assertEqual(result["available_cpus"], 1)
        self.assertIsNone(result["load_average"])
        self.assertNotIn("executable", result)

    def test_private_workers_can_use_more_than_sixteen_machine_ids(self):
        functions = runpy.run_path(str(ROOT / "benchmarks/benchmark.py"))
        result = functions["execute"](
            {
                "source": str(ROOT / "python/src/jazzy_fish/generator.py"),
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

    def test_run_from_another_directory_records_comparison_without_local_paths(self):
        functions = runpy.run_path(str(ROOT / "benchmarks/run.py"))

        @contextmanager
        def provision(versions):
            self.assertEqual(versions, ["3.14.7"])
            yield {"3.14.7": sys.executable}

        with tempfile.TemporaryDirectory(prefix="jazzy benchmark ") as directory:
            output = Path(directory) / "results"
            baseline = Path(directory) / "baseline.py"
            source = (ROOT / "python/src/jazzy_fish/generator.py").read_text()
            baseline.write_text(
                source.replace("def threadsafe(", "def fixture_threadsafe(")
            )
            arguments = [
                "--python",
                "3.14.7",
                "--threads",
                "2",
                "--repeats",
                "1",
                "--calls",
                "1000",
                "--correctness-calls",
                "1000",
                "--baseline",
                str(baseline),
                "--output",
                str(output),
            ]
            previous = Path.cwd()
            try:
                os.chdir(directory)
                with (
                    patch.object(functions["environment"], "provision", provision),
                    redirect_stdout(StringIO()),
                ):
                    functions["main"](arguments)
            finally:
                os.chdir(previous)
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
            self.assertTrue(
                all(
                    row["duplicates"] == 0 and row["within_worker_decreases"] == 0
                    for row in checked
                )
            )
            for path in output.rglob("*"):
                if path.is_file():
                    content = path.read_text()
                    for forbidden in (
                        str(ROOT),
                        str(Path.home()),
                        directory,
                        sys.executable,
                    ):
                        self.assertNotIn(forbidden, content, path.name)
            config = json.loads((output / "config.json").read_text())
            self.assertEqual(list(config["interpreters"].values()), ["3.14.7"])
            self.assertTrue((output / "summary.json").is_file())
            self.assertTrue((output / "snapshots/current.py.txt").is_file())
            self.assertIn("GIL", (output / "README.md").read_text())
            with patch.object(functions["environment"], "provision") as setup:
                with self.assertRaises(SystemExit):
                    functions["main"](arguments)
                setup.assert_not_called()

    def test_interpreter_paths_are_rejected_before_setup(self):
        command = [
            sys.executable,
            str(ROOT / "benchmarks/run.py"),
            "--python",
            sys.executable,
            "--output",
            "unused-output",
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("use a Python version", result.stderr)


if __name__ == "__main__":
    unittest.main()
