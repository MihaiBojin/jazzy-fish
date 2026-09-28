"""Write tables from the recorded benchmark trials."""

import gzip
import json
import statistics
from pathlib import Path
from typing import Any

import benchmark as bench

HERE = Path(__file__).resolve().parent


def main() -> None:
    config = json.loads((HERE / "config.json").read_text())
    rows = [
        json.loads(line)
        for line in gzip.decompress((HERE / "results.jsonl.gz").read_bytes())
        .decode()
        .splitlines()
    ]
    expected = bench.jobs_for(config)
    assert len(rows) == len(expected)
    assert {row["job_index"] for row in rows} == set(range(len(expected)))
    for row in rows:
        assert all(
            row[key] == value for key, value in expected[row["job_index"]].items()
        )
    checks = json.loads((HERE / "verification.json").read_text())
    assert len(checks) == len(config["interpreters"])
    assert all(test["passed"] for check in checks for test in check["tests"])
    assert all(
        row["duplicates"] == 0
        for row in rows
        if row["kind"] == "correctness" and row["variant"] != "unlocked"
    )
    assert all(
        row["within_worker_decreases"] == 0
        for row in rows
        if row["kind"] == "correctness" and row["variant"] != "unlocked"
    )

    def select(
        label: str,
        profile: str,
        variant: str,
        threads: int = 1,
        kind: str = "timing",
        stress: bool = False,
    ) -> list[dict[str, Any]]:
        return [
            row
            for row in rows
            if row["label"] == label
            and row["profile"] == profile
            and row["variant"] == variant
            and row["threads"] == threads
            and row["kind"] == kind
            and bool(row.get("switch_interval")) == stress
        ]

    def median(label: str, profile: str, variant: str, threads: int = 1) -> float:
        return statistics.median(
            row["ns_per_id"] for row in select(label, profile, variant, threads)
        )

    def spread(label: str, profile: str, variant: str, threads: int = 1) -> str:
        values = [row["ns_per_id"] for row in select(label, profile, variant, threads)]
        return f"{statistics.median(values):.1f} ({min(values):.1f}–{max(values):.1f})"

    def paired(
        label: str, profile: str, numerator: str, denominator: str, threads: int = 1
    ) -> float:
        a = {
            row["repeat"]: row["ns_per_id"]
            for row in select(label, profile, numerator, threads)
        }
        b = {
            row["repeat"]: row["ns_per_id"]
            for row in select(label, profile, denominator, threads)
        }
        return statistics.median((a[key] / b[key] - 1) * 100 for key in a)

    overheads = [
        paired(label, "millisecond", "always_locked", "unlocked")
        for label in config["interpreters"]
    ]
    lines = [
        "# Generator benchmark for PR #99",
        "",
        f"PR #99's `Generator` takes {min(overheads):.1f}% to {max(overheads):.1f}% more time per ID than the original unlocked `Generator` in the direct single-thread millisecond workload. The original opt-in `ThreadSafeGenerator` passes every shared-instance uniqueness check in this matrix.",
        "",
        "The original `Generator` provides the unlocked path. The original `ThreadSafeGenerator` locks shared calls. PR #99 puts a lock in `Generator.next_id()`.",
        "",
        "These results measure the exact PR base and head, independently of the current checkout. No production source files are modified.",
        "",
        "## Machine and interpreters",
        "",
        "Apple M1 Max, 10 physical and logical cores (8 performance, 2 efficiency), 64 GiB RAM, macOS 26.6.2 (25G83), arm64. The machine used AC power with normal power mode. CPU affinity and clock frequency were not pinned. Other machine activity was not stopped.",
        "",
        f"Trials ran from {rows[0]['utc']} to {rows[-1]['utc']}. The recorded one-minute system load ranged from {min(r['runtime']['load_average'][0] for r in rows):.2f} to {max(r['runtime']['load_average'][0] for r in rows):.2f}; load average includes benchmark activity and is not a CPU utilization percentage.",
        "",
        "| Label | CPython version | GIL enabled | Build |",
        "|---|---|---|---|",
    ]
    for label in config["interpreters"]:
        runtime = next(row["runtime"] for row in rows if row["label"] == label)
        lines.append(
            f"| {label} | {runtime['version'].split()[0]} | {runtime['gil_enabled']} | {runtime['version'].replace('|', '/')} |"
        )
    lines.extend(
        [
            "",
            "All interpreters are uv-managed python-build-standalone arm64 builds. Free-threaded processes were checked with `sys._is_gil_enabled()` after their trials; the GIL remained disabled. Comparisons between implementations within one runtime isolate the API choice better than comparisons between different Python builds.",
            "",
            "## Inputs and measurement",
            "",
            "| Input | Value |",
            "|---|---|",
            f"| Base revision | `{bench.BASE}` |",
            f"| PR head revision | `{bench.HEAD}` |",
            f"| Timing trials | {sum(r['kind'] == 'timing' for r in rows):,} |",
            f"| Correctness trials | {sum(r['kind'] == 'correctness' for r in rows):,} |",
            f"| Calls in timing trials | {sum(r['calls'] for r in rows if r['kind'] == 'timing'):,} |",
            f"| IDs checked for uniqueness | {sum(r['calls'] for r in rows if r['kind'] == 'correctness'):,} |",
            f"| Timing repetitions per case | {config['repeats']} fresh processes |",
            f"| Direct single-thread calls per trial | {config['single_calls']:,} |",
            f"| Threaded calls per trial | {config['threaded_calls']:,} total, divided evenly among workers |",
            f"| Threads | {', '.join(map(str, config['thread_counts']))} |",
            f"| Default-interval correctness | {config['correctness_repeats']} trials of {config['correctness_calls']:,} IDs per case |",
            f"| Short-interval correctness | {config['stress_calls']:,} IDs per case at `sys.setswitchinterval(1e-6)` |",
            "",
            "Each timing trial imports an immutable generator snapshot, warms the call path with 20,000 calls, creates fresh state, collects garbage, then disables cyclic GC during measurement. Calls use a bound `next_id` method. Timing excludes imports, initialization, thread creation, and duplicate checking. The timed loop discards IDs; correctness trials retain IDs and include list construction in their separate timings.",
            "",
            "`time.perf_counter_ns()` measures elapsed time. Thread workers start through a barrier; elapsed time ends when the last worker finishes. The table values are aggregate throughput, not throughput per worker or individual request latency. One-worker threaded cases run in a worker thread; direct single-thread cases run in the main thread. Timing jobs are shuffled within each repetition across runtimes, implementations, configurations, and thread counts, with a fixed seed. Only one trial process runs at a time.",
            "",
            "The normal switch interval is 5 ms. The short-interval cases target GIL scheduling; on free-threaded builds they serve as extra correctness repetitions. Their timings are excluded from the performance tables. Single-thread configurations use a real wall clock and enough sequence capacity to avoid deliberate rate limiting. The epoch is one day before trial initialization. No encoder work or application I/O is measured.",
            "",
            "| Profile | Resolution | Machine IDs | Machine bits | Sequence bits |",
            "|---|---|---|---|---|",
        ]
    )
    for name, (resolution, mids, bits, seqbits) in bench.PROFILES.items():
        lines.append(f"| {name} | {resolution} | {mids} | {bits} | {seqbits} |")
    lines.extend(
        [
            "",
            "The private-generator control gives each worker a separate unlocked generator and a distinct machine ID from 0 through `threads - 1`. It uses the threaded profile's four machine bits, constructs and warms each instance inside its worker, and requires the application to own those distinct IDs. Other threaded variants share one instance using machine ID 0. The JSON `configuration` field contains the profile defaults; `variant=private` applies this per-worker ID assignment.",
            "",
            "## Direct single-thread timings",
            "",
            "Times are median ns/ID, with the full observed range in parentheses. PR overhead is the median of the seven percentage differences paired by repetition. These are measurements on this machine, not universal latency guarantees.",
            "",
        ]
    )
    for profile in ("millisecond", "four_machines", "second", "minute"):
        lines.extend(
            [
                f"### {profile}",
                "",
                "| Python | Original Generator | Original ThreadSafeGenerator | PR Generator | PR overhead over unlocked |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for label in config["interpreters"]:
            lines.append(
                f"| {label} | {spread(label, profile, 'unlocked')} | {spread(label, profile, 'opt_in')} | {spread(label, profile, 'always_locked')} | {paired(label, profile, 'always_locked', 'unlocked'):+.1f}% |"
            )
        lines.append("")

    lines.extend(
        [
            "## Threaded throughput",
            "",
            "Values are median millions of IDs/second. Both shared locked implementations and the private-generator control passed every uniqueness trial. The unlocked shared generator is excluded from this comparison because its use across threads produces duplicates.",
            "",
        ]
    )
    for label in config["interpreters"]:
        lines.extend(
            [
                f"### Python {label}",
                "",
                "| Threads | Original ThreadSafeGenerator | PR Generator | Private Generator per worker |",
                "|---:|---:|---:|---:|",
            ]
        )
        for threads in config["thread_counts"]:
            values = [
                1000 / median(label, "threaded", variant, threads)
                for variant in ("opt_in", "always_locked", "private")
            ]
            lines.append(
                f"| {threads} | "
                + " | ".join(f"{value:.3f}" for value in values)
                + " |"
            )
        lines.extend(
            [
                "",
                "Timing spread for the two shared locked implementations, in ns/ID:",
                "",
                "| Threads | Original ThreadSafeGenerator median (range) | PR Generator median (range) |",
                "|---:|---:|---:|",
            ]
        )
        for threads in config["thread_counts"]:
            lines.append(
                f"| {threads} | {spread(label, 'threaded', 'opt_in', threads)} | {spread(label, 'threaded', 'always_locked', threads)} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Unlocked shared-generator correctness",
            "",
            "The following table is a misuse control. The original unlocked class is not the API for sharing one instance across threads. A zero count in one experiment does not prove thread safety. The throughput column comes from separate timing trials, so it is not a measure of unique IDs/second.",
            "",
            "| Python | Threads | Raw million calls/s | Duplicates at normal interval / IDs | Duplicates at short interval / IDs |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for label in config["interpreters"]:
        for threads in config["thread_counts"]:
            normal = select(label, "threaded", "unlocked", threads, "correctness")
            stress = select(label, "threaded", "unlocked", threads, "correctness", True)

            def count(samples: list[dict[str, Any]]) -> str:
                if not samples:
                    return "—"
                duplicates = sum(r["duplicates"] for r in samples)
                calls = sum(r["calls"] for r in samples)
                return f"{duplicates:,} / {calls:,} ({duplicates * 100 / calls:.3f}%)"

            lines.append(
                f"| {label} | {threads} | {1000 / median(label, 'threaded', 'unlocked', threads):.3f} | {count(normal)} | {count(stress)} |"
            )
    safe = [
        r for r in rows if r["kind"] == "correctness" and r["variant"] != "unlocked"
    ]
    lines.extend(
        [
            "",
            f"The original `ThreadSafeGenerator`, PR `Generator`, and private-generator control collectively produced **zero duplicate IDs across {sum(r['calls'] for r in safe):,} checked IDs**. Each worker's IDs were strictly increasing. Uniqueness was checked within each trial; each fresh trial starts independent state.",
            "",
            "## Verification",
            "",
            "The AST of the original `Generator.next_id()` body matches PR `Generator._next_id_locked()` after stripping the docstring. All five profiles produce identical 10,000-ID deterministic sequences across the original unlocked class, original locked class, and PR class on every interpreter. The deprecated PR subclass inherits the same `next_id` method as PR `Generator`, so a separate timing series for that alias would measure the same call path.",
            "",
            "| Python | Base generator tests | PR generator and concurrency tests |",
            "|---|---:|---:|",
        ]
    )
    for label, check in zip(config["interpreters"], checks):
        lines.append(
            f"| {label} | {check['tests'][0]['tests']} passed | {check['tests'][1]['tests']} passed |"
        )
    lines.extend(
        [
            "",
            "These checks cover the generator component. They do not run the encoder, packaging, or CLI test suites.",
            "",
            "## Reproduction and files",
            "",
            "The scripts use only the Python standard library. Both git revisions must be available locally. Update interpreter paths in `config.json` for another machine. Use a new output path for a fresh run; an existing output file resumes completed jobs.",
            "",
            "```sh",
            "python3 benchmarks/pr99/benchmark.py run benchmarks/pr99/config.json --output /tmp/pr99-results.jsonl",
            "python3 benchmarks/pr99/benchmark.py summarize /tmp/pr99-results.jsonl",
            "python3 benchmarks/pr99/verify.py",
            "```",
            "",
            "Run `verify.py` with each interpreter listed in `config.json` to repeat the verification across all five builds.",
            "",
            "`results.jsonl.gz` contains every raw trial, source hashes, runtime and GIL metadata, elapsed time, CPU time, worker start/finish spreads, and correctness counts. `summary.json` contains per-case medians, extrema, and median absolute deviations. `verification.json` contains test output for all five interpreters. `config.json` records the run settings. `report.py` validates matrix completeness and writes this report.",
            "",
            "Python's documentation distinguishes runtime GIL state from build capability and describes internal locks on built-in containers. The duplicate-ID race is a compound generator-state race; it does not establish interpreter-level dictionary corruption. See [Python free threading](https://docs.python.org/3/howto/free-threading-python.html).",
            "",
        ]
    )
    (HERE / "README.md").write_text("\n".join(lines))
    print(f"Validated {len(rows)} trials and wrote {HERE / 'README.md'}")


if __name__ == "__main__":
    main()
