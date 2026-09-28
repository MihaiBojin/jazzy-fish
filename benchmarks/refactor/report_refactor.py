"""Validate the recorded matrix and write its performance tables."""

import gzip
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def read_trials(name: str) -> list[dict[str, Any]]:
    path = HERE / name
    if path.exists():
        contents = path.read_text()
    else:
        with gzip.open(str(path) + ".gz", "rt") as stream:
            contents = stream.read()
    return [json.loads(line) for line in contents.splitlines()]


def validate(rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    assert len(rows) == len(config["jobs"])
    assert {row["job_index"] for row in rows} == set(range(len(rows)))
    hashes = {}
    for row in rows:
        expected = config["jobs"][row["job_index"]]
        assert all(row[key] == value for key, value in expected.items())
        revision = row["revision"]
        if revision not in hashes:
            source = (ROOT / revision.removeprefix("file:")).read_bytes()
            hashes[revision] = hashlib.sha256(source).hexdigest()
        assert row["source_sha256"] == hashes[revision]
        runtime = row["runtime"]
        assert runtime["gil_enabled"] != runtime["free_threaded_build"]
        if row["kind"] == "correctness":
            assert row["duplicates"] == 0
            assert row["within_worker_decreases"] == 0


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = ("label", "implementation", "profile", "variant", "threads")
    groups = defaultdict(list)
    for row in rows:
        if row["kind"] == "timing":
            groups[tuple(row[key] for key in keys)].append(row)
    summary = []
    for key, samples in sorted(groups.items()):
        values = [sample["ns_per_id"] for sample in samples]
        median = statistics.median(values)
        summary.append(
            dict(
                zip(keys, key),
                samples=len(values),
                median_ns=median,
                min_ns=min(values),
                max_ns=max(values),
                mad_ns=statistics.median(abs(value - median) for value in values),
                million_ids_per_second=1000 / median,
                median_cpu_to_wall=statistics.median(
                    sample["cpu_to_wall_ratio"] for sample in samples
                ),
            )
        )
    return summary


def write_confirmation() -> None:
    config = json.loads((HERE / "confirmation-config.json").read_text())
    rows = read_trials("confirmation-results.jsonl")
    validate(rows, config)
    summary = summarize(rows)
    (HERE / "confirmation-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    lines = [
        "# Longer worker-count confirmation",
        "",
        "Each case generates 5,000,000 IDs, divided evenly among workers, in five fresh processes. These trials measure the optimized snapshot with a separate unlocked generator per worker. They run after the full baseline/optimized matrix. All nine worker counts are tested on both free-threaded builds; the GIL remains disabled.",
        "",
        "The setup matches the main matrix: 20,000 warmup calls, distinct machine IDs, 4 machine bits, 22 sequence bits, millisecond resolution, and a barrier before timing. Only one process runs at a time; case order is shuffled within each repetition. CPU/wall is process CPU time divided by elapsed wall time. CPU ns/ID measures total process CPU work per ID, including worker teardown and joins.",
        "",
        f"Recorded from {rows[0]['utc']} to {rows[-1]['utc']}: {len(rows)} trials and {sum(r['calls'] for r in rows):,} timed calls.",
    ]
    for label in config["interpreters"]:
        lines += [
            "",
            f"## {label}",
            "",
            "| Workers | Median M IDs/s | Range M IDs/s | MAD, ns/ID | CPU/wall | CPU ns/ID |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
        for item in sorted(
            (s for s in summary if s["label"] == label), key=lambda s: s["threads"]
        ):
            samples = [
                r
                for r in rows
                if r["label"] == label and r["threads"] == item["threads"]
            ]
            cpu_ns = statistics.median(r["cpu_ns"] / r["calls"] for r in samples)
            lines.append(
                f"| {item['threads']} | {item['million_ids_per_second']:.3f} | "
                f"{1000 / item['max_ns']:.3f}–{1000 / item['min_ns']:.3f} | "
                f"{item['mad_ns']:.2f} | {item['median_cpu_to_wall']:.2f} | {cpu_ns:.1f} |"
            )
    lines += [
        "",
        "These ranges describe five observed samples, not confidence intervals. [confirmation-results.jsonl.gz](confirmation-results.jsonl.gz) contains the raw measurements; [confirmation-config.json](confirmation-config.json) contains every job and interpreter path. Reproduce from the repository root:",
        "",
        "```sh",
        "python3 benchmarks/pr99/benchmark.py run benchmarks/refactor/confirmation-config.json --output /tmp/refactor-confirmation.jsonl",
        "```",
    ]
    (HERE / "confirmation.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    for experiment in ("stages", "packing", "conditional"):
        inputs = json.loads((HERE / f"{experiment}-config.json").read_text())
        validate(read_trials(f"{experiment}-results.jsonl"), inputs)
    config = json.loads((HERE / "config.json").read_text())
    rows = read_trials("results.jsonl")
    validate(rows, config)
    tests = json.loads((HERE / "tests.json").read_text())
    assert len(tests) == 5 and all(test["returncode"] == 0 for test in tests)
    summary = summarize(rows)
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    index = {
        (s["label"], s["implementation"], s["profile"], s["variant"], s["threads"]): s
        for s in summary
    }

    def result(
        label: str, implementation: str, profile: str, variant: str, threads: int = 1
    ) -> dict[str, Any]:
        return index[label, implementation, profile, variant, threads]

    def speed(label: str, implementation: str, variant: str, threads: int) -> float:
        return result(label, implementation, "threaded", variant, threads)[
            "million_ids_per_second"
        ]

    def paired_reduction(label: str, profile: str, variant: str) -> float:
        selected = [
            row
            for row in rows
            if row["kind"] == "timing"
            and row["label"] == label
            and row["profile"] == profile
            and row["variant"] == variant
        ]
        samples = {
            (row["implementation"], row["repeat"]): row["ns_per_id"] for row in selected
        }
        return statistics.median(
            100 * (1 - samples["optimized", repeat] / samples["baseline", repeat])
            for repeat in range(config["repeats"])
        )

    lines = [
        "# Opt-in generator performance",
        "",
        "`Generator` performs unlocked generation. `ThreadSafeGenerator` serializes calls with one lock and directly dispatches to the same generation method. Both bind `time.time` at construction, cache the resolution divisor, and pack IDs with one conditional machine-ID shift. Assigning `current_time` remains supported; assigning `resolution` updates the cached divisor.",
        "",
        "## Machine and method",
        "",
        "Apple M1 Max, 10 physical/logical cores: 8 performance and 2 efficiency cores, 64 GiB RAM, macOS 26.6.2 arm64. AC power, normal power mode. No CPU affinity or clock-frequency control. This was a live workstation; comparisons use interleaved baseline and optimized trials from this run.",
        "",
        f"The baseline is commit `{config['baseline_revision']}`. The optimized source SHA-256 is `{config['optimized_sha256']}`. Both sources are in [snapshots](snapshots/). Every raw record contains its source hash and runtime metadata.",
        "",
        f"Trials ran from {rows[0]['utc']} to {rows[-1]['utc']}. Recorded one-minute load average ranged from {min(r['runtime']['load_average'][0] for r in rows):.2f} to {max(r['runtime']['load_average'][0] for r in rows):.2f}; it includes benchmark activity and is not CPU utilization.",
        "",
        "| Label | CPython | GIL enabled |",
        "|---|---|---|",
    ]
    for label in config["interpreters"]:
        runtime = next(row["runtime"] for row in rows if row["label"] == label)
        lines.append(
            f"| {label} | {runtime['version'].split()[0]} | {runtime['gil_enabled']} |"
        )
    lines += [
        "",
        "Each case has seven fresh-process timing trials, shuffled within each repetition. Only one trial runs at a time. A trial warms 20,000 calls, uses a real wall clock and an epoch one day earlier, and disables cyclic GC during measurement. Free-threaded runtimes are checked after every trial to ensure the GIL is disabled.",
        "",
        "Direct cases perform 1,000,000 calls. Threaded cases divide 500,000 calls among workers. A barrier starts the clock, and the last worker's completion ends it. Imports, initialization, thread creation, and correctness checks are outside the timing interval. Values are aggregate throughput from a bound-method loop, excluding encoding and application I/O. One-worker threaded cases run in a worker thread; direct cases run in the main thread.",
        "",
        "| Profile | Resolution | Machine IDs | Machine bits | Sequence bits |",
        "|---|---|---|---:|---:|",
        "| millisecond | millisecond | 0 | 0 | 22 |",
        "| four_machines | millisecond | 0, 1, 2, 3 | 2 | 12 |",
        "| second | second | 0 | 0 | 22 |",
        "| minute | minute | 0 | 0 | 24 |",
        "| threaded | millisecond | 0 shared, or worker index private | 4 | 22 |",
        "",
        "The private case constructs and warms one unlocked generator inside each worker. Machine IDs are disjoint across workers. The shared case uses one `ThreadSafeGenerator`. Both configurations use the same bit widths. Sequence capacities avoid deliberate waiting in the throughput workloads; boundary tests exercise exhaustion separately.",
        "",
        "## Single-thread cost",
        "",
        "Values are median nanoseconds per ID. The percentage is the median reduction in time per ID, paired by repetition. Full extrema and median absolute deviations are in [summary.json](summary.json). Lower time is better.",
    ]
    for profile in ("millisecond", "four_machines", "second", "minute"):
        lines += [
            "",
            f"### {profile}",
            "",
            "| Python | Generator baseline → optimized | Time reduction | ThreadSafeGenerator baseline → optimized | Time reduction |",
            "|---|---:|---:|---:|---:|",
        ]
        for label in config["interpreters"]:
            values = []
            for variant in ("unlocked", "opt_in"):
                before = result(label, "baseline", profile, variant)["median_ns"]
                after = result(label, "optimized", profile, variant)["median_ns"]
                values += [
                    f"{before:.1f} → {after:.1f}",
                    f"{paired_reduction(label, profile, variant):.1f}%",
                ]
            lines.append(f"| {label} | " + " | ".join(values) + " |")
    lines += [
        "",
        "## Thread counts",
        "",
        "Values are median million IDs/second, baseline → optimized. Higher throughput is better. Every integer from one through nine workers is tested.",
    ]
    for variant, title in (
        ("opt_in", "One shared ThreadSafeGenerator"),
        ("private", "One Generator per worker"),
    ):
        lines += [
            "",
            f"### {title}",
            "",
            "| Threads | " + " | ".join(config["interpreters"]) + " |",
            "|---:|" + "---:|" * 5,
        ]
        for threads in range(1, 10):
            cells = [
                f"{speed(label, 'baseline', variant, threads):.3f} → {speed(label, 'optimized', variant, threads):.3f}"
                for label in config["interpreters"]
            ]
            lines.append(f"| {threads} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "### Observed peaks in the full matrix",
        "",
        "| Python | Shared best count | Shared M IDs/s | Private best count | Private M IDs/s | Private speedup over one worker |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label in config["interpreters"]:
        shared = max(range(1, 10), key=lambda t: speed(label, "optimized", "opt_in", t))
        private = max(
            range(1, 10), key=lambda t: speed(label, "optimized", "private", t)
        )
        peak = speed(label, "optimized", "private", private)
        lines.append(
            f"| {label} | {shared} | {speed(label, 'optimized', 'opt_in', shared):.3f} | {private} | {peak:.3f} | {peak / speed(label, 'optimized', 'private', 1):.2f}× |"
        )
    lines += [
        "",
        "These are observed medians on this machine. Small differences within the trial spread do not establish a distinct optimum. See [recommendation.md](recommendation.md) for the worker recommendation and longer confirmation trials.",
        "",
        "## Correctness",
        "",
        f"The matrix contains {sum(r['kind'] == 'timing' for r in rows):,} timing trials and {sum(r['kind'] == 'correctness' for r in rows):,} correctness trials. Timing trials performed {sum(r['calls'] for r in rows if r['kind'] == 'timing'):,} calls.",
        "",
        "| Configuration | IDs checked | Duplicates | Non-increasing IDs within a worker |",
        "|---|---:|---:|---:|",
    ]
    for variant, name in (
        ("opt_in", "Shared ThreadSafeGenerator"),
        ("private", "Separate Generator instances"),
    ):
        checked = [
            r for r in rows if r["kind"] == "correctness" and r["variant"] == variant
        ]
        lines.append(
            f"| {name} | {sum(r['calls'] for r in checked):,} | {sum(r['duplicates'] for r in checked)} | {sum(r['within_worker_decreases'] for r in checked)} |"
        )
    lines += [
        "",
        "Correctness trials check the optimized snapshot only. They retain all IDs and check exact uniqueness plus strictly increasing values within each worker. Each configuration has two trials of 1,000,000 IDs. Shared cases with 2–9 workers also run 200,000 IDs with a 1 µs switch interval. Correctness timings are excluded from performance tables. These checks cover the measured configurations; they are not a proof for arbitrary clock behavior or machine-ID assignments.",
        "",
        "All 41 unit tests pass on each of the five builds, for 205 executions. [tests.json](tests.json) records the commands' runtimes and results. Eight new tests cover clock boundaries, per-machine sequences, zero-bit configurations, replaceable clocks, resolution assignment, disjoint ID domains, extending a machine list, and lock serialization when the clock yields. The clock-boundary and concurrency checks were also verified against intentional in-memory faults before the refactor.",
        "",
        "## Optimization experiments",
        "",
        "[stages-results.jsonl.gz](stages-results.jsonl.gz), [packing-results.jsonl.gz](packing-results.jsonl.gz), and [conditional-results.jsonl.gz](conditional-results.jsonl.gz) record 900 preliminary timing trials on 3.12, 3.14, and 3.14t, with five repetitions per case. The stage snapshots and matching config files preserve their exact inputs.",
        "",
        "Direct dispatch avoids a `super()` lookup in the locked path. Binding the clock removes a Python lambda call. Caching the resolution removes an enum property access on every clock read; it has the largest measured effect on private free-threaded scaling. Reduced access to shared enum state is a plausible contributor to that scaling gain; no native contention profiler was used to isolate the mechanism.",
        "",
        "The conditional packing candidate reduces median time by 1.7–3.0% across its 12 runtime/profile/class combinations. Plain dictionary candidates and local rotation variables do not give consistent gains across builds. An eager dictionary candidate also fails the machine-list-extension compatibility test. The production implementation uses the original lazy defaultdict state. Unconditional machine-ID packing slows the zero-machine-bit profile; production retains that condition.",
        "",
        "## Reproduction",
        "",
        "Use the interpreter paths in [config.json](config.json), or replace them with matching builds. Run from the repository root:",
        "",
        "```sh",
        "python3 benchmarks/pr99/benchmark.py run benchmarks/refactor/config.json --output /tmp/refactor-results.jsonl",
        "PYTHONPATH=python/src /path/to/python -m unittest discover -s python/tests",
        "python3 benchmarks/refactor/report_refactor.py",
        "```",
        "",
        "The first command writes a new experiment to `/tmp`; the report command validates and summarizes the archived repository results. [results.jsonl.gz](results.jsonl.gz) contains all raw trials, including source hashes, GIL state, wall/CPU times, worker timing spreads, and correctness counts. [report_refactor.py](report_refactor.py) checks completeness against every configured job and verifies source hashes before generating this report.",
    ]
    (HERE / "README.md").write_text("\n".join(lines) + "\n")
    write_confirmation()
    print(f"Validated {len(rows)} trials; wrote README.md and summary.json")


if __name__ == "__main__":
    main()
