# Generator benchmarks

Run from a source checkout with Python 3.12 or newer, including its `venv` and
`ensurepip` modules, and network access:

```sh
python3 benchmarks/run.py --output out/benchmark
```

Every invocation creates a new temporary directory, installs pinned `uv` into a
bootstrap virtual environment, downloads the requested Python builds, and creates
a separate virtual environment for each. Interpreter installations and download
caches stay inside that directory. The runner removes them on success, failure,
or Ctrl+C. It uses no existing uv installation or managed Python environment.
The generator and measurement harness use only the Python standard library.

The default runtime matrix is CPython 3.12.14, 3.13.15, and 3.14.7 with the GIL,
plus free-threaded 3.13.15 and 3.14.7. Setup pins uv to 0.12.11. The bootstrap
Python runs orchestration only; measurements run on the downloaded interpreters.
Versions are declared in [environment.py](environment.py).

## Select Python versions and callers

The default compares one and six callers. `--sweep` tests every count from one
through the available CPU count minus one, with a minimum of one:

```sh
python3 benchmarks/run.py --sweep --output out/benchmark-sweep
```

Pass `--python` once per version to download. A `t` suffix selects a free-threaded
build. Executable paths are rejected. Exact patch versions make the runtime
selection repeatable; requests such as `3.14` resolve the version available to
the pinned uv release.

```sh
python3 benchmarks/run.py --python 3.13.15t --python 3.14.7t \
  --threads 2 4 6 8 --output out/benchmark-free-threaded
```

One caller is always included. CPU availability respects process availability or
affinity where the interpreter exposes it. Six is the benchmark's default
comparison count. The library creates no threads; choose application concurrency
by measuring the complete workload.

For a setup check, run a small matrix. This still provisions a fresh environment:

```sh
python3 benchmarks/run.py --python 3.14.7 --threads 2 --repeats 1 \
  --calls 1000 --correctness-calls 1000 --output out/benchmark-smoke
```

These small samples cannot establish the fastest worker count.

## Compare implementations

Each run measures the checkout's generator. `--baseline` adds a comparison with
a local git revision or a generator source file. Both implementations use the
same bit widths, call counts, and caller counts. Each source is copied into the
results directory and identified by its SHA-256 hash.

This command runs the reference comparison, adapting caller counts to the machine:

```sh
python3 benchmarks/run.py --sweep \
  --baseline 4763e1ac9def84b3abeabba7ddb70f7f48c09d3e \
  --repeats 5 --calls 500000 --correctness-calls 100000 \
  --output out/benchmark-comparison
```

The revision must exist in the local checkout. The default five-build matrix
applies when `--python` is omitted. For longer free-threaded samples:

```sh
python3 benchmarks/run.py --sweep \
  --python 3.13.15t --python 3.14.7t \
  --repeats 5 --calls 5000000 --correctness-calls 100000 \
  --output out/benchmark-long-samples
```

Repeat a command with a new output directory to provision and measure again.
Existing output is never overwritten or resumed. Results under `out/` are
ignored by git. Benchmark artifacts are generated locally rather than committed.

## Results and privacy

| File | Contents |
|---|---|
| `README.md` | Timing tables, sample ranges, correctness totals, and best tested caller counts |
| `results.jsonl` | Every trial's source hash, runtime/GIL metadata, wall/CPU time, and correctness counts |
| `summary.json` | Per-case medians, extrema, and median absolute deviations |
| `config.json`, `snapshots/` | Python version requests, pinned uv version, exact jobs, and measured source |

Generated metadata contains Python versions and relative snapshot filenames.
It omits interpreter paths, checkout paths, and temporary environment paths.
The retained files can be inspected after the temporary environments are removed.

## Measurement method

The benchmark compares these ownership models:

| Mode | Ownership |
|---|---|
| Direct | Unlocked `Generator` or locked `ThreadSafeGenerator`, called by the main thread |
| Shared lock | Application threads call one `ThreadSafeGenerator` with one process-level machine ID |

Each timing case uses seven fresh processes by default, with one million calls
per process. Cases are shuffled within each repetition using a recorded seed;
trials run serially. The harness warms 20,000 calls, uses a real wall clock with
an epoch one day earlier, and disables cyclic GC during measurement. All threaded
callers share the same generator state.

A barrier starts threaded timing, and the last caller stops it. Imports,
initialization, thread creation, and uniqueness checks are outside timing.
`--calls` is the total per trial, divided among callers. One-caller threaded
cases run in a worker thread. Sequence capacity avoids deliberate waiting in
throughput trials; the generator tests cover exhaustion separately.

| Profile | Resolution | Machine IDs | Machine bits | Sequence bits |
|---|---|---|---:|---:|
| millisecond | millisecond | 0 | 0 | 22 |
| four_machines | millisecond | 0, 1, 2, 3 | 2 | 12 |
| second | second | 0 | 0 | 22 |
| minute | minute | 0 | 0 | 24 |
| threaded | millisecond | 0 shared by every caller | 0 | 22 |

Each correctness case runs twice, with one million IDs per trial by default.
`--correctness-calls` changes that count. Shared-lock cases with multiple callers
also run at a 1 µs thread-switch interval, capped at 200,000 IDs.
The checks fail on duplicates or non-increasing IDs within a worker. Their timing
is excluded from performance results. Each trial records runtime and GIL state;
a free-threaded trial with its GIL enabled fails the run.

Reports use median time per ID and aggregate throughput, with sample ranges and
median absolute deviations. Sample ranges are not confidence intervals. Process
CPU time includes worker teardown and joins; it covers a slightly wider interval
than timed generation. Affinity and clock frequency are uncontrolled. Run without
competing CPU workloads and increase `--calls` or `--repeats` for close results.
Encoding and application I/O are outside this benchmark.

## Optimization rationale

| Implementation | Cost or behavior |
|---|---|
| Direct dispatch from `ThreadSafeGenerator` | Calls the generation body under the lock without a `super()` lookup per ID |
| Clock bound at construction | Avoids a Python lambda call; `current_time` remains replaceable |
| Cached integer resolution | Avoids an enum property lookup per clock read; assigning `resolution` updates the divisor |
| Conditional machine-ID packing | Skips the shift when machine bits are zero and preserves the ID layout |

The cached divisor avoids repeated enum access while preserving resolution
reassignment. The benchmark compares the combined optimizations against the
selected baseline. It does not isolate native runtime contention.
Lazy `defaultdict` state preserves initialization when a single-owner generator's
machine list is extended. Eager dictionaries fail that compatibility case.
Plain-dictionary and local-rotation candidates gave inconsistent gains across
builds; unconditional machine-ID packing slowed the zero-machine-bit profile.

A shared lock serializes generation, so extra callers add contention. Standard
CPython's GIL also limits Python CPU parallelism, but it does not make the
unlocked generator safe to share. Machine IDs are process-level allocations;
changing the caller count does not change the benchmark's machine ID or bit
width. Increasing CPU work per ID while throughput falls indicates overhead
without identifying its source.

## Reference measurements

The 2026-09-28 reference run measures generator source at `0c62a73` against
`4763e1a` on a 10-core Apple M1 Max running macOS 26.6.2. It uses the comparison
command above: five samples of 500,000 calls per case, all five Python builds,
and one through nine callers. The matrix contains 850 timing trials and 260
correctness trials. All 26 million checked IDs are unique within their trial
and strictly increasing within each caller. Both free-threaded builds keep the
GIL disabled. Fresh environments are removed after the run.

Direct millisecond calls, median ns/ID; lower is better. These profiles use
machine ID zero, zero machine bits, and 22 sequence bits. The `t` suffix means
a free-threaded build with its GIL disabled.

| Python | Baseline `Generator` | Current `Generator` | Baseline `ThreadSafeGenerator` | Current `ThreadSafeGenerator` |
|---|---:|---:|---:|---:|
| 3.12.14 | 546.3 | 434.3 | 679.5 | 572.0 |
| 3.13.15 | 545.7 | 436.4 | 665.5 | 551.1 |
| 3.14.7 | 466.4 | 363.3 | 577.9 | 438.5 |
| 3.13.15t | 742.1 | 578.5 | 936.5 | 706.1 |
| 3.14.7t | 483.8 | 378.6 | 607.2 | 474.8 |

The unlocked class takes 20.0–22.1% less median time than the baseline; the
internally locked class takes 15.8–24.6% less. The internal lock still adds
per-call cost relative to the current unlocked class.

Current shared `ThreadSafeGenerator`, median aggregate million IDs/s; higher
is better. Every caller uses the same generator and machine ID zero.

| Callers | 3.12.14 | 3.13.15 | 3.14.7 | 3.13.15t | 3.14.7t |
|---:|---:|---:|---:|---:|---:|
| 1 | 1.746 | 1.803 | 2.286 | 1.357 | 1.964 |
| 2 | 1.733 | 1.843 | 2.282 | 0.938 | 1.571 |
| 3 | 1.776 | 1.832 | 2.225 | 0.858 | 1.238 |
| 4 | 1.739 | 1.798 | 2.219 | 0.815 | 1.209 |
| 5 | 1.748 | 1.857 | 2.248 | 0.640 | 0.929 |
| 6 | 1.709 | 1.842 | 2.249 | 0.538 | 0.806 |
| 7 | 1.708 | 1.805 | 2.235 | 0.500 | 0.737 |
| 8 | 1.732 | 1.776 | 2.262 | 0.484 | 0.694 |
| 9 | 1.745 | 1.817 | 2.226 | 0.471 | 0.673 |

Use one caller for generation-only work, since additional callers cannot run
the locked generation body concurrently. On 3.12 and 3.13 with the GIL, the
highest medians occur at three and five callers, respectively, but exceed the
one-caller median by only 1.7% and 3.0%. Their sample ranges overlap the
one-caller ranges, so these measurements do not establish a distinct optimum.
The remaining builds peak at one caller. Both free-threaded builds lose about
60% of their one-caller throughput with six callers.

Application concurrency should follow the complete workload. The generated
report includes both sources at every caller count and all sample ranges;
rerun it on the deployment machine before selecting application thread counts.

SDK-managed workers and bulk generation for a possible HTTP service are tracked
in [issue #124](https://github.com/MihaiBojin/jazzy-fish/issues/124).
