"""Compare generators on this machine and write raw trials and a report."""

import argparse
import ast
import hashlib
import json
import random
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark as bench
import environment

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "python/src/jazzy_fish/generator.py"

OWNERSHIP = {
    "opt_in": "shared ThreadSafeGenerator",
    "private": "private Generator per caller",
    "factory": "Generator.threadsafe factory",
}


def threaded_variants(source: dict[str, Any]) -> tuple[str, ...]:
    return (
        ("opt_in", "private", "factory")
        if source["has_factory"]
        else ("opt_in", "private")
    )


def positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def python_version(value: str) -> str:
    match = re.fullmatch(r"3\.(\d+)(?:\.\d+)?t?", value)
    if match is None or int(match[1]) < 12:
        raise argparse.ArgumentTypeError(
            "use a Python version >= 3.12, such as 3.14.7 or 3.14.7t"
        )
    return value


def probe(executable: str) -> dict[str, Any]:
    completed = subprocess.run(
        [
            executable,
            "-I",
            "-c",
            "import json, runpy, sys; print(json.dumps(runpy.run_path(sys.argv[1])['runtime_metadata']()))",
            str(Path(bench.__file__).resolve()),
        ],
        env=environment.clean_environment(),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    metadata = json.loads(completed.stdout)
    if metadata["free_threaded_build"] and metadata["gil_enabled"]:
        raise ValueError("Free-threaded Python has its GIL enabled")
    return metadata


def make_jobs(config: dict[str, Any]) -> list[dict[str, Any]]:
    jobs = []
    for repeat in range(config["repeats"]):
        block = []
        for label in config["interpreters"]:
            counts = config["thread_counts"][label]
            machine_bits = (max(counts) - 1).bit_length()
            for implementation, source in config["sources"].items():
                common = {
                    "label": label,
                    "implementation": implementation,
                    "source": source["path"],
                    "kind": "timing",
                    "repeat": repeat,
                    "calls": config["calls"],
                }
                for profile in ("millisecond", "four_machines", "second", "minute"):
                    for variant in ("unlocked", "opt_in"):
                        block.append(
                            dict(common, profile=profile, variant=variant, threads=1)
                        )
                for threads in counts:
                    for variant in threaded_variants(source):
                        block.append(
                            dict(
                                common,
                                profile="threaded",
                                variant=variant,
                                threads=threads,
                                machine_id_bits=machine_bits,
                                worker_thread=True,
                            )
                        )
        random.Random(config["seed"] + repeat).shuffle(block)
        jobs.extend(block)
    for label in config["interpreters"]:
        counts = config["thread_counts"][label]
        for implementation, source in config["sources"].items():
            for threads in counts:
                for variant in threaded_variants(source):
                    for repeat in range(2):
                        jobs.append(
                            {
                                "label": label,
                                "implementation": implementation,
                                "source": source["path"],
                                "kind": "correctness",
                                "profile": "threaded",
                                "variant": variant,
                                "threads": threads,
                                "machine_id_bits": (max(counts) - 1).bit_length(),
                                "calls": config["correctness_calls"],
                                "repeat": repeat,
                                "worker_thread": True,
                            }
                        )
                    if threads > 1 and variant != "private":
                        jobs.append(
                            dict(
                                jobs[-1],
                                repeat=0,
                                calls=min(config["correctness_calls"], 200_000),
                                switch_interval=1e-6,
                            )
                        )
    return jobs


def write_report(output: Path, config: dict[str, Any]) -> None:
    rows = [
        json.loads(line) for line in (output / "results.jsonl").read_text().splitlines()
    ]
    if len(rows) != len(config["jobs"]):
        raise ValueError("Incomplete benchmark results")
    for index, row in enumerate(rows):
        if row["job_index"] != index or any(
            row[key] != value for key, value in config["jobs"][index].items()
        ):
            raise ValueError(f"Result does not match job {index}")
        if row["source_sha256"] != config["sources"][row["implementation"]]["sha256"]:
            raise ValueError(f"Source changed during trial {index}")
        if row.get("duplicates", 0) or row.get("within_worker_decreases", 0):
            raise ValueError(
                f"Correctness failure in trial {index}; raw results are in {output}"
            )
    summary = bench.summarize_rows(rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = [
        "# Generator benchmark on this machine",
        "",
        "Baseline and Current identify the source snapshots recorded in config.json. Current is the checkout at the start of this run. Comparisons use the same settings and fresh processes, shuffled within each repetition.",
        "",
        "| Python | Platform | Available CPUs | GIL enabled | Threads tested |",
        "|---|---|---:|---|---|",
    ]
    for label, metadata in config["runtimes"].items():
        lines.append(
            f"| {label} | {metadata['platform']} | {metadata['available_cpus']} | {metadata['gil_enabled']} | {', '.join(map(str, config['thread_counts'][label]))} |"
        )
    lines += [
        "",
        "## Direct single-thread calls",
        "",
        "Times are median ns/ID with the observed minimum–maximum sample range. These are sample ranges, not confidence intervals. Lower time is better.",
        "",
        "| Python | Source | Profile | Class | Median ns/ID | Range |",
        "|---|---|---|---|---:|---:|",
    ]
    timing = [row for row in summary if row["kind"] == "timing"]
    for row in sorted(
        timing,
        key=lambda r: (
            r["label"],
            r["profile"],
            r["variant"],
            r["implementation"],
            r["threads"],
        ),
    ):
        if row["profile"] != "threaded":
            name = (
                "Generator" if row["variant"] == "unlocked" else "ThreadSafeGenerator"
            )
            lines.append(
                f"| {row['label']} | {row['implementation'].title()} | {row['profile']} | {name} | {row['median_ns']:.1f} | {row['min_ns']:.1f}–{row['max_ns']:.1f} |"
            )
    lines += [
        "",
        "## Threaded throughput",
        "",
        "Values are aggregate million IDs/second. Shared uses one ThreadSafeGenerator; private uses one unlocked Generator per caller with disjoint machine IDs. The factory uses Generator.threadsafe with one group per caller when the snapshot supports it. Higher throughput is better.",
        "",
        "| Python | Source | Ownership | Workers | Million IDs/s | Range |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in sorted(
        timing,
        key=lambda r: (r["label"], r["variant"], r["threads"], r["implementation"]),
    ):
        if row["profile"] == "threaded":
            ownership = OWNERSHIP[row["variant"]]
            lines.append(
                f"| {row['label']} | {row['implementation'].title()} | {ownership} | {row['threads']} | {row['million_ids_per_second']:.3f} | {1000 / row['max_ns']:.3f}–{1000 / row['min_ns']:.3f} |"
            )
    lines += [
        "",
        "## Observed worker recommendations",
        "",
        "| Python | Ownership | Best tested workers | Million IDs/s |",
        "|---|---|---:|---:|",
    ]
    for label in config["interpreters"]:
        for variant in threaded_variants(config["sources"]["current"]):
            cases = [
                r
                for r in timing
                if r["label"] == label
                and r["implementation"] == "current"
                and r["profile"] == "threaded"
                and r["variant"] == variant
            ]
            peak = max(
                cases, key=lambda r: (r["million_ids_per_second"], -r["threads"])
            )
            lines.append(
                f"| {label} | {OWNERSHIP[variant]} | {peak['threads']} | {peak['million_ids_per_second']:.3f} |"
            )
    checked = [row for row in rows if row["kind"] == "correctness"]
    lines += [
        "",
        "Recommendations select the highest median among tested counts, with fewer workers breaking an exact tie. Close results and overlapping ranges require longer trials. The default compares one and six workers; use --sweep for a machine-wide search. These results measure integer generation, excluding encoding and application work.",
        "",
        "## Correctness and method",
        "",
        f"{len(checked):,} correctness trials checked {sum(r['calls'] for r in checked):,} IDs with zero duplicates and strictly increasing IDs within each worker. Each source is checked separately; snapshots do not share an ID domain.",
        "",
        f"Each timing case has {config['repeats']} fresh-process samples of {config['calls']:,} calls. The measured path is warmed with 20,000 calls. Private generators and factory bindings are warmed inside each caller before timing. Threaded calls are divided evenly; a barrier starts the clock and the last caller stops it. Thread creation, imports, and uniqueness checks are outside timing. Cyclic GC is disabled during measurement. Correctness trials retain IDs, run separately, and include extra shared-generator checks with a 1 µs thread-switch interval. Their timings do not contribute to throughput estimates.",
        "",
        "The direct profiles use millisecond, second, and minute resolution with one machine, plus a millisecond profile with four machine IDs. The threaded profile uses millisecond resolution and 22 sequence bits. Its machine bit width fits the largest tested count and is identical across sources and ownership modes. Each worker's machine ID is its zero-based index in private mode; shared mode uses machine ID zero. Factory mode supplies IDs zero through callers minus one and sets threads to the caller count. Full configuration and runtime metadata are in results.jsonl; interpreter and checkout paths are omitted.",
        "",
        "The CPU count uses process availability when supported, then CPU affinity, then the operating system's logical CPU count. Affinity and frequency are not controlled by this benchmark. Run without competing workloads for less variation. Free-threaded builds are checked after every trial to ensure the GIL remains disabled.",
        "",
        "config.json records Python requests, the uv version, exact jobs, and source hashes; snapshots/ preserves the measured source. results.jsonl contains every raw trial; summary.json contains per-case medians, ranges, and median absolute deviations. A nonzero exit status indicates an incomplete run or a correctness failure. Timing differences never fail a test.",
    ]
    (output / "README.md").write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--python",
        action="append",
        dest="pythons",
        type=python_version,
        help="Python version to download; repeat to compare builds (suffix t for free-threaded)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--threads",
        nargs="+",
        type=positive,
        help="Caller counts to compare with one (default: 6)",
    )
    group.add_argument(
        "--sweep",
        action="store_true",
        help="Test every count from 1 through available CPUs minus one",
    )
    parser.add_argument("--repeats", type=positive, default=7)
    parser.add_argument(
        "--calls", type=positive, default=1_000_000, help="Total calls per timing trial"
    )
    parser.add_argument("--correctness-calls", type=positive, default=1_000_000)
    parser.add_argument(
        "--baseline", help="Optional generator source file or local git revision"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="New results directory"
    )
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.exists():
        parser.error("Output already exists; choose a new directory")
    versions = list(dict.fromkeys(args.pythons or environment.DEFAULT_PYTHONS))
    config: dict[str, Any] = {
        "interpreters": {},
        "runtimes": {},
        "thread_counts": {},
        "sources": {},
        "repeats": args.repeats,
        "calls": args.calls,
        "correctness_calls": args.correctness_calls,
        "seed": 990928,
        "setup": {
            "uv_version": environment.UV_VERSION,
            "python_requests": versions,
            "runtime_dependencies": [],
            "environment": "fresh temporary installations and virtual environments",
        },
    }
    try:
        sources = {"current": (ROOT / SOURCE).read_bytes()}
        if args.baseline:
            path = Path(args.baseline)
            sources["baseline"] = (
                path.read_bytes()
                if path.is_file()
                else subprocess.check_output(
                    ["git", "show", f"{args.baseline}:{SOURCE}"], cwd=ROOT
                )
            )
        with environment.provision(versions) as installed:
            interpreters = {}
            for version, executable in installed.items():
                metadata = probe(executable)
                label = metadata["version"].split()[0] + (
                    "-gil" if metadata["gil_enabled"] else "-free"
                )
                if label in interpreters:
                    continue
                counts = (
                    list(range(1, max(1, metadata["available_cpus"] - 1) + 1))
                    if args.sweep
                    else sorted({1, *(args.threads or [6])})
                )
                if max(counts) > min(args.calls, args.correctness_calls):
                    raise ValueError(
                        "Calls per trial must be at least the largest caller count"
                    )
                interpreters[label] = executable
                config["interpreters"][label] = version
                config["runtimes"][label] = metadata
                config["thread_counts"][label] = counts
            output.mkdir(parents=True)
            (output / "snapshots").mkdir()
            for name, source in sources.items():
                path = Path("snapshots") / f"{name}.py.txt"
                (output / path).write_bytes(source)
                generator_class = next(
                    node
                    for node in ast.parse(source).body
                    if isinstance(node, ast.ClassDef) and node.name == "Generator"
                )
                config["sources"][name] = {
                    "path": path.as_posix(),
                    "sha256": hashlib.sha256(source).hexdigest(),
                    "has_factory": any(
                        isinstance(node, ast.FunctionDef) and node.name == "threadsafe"
                        for node in generator_class.body
                    ),
                }
            config["jobs"] = make_jobs(config)
            (output / "config.json").write_text(json.dumps(config, indent=2) + "\n")
            print(
                f"Running {len(config['jobs'])} trials across {len(interpreters)} Python builds.",
                flush=True,
            )
            bench.run(
                config,
                output / "results.jsonl",
                interpreters,
                environment.clean_environment(),
            )
            write_report(output, config)
    except KeyboardInterrupt:
        parser.exit(130, "Benchmark interrupted; temporary environments removed.\n")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Benchmark failed: {error}\n")
    print(
        "Finished; report written to the requested output directory. Temporary environments removed."
    )


if __name__ == "__main__":
    main()
