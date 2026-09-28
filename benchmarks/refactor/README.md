# Opt-in generator performance

`Generator` performs unlocked generation. `ThreadSafeGenerator` serializes calls with one lock and directly dispatches to the same generation method. Both bind `time.time` at construction, cache the resolution divisor, and pack IDs with one conditional machine-ID shift. Assigning `current_time` remains supported; assigning `resolution` updates the cached divisor.

## Machine and method

Apple M1 Max, 10 physical/logical cores: 8 performance and 2 efficiency cores, 64 GiB RAM, macOS 26.6.2 arm64. AC power, normal power mode. No CPU affinity or clock-frequency control. This was a live workstation; comparisons use interleaved baseline and optimized trials from this run.

The baseline is commit `3c997cb8b0a81f83336ed0dae8ad82f3790ca91d`. The optimized source SHA-256 is `7bf3b62e3e5915616854736890ecf53303b763417f9d91d5f8da98ff6ce7a01a`. Both sources are in [snapshots](snapshots/). Every raw record contains its source hash and runtime metadata.

Trials ran from 2026-09-27T23:31:08Z to 2026-09-27T23:53:33Z. Recorded one-minute load average ranged from 2.55 to 12.80; it includes benchmark activity and is not CPU utilization.

| Label | CPython | GIL enabled |
|---|---|---|
| 3.12 | 3.12.14 | True |
| 3.13 | 3.13.15 | True |
| 3.14 | 3.14.7 | True |
| 3.13t | 3.13.15 | False |
| 3.14t | 3.14.7 | False |

Each case has seven fresh-process timing trials, shuffled within each repetition. Only one trial runs at a time. A trial warms 20,000 calls, uses a real wall clock and an epoch one day earlier, and disables cyclic GC during measurement. Free-threaded runtimes are checked after every trial to ensure the GIL is disabled.

Direct cases perform 1,000,000 calls. Threaded cases divide 500,000 calls among workers. A barrier starts the clock, and the last worker's completion ends it. Imports, initialization, thread creation, and correctness checks are outside the timing interval. Values are aggregate throughput from a bound-method loop, excluding encoding and application I/O. One-worker threaded cases run in a worker thread; direct cases run in the main thread.

| Profile | Resolution | Machine IDs | Machine bits | Sequence bits |
|---|---|---|---:|---:|
| millisecond | millisecond | 0 | 0 | 22 |
| four_machines | millisecond | 0, 1, 2, 3 | 2 | 12 |
| second | second | 0 | 0 | 22 |
| minute | minute | 0 | 0 | 24 |
| threaded | millisecond | 0 shared, or worker index private | 4 | 22 |

The private case constructs and warms one unlocked generator inside each worker. Machine IDs are disjoint across workers. The shared case uses one `ThreadSafeGenerator`. Both configurations use the same bit widths. Sequence capacities avoid deliberate waiting in the throughput workloads; boundary tests exercise exhaustion separately.

## Single-thread cost

Values are median nanoseconds per ID. The percentage is the median reduction in time per ID, paired by repetition. Full extrema and median absolute deviations are in [summary.json](summary.json). Lower time is better.

### millisecond

| Python | Generator baseline → optimized | Time reduction | ThreadSafeGenerator baseline → optimized | Time reduction |
|---|---:|---:|---:|---:|
| 3.12 | 614.7 → 491.7 | 19.9% | 792.6 → 655.6 | 18.3% |
| 3.13 | 600.0 → 478.3 | 20.2% | 752.8 → 607.7 | 18.9% |
| 3.14 | 530.0 → 409.4 | 22.9% | 654.2 → 504.9 | 22.9% |
| 3.13t | 840.0 → 648.3 | 22.6% | 1063.3 → 795.8 | 24.9% |
| 3.14t | 556.4 → 433.2 | 21.9% | 705.3 → 542.4 | 22.5% |

### four_machines

| Python | Generator baseline → optimized | Time reduction | ThreadSafeGenerator baseline → optimized | Time reduction |
|---|---:|---:|---:|---:|
| 3.12 | 651.8 → 537.5 | 17.6% | 831.0 → 691.0 | 16.8% |
| 3.13 | 644.6 → 527.6 | 18.1% | 797.2 → 656.1 | 17.6% |
| 3.14 | 583.6 → 457.3 | 21.5% | 707.1 → 555.3 | 21.5% |
| 3.13t | 879.4 → 690.2 | 21.5% | 1115.5 → 835.1 | 25.0% |
| 3.14t | 610.2 → 481.7 | 21.1% | 751.5 → 590.2 | 21.3% |

### second

| Python | Generator baseline → optimized | Time reduction | ThreadSafeGenerator baseline → optimized | Time reduction |
|---|---:|---:|---:|---:|
| 3.12 | 615.4 → 491.9 | 20.2% | 800.7 → 656.2 | 17.9% |
| 3.13 | 600.8 → 480.6 | 20.0% | 759.5 → 607.2 | 20.1% |
| 3.14 | 533.5 → 408.8 | 23.1% | 655.6 → 505.6 | 23.2% |
| 3.13t | 842.8 → 654.9 | 22.4% | 1065.8 → 798.6 | 25.1% |
| 3.14t | 558.8 → 437.0 | 22.2% | 709.0 → 546.0 | 22.5% |

### minute

| Python | Generator baseline → optimized | Time reduction | ThreadSafeGenerator baseline → optimized | Time reduction |
|---|---:|---:|---:|---:|
| 3.12 | 616.8 → 493.1 | 19.8% | 797.2 → 657.7 | 17.2% |
| 3.13 | 600.4 → 479.5 | 20.2% | 753.3 → 608.5 | 19.1% |
| 3.14 | 534.7 → 409.6 | 23.2% | 654.7 → 505.8 | 22.8% |
| 3.13t | 841.7 → 652.4 | 22.5% | 1066.4 → 801.2 | 24.8% |
| 3.14t | 560.0 → 435.8 | 22.2% | 701.2 → 545.7 | 22.1% |

## Thread counts

Values are median million IDs/second, baseline → optimized. Higher throughput is better. Every integer from one through nine workers is tested.

### One shared ThreadSafeGenerator

| Threads | 3.12 | 3.13 | 3.14 | 3.13t | 3.14t |
|---:|---:|---:|---:|---:|---:|
| 1 | 1.201 → 1.441 | 1.260 → 1.538 | 1.432 → 1.836 | 0.852 → 1.138 | 1.266 → 1.640 |
| 2 | 1.195 → 1.438 | 1.257 → 1.529 | 1.425 → 1.833 | 0.586 → 0.800 | 0.910 → 1.271 |
| 3 | 1.195 → 1.437 | 1.250 → 1.530 | 1.432 → 1.827 | 0.558 → 0.762 | 0.814 → 1.053 |
| 4 | 1.193 → 1.429 | 1.262 → 1.519 | 1.429 → 1.828 | 0.493 → 0.682 | 0.720 → 0.974 |
| 5 | 1.196 → 1.432 | 1.251 → 1.527 | 1.426 → 1.823 | 0.388 → 0.511 | 0.552 → 0.756 |
| 6 | 1.194 → 1.433 | 1.255 → 1.521 | 1.426 → 1.816 | 0.345 → 0.445 | 0.476 → 0.657 |
| 7 | 1.192 → 1.434 | 1.248 → 1.520 | 1.421 → 1.819 | 0.320 → 0.410 | 0.435 → 0.576 |
| 8 | 1.186 → 1.424 | 1.251 → 1.520 | 1.416 → 1.818 | 0.306 → 0.378 | 0.406 → 0.527 |
| 9 | 1.185 → 1.431 | 1.249 → 1.518 | 1.419 → 1.814 | 0.298 → 0.381 | 0.406 → 0.515 |

### One Generator per worker

| Threads | 3.12 | 3.13 | 3.14 | 3.13t | 3.14t |
|---:|---:|---:|---:|---:|---:|
| 1 | 1.523 → 1.878 | 1.572 → 1.922 | 1.729 → 2.224 | 1.120 → 1.473 | 1.603 → 2.116 |
| 2 | 1.513 → 1.863 | 1.551 → 1.909 | 1.716 → 2.199 | 1.437 → 2.609 | 2.125 → 3.497 |
| 3 | 1.502 → 1.853 | 1.543 → 1.905 | 1.707 → 2.182 | 1.424 → 3.300 | 1.933 → 4.286 |
| 4 | 1.494 → 1.852 | 1.537 → 1.898 | 1.706 → 2.175 | 1.319 → 3.955 | 1.882 → 5.211 |
| 5 | 1.498 → 1.856 | 1.541 → 1.891 | 1.700 → 2.189 | 1.009 → 4.668 | 1.692 → 5.786 |
| 6 | 1.495 → 1.846 | 1.538 → 1.886 | 1.700 → 2.175 | 0.863 → 5.050 | 1.593 → 5.899 |
| 7 | 1.500 → 1.842 | 1.535 → 1.893 | 1.691 → 2.173 | 0.717 → 5.553 | 1.419 → 5.475 |
| 8 | 1.500 → 1.841 | 1.532 → 1.879 | 1.697 → 2.172 | 0.616 → 5.205 | 1.279 → 4.626 |
| 9 | 1.487 → 1.839 | 1.507 → 1.863 | 1.698 → 2.169 | 0.591 → 4.699 | 1.187 → 3.971 |

### Observed peaks in the full matrix

| Python | Shared best count | Shared M IDs/s | Private best count | Private M IDs/s | Private speedup over one worker |
|---|---:|---:|---:|---:|---:|
| 3.12 | 1 | 1.441 | 1 | 1.878 | 1.00× |
| 3.13 | 1 | 1.538 | 1 | 1.922 | 1.00× |
| 3.14 | 1 | 1.836 | 1 | 2.224 | 1.00× |
| 3.13t | 1 | 1.138 | 7 | 5.553 | 3.77× |
| 3.14t | 1 | 1.640 | 6 | 5.899 | 2.79× |

These are observed medians on this machine. Small differences within the trial spread do not establish a distinct optimum. See [recommendation.md](recommendation.md) for the worker recommendation and longer confirmation trials.

## Correctness

The matrix contains 1,820 timing trials and 220 correctness trials. Timing trials performed 1,190,000,000 calls.

| Configuration | IDs checked | Duplicates | Non-increasing IDs within a worker |
|---|---:|---:|---:|
| Shared ThreadSafeGenerator | 98,000,000 | 0 | 0 |
| Separate Generator instances | 90,000,000 | 0 | 0 |

Correctness trials check the optimized snapshot only. They retain all IDs and check exact uniqueness plus strictly increasing values within each worker. Each configuration has two trials of 1,000,000 IDs. Shared cases with 2–9 workers also run 200,000 IDs with a 1 µs switch interval. Correctness timings are excluded from performance tables. These checks cover the measured configurations; they are not a proof for arbitrary clock behavior or machine-ID assignments.

All 41 unit tests pass on each of the five builds, for 205 executions. [tests.json](tests.json) records the commands' runtimes and results. Eight new tests cover clock boundaries, per-machine sequences, zero-bit configurations, replaceable clocks, resolution assignment, disjoint ID domains, extending a machine list, and lock serialization when the clock yields. The clock-boundary and concurrency checks were also verified against intentional in-memory faults before the refactor.

## Optimization experiments

[stages-results.jsonl.gz](stages-results.jsonl.gz), [packing-results.jsonl.gz](packing-results.jsonl.gz), and [conditional-results.jsonl.gz](conditional-results.jsonl.gz) record 900 preliminary timing trials on 3.12, 3.14, and 3.14t, with five repetitions per case. The stage snapshots and matching config files preserve their exact inputs.

Direct dispatch avoids a `super()` lookup in the locked path. Binding the clock removes a Python lambda call. Caching the resolution removes an enum property access on every clock read; it has the largest measured effect on private free-threaded scaling. Reduced access to shared enum state is a plausible contributor to that scaling gain; no native contention profiler was used to isolate the mechanism.

The conditional packing candidate reduces median time by 1.7–3.0% across its 12 runtime/profile/class combinations. Plain dictionary candidates and local rotation variables do not give consistent gains across builds. An eager dictionary candidate also fails the machine-list-extension compatibility test. The production implementation uses the original lazy defaultdict state. Unconditional machine-ID packing slows the zero-machine-bit profile; production retains that condition.

## Reproduction

Use the interpreter paths in [config.json](config.json), or replace them with matching builds. Run from the repository root:

```sh
python3 benchmarks/pr99/benchmark.py run benchmarks/refactor/config.json --output /tmp/refactor-results.jsonl
PYTHONPATH=python/src /path/to/python -m unittest discover -s python/tests
python3 benchmarks/refactor/report_refactor.py
```

The first command writes a new experiment to `/tmp`; the report command validates and summarizes the archived repository results. [results.jsonl.gz](results.jsonl.gz) contains all raw trials, including source hashes, GIL state, wall/CPU times, worker timing spreads, and correctness counts. [report_refactor.py](report_refactor.py) checks completeness against every configured job and verifies source hashes before generating this report.
