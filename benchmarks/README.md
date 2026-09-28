# Run the generator benchmark on your machine

From a source checkout, run with Python 3.12 or newer:

```sh
python3.14 benchmarks/run.py --output out/benchmark
```

The default compares one and six callers on the current interpreter. It measures
unlocked single-thread generation, a shared `ThreadSafeGenerator`, separate
unlocked generators with disjoint machine IDs, and `Generator.threadsafe` with
one group per caller. Each timing case has seven fresh processes with one million
calls per process. Correctness runs separately and fails on duplicates or non-increasing
IDs within a worker.

To find the best count on the current machine:

```sh
python3.14 benchmarks/run.py --sweep --output out/benchmark-sweep
```

`--sweep` tests every count from one through the available CPU count minus one,
with a minimum of one. CPU availability respects process affinity where the
interpreter exposes it. To test chosen counts, use `--threads 2 4 6 8`; one worker
is always included. The default of six is a comparison point, not a claim that
six is fastest on every machine.

Use `--python` repeatedly to compare installed interpreters. An executable name
on `PATH` or an absolute path works, including free-threaded builds:

```sh
python3.14 benchmarks/run.py --sweep \
  --python python3.12 --python python3.13 --python python3.14 \
  --python python3.13t --python python3.14t \
  --baseline benchmarks/sdk/snapshots/baseline.py.txt \
  --output out/benchmark-versions
```

The tool does not install interpreters. Omit any build that is unavailable.
`--baseline` accepts a generator source snapshot or a local git revision. The
current checkout and optional baseline are copied into the output directory
before measurement, with their SHA-256 hashes. Comparisons use the same bit widths,
call counts, and thread counts for both sources.

For a quick setup check, shorten the run. These settings are too small for a
worker recommendation:

```sh
python3.14 benchmarks/run.py --threads 2 --repeats 1 \
  --calls 1000 --correctness-calls 1000 --output out/benchmark-smoke
```

The output directory must be new. It contains:

| File | Contents |
|---|---|
| `README.md` | Timing tables, sample ranges, correctness totals, and best tested worker counts |
| `results.jsonl` | Every trial with source hash, runtime, GIL state, wall/CPU time, and correctness counts |
| `summary.json` | Per-case medians, extrema, and median absolute deviations |
| `config.json`, `snapshots/` | Exact jobs, interpreter paths, and measured source |

Run without competing CPU workloads. The report measures integer generation;
encoding, I/O, and application scheduling can change the best count. Overlapping
sample ranges need longer trials before choosing between close results. Increase
`--calls` or `--repeats` for those comparisons. Timing differences never cause a
test failure.

## Measurement method

Each timing trial runs in a fresh process. Cases are shuffled within each
repetition, with the seed recorded in `config.json`. The harness warms the path
with 20,000 calls; private generators and factory assignments are warmed inside
each caller. A barrier starts threaded timing, and the last caller stops it.
Thread creation, imports, and uniqueness checks are outside timing. Cyclic GC is
disabled during measurement. `--calls` is the total per trial, divided among
callers, rather than the number per caller.

The direct profiles cover millisecond, second, and minute resolution with one
machine ID, plus a millisecond profile with four IDs. Threaded trials use
millisecond resolution and 22 sequence bits; the machine bit width fits the
largest tested count. Private callers and factory groups have disjoint machine
IDs. Shared-lock trials use one `ThreadSafeGenerator`. The factory uses one group
per measured caller and creates no threads itself.

Every configured correctness case runs twice with `--correctness-calls` IDs per
trial, defaulting to one million. Shared-lock and factory cases with multiple
callers also run at a 1 µs thread-switch interval, capped at 200,000 IDs. Timing
results exclude these checks. The harness records runtime and GIL state for every
trial and rejects free-threaded runs whose GIL becomes enabled.

The benchmark reuses [the measurement harness](pr99/benchmark.py). The integration
tests in [test_benchmark_cli.py](../python/tests/test_benchmark_cli.py) cover execution
from another directory, source comparisons, correctness, and output preservation.

## Recorded SDK results

The recorded machine is a 10-core Apple M1 Max. The SDK matrix measures standard
CPython 3.12.14, 3.13.15, and 3.14.7, plus free-threaded 3.13.15 and 3.14.7, with
every caller count from one through nine. Its baseline is main at `4763e1a`;
the measured SDK is included in commit `d44de33`. Exact source and harness hashes
are in [provenance.json](sdk/provenance.json), with the measured source files in
[snapshots/](sdk/snapshots/).

| Experiment | Settings | Evidence |
|---|---|---|
| SDK matrix | 1,525 timing trials; five samples of 500,000 IDs per case | [Report](sdk/README.md), [raw trials](sdk/results.jsonl.gz) |
| Correctness matrix | 570 trials; 57 million IDs; zero duplicates or within-worker decreases | [Job configuration](sdk/config.json), [raw trials](sdk/results.jsonl.gz) |
| Longer free-threaded trials | 180 trials; five samples of five million IDs per factory/private case | [Report](sdk/confirmation.md), [raw trials](sdk/confirmation-results.jsonl.gz) |
| Test suite | 95 tests and 26 subtests pass on each of five builds | [Test results](sdk/tests.json) |

Direct single-thread `Generator` calls take 16.0–22.6% less median time than the
baseline in the millisecond profile. Use one generation worker on standard
CPython. The longer free-threaded trials give these factory results:

| Python | Best measured factory groups | Million IDs/s | Six groups, million IDs/s |
|---|---:|---:|---:|
| 3.13.15, GIL disabled | 4 | 3.284 | 2.663 |
| 3.14.7, GIL disabled | 4 | 4.873 | 4.194 |

The SDK default remains six groups. Four is this machine's observed factory
winner; the four- and six-group sample ranges overlap on 3.14t. Its shorter trials
rank eight groups first, so trial length matters. Private unlocked generators
peak at seven workers on 3.13t and four on 3.14t. See the
[recommendation](sdk/recommendation.md) for ranges and ownership costs.

A shared `ThreadSafeGenerator` serializes generation on one lock; more callers
add contention. The GIL also limits Python CPU parallelism on standard builds.
Factory groups and private generators can run concurrently on free-threaded
builds, but scheduling and runtime coordination still cost time. These trials
measure the throughput decline at higher counts without isolating its cause.

## Reproduce the recorded settings

Run from the repository root with the five matching builds installed. Replace
the executable names with their paths if necessary. This command matches the
recorded matrix's counts and sample sizes, including on machines with a different
CPU count:

```sh
python3.14 benchmarks/run.py --threads 1 2 3 4 5 6 7 8 9 \
  --python python3.12 --python python3.13 --python python3.14 \
  --python python3.13t --python python3.14t \
  --baseline benchmarks/sdk/snapshots/baseline.py.txt \
  --repeats 5 --calls 500000 --correctness-calls 100000 \
  --output out/sdk-reproduction
```

The current side always measures the checkout's generator. Use commit `d44de33`
to measure the recorded SDK source; later checkouts measure their own code.
The archived baseline snapshot avoids dependence on a moving `main` branch.
Different hardware, runtime builds, and system load can produce different results.

For longer samples on the deployment machine's free-threaded builds:

```sh
python3.14 benchmarks/run.py --sweep \
  --python python3.13t --python python3.14t \
  --repeats 5 --calls 5000000 --correctness-calls 100000 \
  --output out/sdk-long-samples
```

This portable command includes direct and shared-lock measurements. To repeat
only the recorded 180 factory/private trials, copy
[confirmation-config.json](sdk/confirmation-config.json) to a new file. Set its
`interpreters` values to local executable paths, its `sources.current.path` to
the absolute path of `benchmarks/sdk/snapshots/current.py.txt`, and every job's
`revision` to `file:` followed by that same absolute path. Then run:

```sh
python3.14 benchmarks/pr99/benchmark.py run /path/to/confirmation-config.json \
  --output out/sdk-confirmation.jsonl
```

Create `out/` first if it does not exist and choose a new results filename.
The low-level harness resumes existing output by job index; reuse it only with
the identical configuration.

## Regenerate reports from archived trials

These commands validate and summarize existing archives without rerunning timing
trials or requiring the original interpreter paths:

```sh
python3.14 benchmarks/sdk/report_sdk.py
python3.14 benchmarks/refactor/report_refactor.py
python3.14 benchmarks/pr99/report.py
```

The SDK command verifies 2,095 matrix trials and 180 longer trials against their
configured jobs and source hashes, then rewrites the SDK matrix and confirmation
reports and JSON summaries. Raw archives use `.jsonl.gz`; new portable runs write
uncompressed `results.jsonl`. The other commands regenerate the historical
reports below from their own recorded data.

## Report index

The PR comparison and refactor reports preserve historical source snapshots.
Their numbers do not measure the current factory; use the SDK matrix for that API.

| Experiment | Results |
|---|---|
| Current SDK against main at `4763e1a` | [SDK matrix](sdk/README.md) |
| Current factory and private worker counts | [Longer trials](sdk/confirmation.md), [recommendation](sdk/recommendation.md) |
| Original API versus mandatory locking in PR #99 | [PR comparison](pr99/README.md) |
| Optimized opt-in API across five Python builds | [Refactor matrix](refactor/README.md) |
| Longer free-threaded worker-count trials | [Confirmation](refactor/confirmation.md) |
| Historical M1 Max worker recommendations | [Recommendation](refactor/recommendation.md) |
