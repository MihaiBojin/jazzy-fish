"""Provision disposable Python runtimes without using existing installations."""

import os
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

UV_VERSION = "0.12.11"
DEFAULT_PYTHONS = ("3.12.14", "3.13.15", "3.14.7", "3.13.15t", "3.14.7t")


def clean_environment() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("PYTHON", "UV_", "PIP_"))
        and key not in ("VIRTUAL_ENV", "CONDA_PREFIX", "__PYVENV_LAUNCHER__")
    }


def python_in(directory: Path) -> Path:
    return directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


@contextmanager
def provision(versions: list[str]) -> Iterator[dict[str, str]]:
    with TemporaryDirectory(prefix="jazzy-benchmark-") as directory:
        root = Path(directory).resolve()
        env = clean_environment()
        env.update(
            UV_PYTHON_INSTALL_DIR=str(root / "pythons"),
            UV_CACHE_DIR=str(root / "cache"),
            UV_PYTHON_CACHE_DIR=str(root / "python-cache"),
            UV_PYTHON_BIN_DIR=str(root / "bin"),
            UV_NO_CONFIG="1",
            UV_NO_PROGRESS="1",
            PIP_CONFIG_FILE=os.devnull,
        )

        def run(arguments: list[str]) -> str:
            result = subprocess.run(
                arguments,
                cwd=root,
                env=env,
                check=True,
                capture_output=True,
                text=True,
                timeout=600,
            )
            return result.stdout.strip()

        bootstrap = root / "bootstrap"
        print(
            f"Installing uv {UV_VERSION} in a fresh temporary environment.", flush=True
        )
        run([sys.executable, "-I", "-m", "venv", str(bootstrap)])
        run(
            [
                str(python_in(bootstrap)),
                "-I",
                "-m",
                "pip",
                "--isolated",
                "--disable-pip-version-check",
                "install",
                "--no-cache-dir",
                "--no-deps",
                "--index-url",
                "https://pypi.org/simple",
                f"uv=={UV_VERSION}",
            ]
        )
        uv = str(bootstrap / ("Scripts/uv.exe" if os.name == "nt" else "bin/uv"))
        print("Downloading Python " + ", ".join(versions) + ".", flush=True)
        run([uv, "python", "install", "--no-bin", "--no-registry", *versions])
        runtimes = {}
        for index, version in enumerate(versions):
            managed = Path(
                run(
                    [
                        uv,
                        "python",
                        "find",
                        "--managed-python",
                        "--no-project",
                        version,
                    ]
                )
            ).resolve()
            if not managed.is_relative_to(root):
                raise RuntimeError(
                    "Python was resolved outside the temporary environment"
                )
            virtualenv = root / f"venv-{index}"
            run([uv, "venv", "--python", str(managed), str(virtualenv)])
            runtimes[version] = str(python_in(virtualenv))
        yield runtimes
