"""Isolate method dispatch overhead without changing library files."""

import gc
import json
import os
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import benchmark as bench


def direct_next_id(self: Any) -> int:
    with self.lock:
        return self._unlocked_next_id()


def measure(variant: str) -> dict[str, Any]:
    module, _ = bench.load_module(bench.HEAD if variant == "pr" else bench.BASE)
    cls = module.Generator if variant == "pr" else module.ThreadSafeGenerator
    if variant == "opt_in_direct":
        cls._unlocked_next_id = module.Generator.next_id
        cls.next_id = direct_next_id
    generator = cls(time.time() - 86400, module.Resolution.MILLISECOND, [0], 0, 22)
    next_id = generator.next_id
    for _ in range(20_000):
        next_id()
    gc.collect()
    gc.disable()
    start = time.perf_counter_ns()
    for _ in range(500_000):
        next_id()
    elapsed = time.perf_counter_ns() - start
    return {
        "variant": variant,
        "ns_per_id": elapsed / 500_000,
        "calls": 500_000,
        "runtime": bench.runtime_metadata(),
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(measure(sys.argv[1])))
    else:
        config = json.loads((bench.HERE / "config.json").read_text())
        results = []
        for repeat in range(7):
            jobs = [
                (label, variant)
                for label in config["interpreters"]
                for variant in ("opt_in", "opt_in_direct", "pr")
            ]
            random.Random(982027 + repeat).shuffle(jobs)
            for label, variant in jobs:
                env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0")
                env.pop("PYTHON_GIL", None)
                process = subprocess.run(
                    [
                        config["interpreters"][label],
                        str(Path(__file__).resolve()),
                        variant,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    env=env,
                    timeout=30,
                )
                result = json.loads(process.stdout)
                result.update(label=label, repeat=repeat)
                results.append(result)
            print(f"Completed repetition {repeat + 1}/7", flush=True)
        (bench.HERE / "dispatch-results.json").write_text(
            json.dumps(results, indent=2) + "\n"
        )
        for label in config["interpreters"]:
            print(
                label,
                {
                    variant: round(
                        statistics.median(
                            r["ns_per_id"]
                            for r in results
                            if r["label"] == label and r["variant"] == variant
                        ),
                        1,
                    )
                    for variant in ("opt_in", "opt_in_direct", "pr")
                },
            )
