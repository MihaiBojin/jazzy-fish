"""Measure generator calls and check uniqueness at the exact PR revisions."""

import argparse
import gc
import gzip
import hashlib
import importlib.util
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import sysconfig
import threading
import time
import traceback
from itertools import pairwise
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = "95affdf00dd2c4b3a0a6ffa2c7185aaaa03c1761"
HEAD = "7cc9e250eb01f6434ceeb1224475a2b10953777d"
SOURCE = "python/src/jazzy_fish/generator.py"
VARIANTS = ("unlocked", "opt_in", "always_locked")
PROFILES = {
    "millisecond": ("MILLISECOND", [0], 0, 22),
    "four_machines": ("MILLISECOND", [0, 1, 2, 3], 2, 12),
    "second": ("SECOND", [0], 0, 22),
    "minute": ("MINUTE", [0], 0, 24),
    "threaded": ("MILLISECOND", [0], 4, 22),
}


def load_module(revision: str) -> tuple[ModuleType, str]:
    if revision.startswith("file:"):
        source = (ROOT / revision[5:]).read_bytes()
    else:
        source = subprocess.check_output(
            ["git", "show", f"{revision}:{SOURCE}"], cwd=ROOT
        )
    name = "generator_" + revision[:8]
    spec = importlib.util.spec_from_loader(name, loader=None)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, f"{revision}/{SOURCE}", "exec"), module.__dict__)  # noqa: S102 - Load the inspected source snapshot.
    return module, hashlib.sha256(source).hexdigest()


def available_cpus() -> int:
    process_count = getattr(os, "process_cpu_count", lambda: None)()
    if process_count is not None:
        return max(1, process_count)
    if hasattr(os, "sched_getaffinity"):
        try:
            return max(1, len(os.sched_getaffinity(0)))
        except OSError:
            pass
    return os.cpu_count() or 1


def runtime_metadata() -> dict[str, Any]:
    return {
        "version": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "logical_cpus": os.cpu_count(),
        "available_cpus": available_cpus(),
        "gil_enabled": getattr(sys, "_is_gil_enabled", lambda: True)(),
        "free_threaded_build": bool(sysconfig.get_config_var("Py_GIL_DISABLED")),
        "switch_interval": sys.getswitchinterval(),
        "timer": vars(time.get_clock_info("perf_counter")),
        "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
    }


def execute(job: dict[str, Any]) -> dict[str, Any]:
    variant = job["variant"]
    revision = job.get("revision", HEAD if variant == "always_locked" else BASE)
    module, source_hash = load_module(revision)
    constructor = (
        module.ThreadSafeGenerator if variant == "opt_in" else module.Generator
    )
    resolution, machine_ids, machine_bits, sequence_bits = PROFILES[job["profile"]]
    machine_bits = job.get("machine_id_bits", machine_bits)
    if variant == "factory":
        constructor = module.Generator.threadsafe
        machine_ids = list(range(job["threads"]))
    epoch = time.time() - 86400

    def make_generator(machine_id: int | None = None) -> Any:
        return constructor(
            epoch=epoch,
            resolution=getattr(module.Resolution, resolution),
            machine_ids=machine_ids if machine_id is None else [machine_id],
            machine_id_bits=machine_bits,
            sequence_bits=sequence_bits,
            **({"threads": job["threads"]} if variant == "factory" else {}),
        )

    if job.get("switch_interval"):
        sys.setswitchinterval(job["switch_interval"])
    generator = make_generator()
    for _ in range(20_000):
        generator.next_id()
    generator = make_generator()
    gc.collect()
    gc.disable()
    threads = job["threads"]
    count = job["calls"]
    collect = job["kind"] == "correctness"
    private = variant == "private"
    results: list[Any] = [None] * threads
    errors: list[str | None] = [None] * threads
    starts = [0] * threads
    finishes = [0] * threads
    clock = {}

    def start_clock() -> None:
        clock["cpu_start"] = time.process_time_ns()
        clock["wall_start"] = time.perf_counter_ns()

    barrier = threading.Barrier(threads, action=start_clock)

    def worker(index: int) -> None:
        try:
            instance = make_generator(index) if private else generator
            if private or variant == "factory":
                for _ in range(20_000):
                    instance.next_id()
            next_id = instance.next_id
            worker_calls = count // threads + (index < count % threads)
            if threads > 1 or job.get("worker_thread"):
                barrier.wait(timeout=60)
            else:
                start_clock()
            starts[index] = time.perf_counter_ns()
            if collect:
                values = [next_id() for _ in range(worker_calls)]
                finishes[index] = time.perf_counter_ns()
                results[index] = values
            else:
                for _ in range(worker_calls):
                    next_id()
                finishes[index] = time.perf_counter_ns()
                results[index] = worker_calls
        except BaseException:  # noqa: BLE001 - Propagate worker failures after aborting the barrier.
            errors[index] = traceback.format_exc()
            barrier.abort()

    if threads == 1 and not job.get("worker_thread"):
        worker(0)
    else:
        workers = [threading.Thread(target=worker, args=(i,)) for i in range(threads)]
        for thread in workers:
            thread.start()
        for thread in workers:
            thread.join(timeout=120)
        if any(thread.is_alive() for thread in workers):
            raise RuntimeError("Worker did not finish")
    cpu_elapsed = time.process_time_ns() - clock.get("cpu_start", 0)
    if any(errors):
        raise RuntimeError(str(errors))
    elapsed = max(finishes) - clock["wall_start"]
    gc.enable()
    result = {
        **job,
        "runtime": runtime_metadata(),
        "revision": revision,
        "source_sha256": source_hash,
        "elapsed_ns": elapsed,
        "cpu_ns": cpu_elapsed,
        "ns_per_id": elapsed / count,
        "ids_per_second": count * 1e9 / elapsed,
        "cpu_to_wall_ratio": cpu_elapsed / elapsed,
        "start_spread_ns": max(starts) - min(starts),
        "finish_spread_ns": max(finishes) - min(finishes),
        "configuration": {
            "resolution": resolution,
            "machine_ids": machine_ids,
            "machine_id_bits": machine_bits,
            "sequence_bits": sequence_bits,
            "epoch_seconds_ago": 86400,
        },
    }
    if collect:
        values = [value for batch in results for value in batch]
        assert len(values) == count
        result["duplicates"] = count - len(set(values))
        result["duplicate_percent"] = result["duplicates"] * 100 / count
        result["within_worker_decreases"] = sum(
            sum(a >= b for a, b in pairwise(batch)) for batch in results
        )
    else:
        assert sum(results) == count
    return result


def jobs_for(config: dict[str, Any]) -> list[dict[str, Any]]:
    jobs = []
    for repeat in range(config["repeats"]):
        round_jobs = []
        for label in config["interpreters"]:
            for profile in ("millisecond", "four_machines", "second", "minute"):
                for variant in VARIANTS:
                    round_jobs.append(
                        {
                            "label": label,
                            "kind": "timing",
                            "profile": profile,
                            "variant": variant,
                            "threads": 1,
                            "calls": config["single_calls"],
                            "repeat": repeat,
                        }
                    )
            for threads in config["thread_counts"]:
                for variant in (*VARIANTS, "private"):
                    round_jobs.append(
                        {
                            "label": label,
                            "kind": "timing",
                            "profile": "threaded",
                            "variant": variant,
                            "threads": threads,
                            "calls": config["threaded_calls"],
                            "repeat": repeat,
                            "worker_thread": True,
                        }
                    )
        random.Random(config["seed"] + repeat).shuffle(round_jobs)
        jobs.extend(round_jobs)
    for repeat in range(config["correctness_repeats"]):
        for label in config["interpreters"]:
            for threads in config["thread_counts"]:
                for variant in (*VARIANTS, "private"):
                    jobs.append(
                        {
                            "label": label,
                            "kind": "correctness",
                            "profile": "threaded",
                            "variant": variant,
                            "threads": threads,
                            "calls": config["correctness_calls"],
                            "repeat": repeat,
                            "worker_thread": True,
                        }
                    )
    for label in config["interpreters"]:
        for threads in config["thread_counts"][1:]:
            for variant in VARIANTS:
                jobs.append(
                    {
                        "label": label,
                        "kind": "correctness",
                        "profile": "threaded",
                        "variant": variant,
                        "threads": threads,
                        "calls": config["stress_calls"],
                        "repeat": 0,
                        "switch_interval": 1e-6,
                        "worker_thread": True,
                    }
                )
    return jobs


def run(config_path: Path, output: Path) -> None:
    config = json.loads(config_path.read_text())
    jobs = config["jobs"] if "jobs" in config else jobs_for(config)
    completed = set()
    if output.exists():
        completed = {
            json.loads(line)["job_index"] for line in output.read_text().splitlines()
        }
    started = time.monotonic()
    for index, job in enumerate(jobs):
        if index in completed:
            continue
        env = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
        env.pop("PYTHON_GIL", None)
        process = subprocess.run(
            [
                config["interpreters"][job["label"]],
                str(Path(__file__).resolve()),
                "worker",
                json.dumps(job),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=180,
        )
        if process.returncode:
            raise RuntimeError(f"{job}\n{process.stdout}\n{process.stderr}")
        result = json.loads(process.stdout)
        if (
            result["runtime"]["free_threaded_build"]
            and result["runtime"]["gil_enabled"]
        ):
            raise RuntimeError("Free-threaded runtime enabled the GIL")
        result["job_index"] = index
        result["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with output.open("a") as stream:
            stream.write(json.dumps(result, sort_keys=True) + "\n")
        if index % 10 == 0 or index + 1 == len(jobs):
            print(
                f"{index + 1}/{len(jobs)} {time.monotonic() - started:.0f}s "
                f"{job['label']} {job['variant']} {job['threads']} threads "
                f"{result['ns_per_id']:.1f} ns/id",
                flush=True,
            )


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = (
        "label",
        "implementation",
        "kind",
        "profile",
        "variant",
        "threads",
        "switch_interval",
    )
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = tuple(row.get(k) for k in fields)
        groups.setdefault(key, []).append(row)
    summary = []
    for key, samples in groups.items():
        times = [row["ns_per_id"] for row in samples]
        median = statistics.median(times)
        summary.append(
            {
                **dict(zip(fields, key)),
                "samples": len(samples),
                "median_ns": median,
                "min_ns": min(times),
                "max_ns": max(times),
                "median_absolute_deviation_ns": statistics.median(
                    abs(t - median) for t in times
                ),
                "million_ids_per_second": 1000 / median,
                "total_calls": sum(row["calls"] for row in samples),
                "duplicates": sum(row.get("duplicates", 0) for row in samples),
                "within_worker_decreases": sum(
                    row.get("within_worker_decreases", 0) for row in samples
                ),
            }
        )
    return summary


def summarize(path: Path) -> None:
    contents = (
        gzip.decompress(path.read_bytes()).decode()
        if path.suffix == ".gz"
        else path.read_text()
    )
    summary = summarize_rows([json.loads(line) for line in contents.splitlines()])
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("worker", "run", "summarize"))
    parser.add_argument("input")
    parser.add_argument("--output", type=Path, default=HERE / "results.jsonl")
    args = parser.parse_args()
    if args.action == "worker":
        print(json.dumps(execute(json.loads(args.input))))
    elif args.action == "run":
        run(Path(args.input), args.output)
    else:
        summarize(Path(args.input))
