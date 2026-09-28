# Run the generator benchmark on your machine

From a source checkout, run with Python 3.12 or newer:

```sh
python3.14 benchmarks/run.py --output out/benchmark
```

The default compares one and six callers on the current interpreter. It measures
unlocked single-thread generation, a shared `ThreadSafeGenerator`, separate
unlocked generators with disjoint machine IDs, and `Generator.threadsafe` with
one group per caller. Each timing case has seven fresh
processes. Correctness runs separately and fails on duplicates or non-increasing
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
  --baseline benchmarks/refactor/snapshots/baseline.py.txt \
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

The benchmark reuses [the measurement harness](pr99/benchmark.py). The integration
tests in [test_benchmark_cli.py](../python/tests/test_benchmark_cli.py) cover execution
from another directory, source comparisons, correctness, and output preservation.

## Recorded experiments

The PR comparison and refactor reports preserve historical source snapshots.
Their numbers do not measure the current factory; use the SDK matrix for that API.

| Experiment | Results |
|---|---|
| Current SDK against main at `4763e1a` | [SDK matrix](sdk/README.md) |
| Current factory and private worker counts | [Longer trials](sdk/confirmation.md), [recommendation](sdk/recommendation.md) |
| Original API versus mandatory locking in PR #99 | [PR comparison](pr99/README.md) |
| Optimized opt-in API across five Python builds | [Refactor matrix](refactor/README.md) |
| Longer free-threaded worker-count trials | [Confirmation](refactor/confirmation.md) |
| M1 Max worker recommendations | [Recommendation](refactor/recommendation.md) |
