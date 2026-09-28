from contextlib import ExitStack
from pathlib import Path
import runpy
import subprocess
import unittest
from typing import Any
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


class TestBenchmarkEnvironment(unittest.TestCase):
    def load_environment(self) -> dict[str, Any]:
        source = ROOT / "benchmarks/environment.py"
        self.assertTrue(source.exists(), "Missing fresh-runtime provisioner")
        return runpy.run_path(str(source))

    def test_each_run_installs_into_a_new_directory_and_cleans_up(self):
        functions = self.load_environment()
        seen = []

        def command(args, **kwargs):
            env = kwargs["env"]
            self.assertNotIn("PYTHONPATH", env)
            self.assertNotIn("VIRTUAL_ENV", env)
            self.assertNotIn("UV_PYTHON", env)
            root = Path(env["UV_PYTHON_INSTALL_DIR"]).parent
            seen.append((args, root, env))
            output = str(root / "pythons" / "python") if "find" in args else ""
            return subprocess.CompletedProcess(args, 0, output, "")

        roots = []
        with ExitStack() as stack:
            stack.enter_context(
                patch.dict(
                    "os.environ",
                    {
                        "PYTHONPATH": "/injected",
                        "UV_PYTHON": "/existing",
                        "VIRTUAL_ENV": "/active",
                    },
                )
            )
            stack.enter_context(
                patch.object(functions["subprocess"], "run", side_effect=command)
            )
            for _ in range(2):
                with functions["provision"](["3.12.14"]) as runtimes:
                    executable = Path(runtimes["3.12.14"])
                    root = next(root for _, root, _ in reversed(seen))
                    self.assertTrue(root.is_dir())
                    self.assertTrue(executable.is_relative_to(root))
                    roots.append(root)
                self.assertFalse(root.exists())
        self.assertNotEqual(*roots)
        self.assertEqual(
            sum("install" in args and "--no-cache-dir" in args for args, _, _ in seen),
            2,
        )
        self.assertEqual(
            sum("--no-bin" in args and "--no-registry" in args for args, _, _ in seen),
            2,
        )

    def test_interruption_during_measurement_removes_the_environment(self):
        functions = self.load_environment()
        roots = []

        def command(args, **kwargs):
            root = Path(kwargs["env"]["UV_PYTHON_INSTALL_DIR"]).parent
            roots.append(root)
            output = str(root / "pythons" / "python") if "find" in args else ""
            return subprocess.CompletedProcess(args, 0, output, "")

        with patch.object(functions["subprocess"], "run", side_effect=command):
            with self.assertRaises(KeyboardInterrupt):
                with functions["provision"](["3.12.14"]):
                    raise KeyboardInterrupt
        self.assertFalse(roots[-1].exists())

    def test_failed_setup_removes_the_temporary_directory(self):
        functions = self.load_environment()
        roots = []

        def fail(args, **kwargs):
            roots.append(Path(kwargs["env"]["UV_PYTHON_INSTALL_DIR"]).parent)
            raise subprocess.CalledProcessError(1, args)

        with patch.object(functions["subprocess"], "run", side_effect=fail):
            with self.assertRaises(subprocess.CalledProcessError):
                with functions["provision"](["3.12.14"]):
                    self.fail("Setup failure must not yield an environment")
        self.assertFalse(roots[0].exists())


if __name__ == "__main__":
    unittest.main()
