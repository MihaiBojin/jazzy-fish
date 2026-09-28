# Generator benchmark for PR #99

PR #99's `Generator` takes 16.5% to 26.9% more time per ID than the original unlocked `Generator` in the direct single-thread millisecond workload. The original opt-in `ThreadSafeGenerator` passes every shared-instance uniqueness check in this matrix.

The original `Generator` provides the unlocked path. The original `ThreadSafeGenerator` locks shared calls. PR #99 puts a lock in `Generator.next_id()`.

These results measure the exact PR base and head, independently of the current checkout. No production source files are modified.

## Machine and interpreters

Apple M1 Max, 10 physical and logical cores (8 performance, 2 efficiency), 64 GiB RAM, macOS 26.6.2 (25G83), arm64. The machine used AC power with normal power mode. CPU affinity and clock frequency were not pinned. Other machine activity was not stopped.

Trials ran from 2026-09-27T21:46:53Z to 2026-09-27T22:04:04Z. The recorded one-minute system load ranged from 5.00 to 26.31; load average includes benchmark activity and is not a CPU utilization percentage.

| Label | CPython version | GIL enabled | Build |
|---|---|---|---|
| 3.12 | 3.12.14 | True | 3.12.14 (main, Sep  1 2026, 14:09:38) [Clang 22.1.3 ] |
| 3.13 | 3.13.15 | True | 3.13.15 (main, Sep  1 2026, 14:05:45) [Clang 22.1.3 ] |
| 3.14 | 3.14.7 | True | 3.14.7 (main, Sep  1 2026, 14:05:28) [Clang 22.1.3 ] |
| 3.13t | 3.13.15 | False | 3.13.15 experimental free-threading build (main, Sep  1 2026, 14:05:50) [Clang 22.1.3 ] |
| 3.14t | 3.14.7 | False | 3.14.7 free-threading build (main, Sep  1 2026, 14:07:44) [Clang 22.1.3 ] |

All interpreters are uv-managed python-build-standalone arm64 builds. Free-threaded processes were checked with `sys._is_gil_enabled()` after their trials; the GIL remained disabled. Comparisons between implementations within one runtime isolate the API choice better than comparisons between different Python builds.

## Inputs and measurement

| Input | Value |
|---|---|
| Base revision | `95affdf00dd2c4b3a0a6ffa2c7185aaaa03c1761` |
| PR head revision | `7cc9e250eb01f6434ceeb1224475a2b10953777d` |
| Timing trials | 1,260 |
| Correctness trials | 315 |
| Calls in timing trials | 672,000,000 |
| IDs checked for uniqueness | 255,000,000 |
| Timing repetitions per case | 7 fresh processes |
| Direct single-thread calls per trial | 1,000,000 |
| Threaded calls per trial | 300,000 total, divided evenly among workers |
| Threads | 1, 2, 4, 6, 8, 9 |
| Default-interval correctness | 2 trials of 1,000,000 IDs per case |
| Short-interval correctness | 200,000 IDs per case at `sys.setswitchinterval(1e-6)` |

Each timing trial imports an immutable generator snapshot, warms the call path with 20,000 calls, creates fresh state, collects garbage, then disables cyclic GC during measurement. Calls use a bound `next_id` method. Timing excludes imports, initialization, thread creation, and duplicate checking. The timed loop discards IDs; correctness trials retain IDs and include list construction in their separate timings.

`time.perf_counter_ns()` measures elapsed time. Thread workers start through a barrier; elapsed time ends when the last worker finishes. The table values are aggregate throughput, not throughput per worker or individual request latency. One-worker threaded cases run in a worker thread; direct single-thread cases run in the main thread. Timing jobs are shuffled within each repetition across runtimes, implementations, configurations, and thread counts, with a fixed seed. Only one trial process runs at a time.

The normal switch interval is 5 ms. The short-interval cases target GIL scheduling; on free-threaded builds they serve as extra correctness repetitions. Their timings are excluded from the performance tables. Single-thread configurations use a real wall clock and enough sequence capacity to avoid deliberate rate limiting. The epoch is one day before trial initialization. No encoder work or application I/O is measured.

| Profile | Resolution | Machine IDs | Machine bits | Sequence bits |
|---|---|---|---|---|
| millisecond | MILLISECOND | [0] | 0 | 22 |
| four_machines | MILLISECOND | [0, 1, 2, 3] | 2 | 12 |
| second | SECOND | [0] | 0 | 22 |
| minute | MINUTE | [0] | 0 | 24 |
| threaded | MILLISECOND | [0] | 4 | 22 |

The private-generator control gives each worker a separate unlocked generator and a distinct machine ID from 0 through `threads - 1`. It uses the threaded profile's four machine bits, constructs and warms each instance inside its worker, and requires the application to own those distinct IDs. Other threaded variants share one instance using machine ID 0. The JSON `configuration` field contains the profile defaults; `variant=private` applies this per-worker ID assignment.

## Direct single-thread timings

Times are median ns/ID, with the full observed range in parentheses. PR overhead is the median of the seven percentage differences paired by repetition. These are measurements on this machine, not universal latency guarantees.

### millisecond

| Python | Original Generator | Original ThreadSafeGenerator | PR Generator | PR overhead over unlocked |
|---|---:|---:|---:|---:|
| 3.12 | 522.2 (518.9–525.9) | 678.7 (675.7–682.5) | 662.7 (657.5–715.2) | +26.9% |
| 3.13 | 508.9 (507.9–514.1) | 638.9 (636.3–647.6) | 620.7 (619.5–627.6) | +21.9% |
| 3.14 | 453.2 (450.2–455.7) | 560.6 (556.6–565.1) | 537.9 (531.1–546.6) | +18.7% |
| 3.13t | 717.7 (711.6–741.3) | 903.5 (902.0–926.8) | 835.2 (828.9–851.4) | +16.5% |
| 3.14t | 475.7 (472.4–478.1) | 596.7 (590.8–606.3) | 573.6 (567.7–577.7) | +20.5% |

### four_machines

| Python | Original Generator | Original ThreadSafeGenerator | PR Generator | PR overhead over unlocked |
|---|---:|---:|---:|---:|
| 3.12 | 560.1 (557.3–566.0) | 716.0 (713.4–726.6) | 692.8 (688.1–726.4) | +24.2% |
| 3.13 | 550.8 (545.7–554.6) | 679.5 (670.3–684.6) | 662.0 (656.8–664.4) | +20.4% |
| 3.14 | 498.9 (497.4–502.0) | 604.1 (596.7–610.2) | 582.5 (576.6–587.3) | +16.7% |
| 3.13t | 752.7 (748.0–757.6) | 944.5 (936.0–945.1) | 865.2 (862.5–881.5) | +15.1% |
| 3.14t | 519.3 (515.2–525.7) | 639.5 (637.6–645.2) | 614.2 (606.2–620.2) | +18.3% |

### second

| Python | Original Generator | Original ThreadSafeGenerator | PR Generator | PR overhead over unlocked |
|---|---:|---:|---:|---:|
| 3.12 | 523.2 (516.7–526.9) | 685.7 (682.6–711.4) | 660.9 (656.7–674.7) | +26.6% |
| 3.13 | 511.2 (507.8–514.6) | 640.8 (634.4–647.3) | 618.9 (616.4–620.3) | +21.1% |
| 3.14 | 455.4 (449.9–463.6) | 559.8 (552.7–564.4) | 535.9 (533.2–540.5) | +17.9% |
| 3.13t | 719.2 (716.9–738.1) | 912.7 (904.2–939.1) | 833.7 (832.1–845.2) | +15.9% |
| 3.14t | 479.1 (475.6–490.1) | 599.9 (594.8–607.9) | 573.4 (571.4–580.7) | +20.1% |

### minute

| Python | Original Generator | Original ThreadSafeGenerator | PR Generator | PR overhead over unlocked |
|---|---:|---:|---:|---:|
| 3.12 | 523.2 (521.0–528.6) | 684.7 (678.1–704.3) | 661.6 (653.0–666.9) | +26.5% |
| 3.13 | 510.5 (509.3–520.5) | 641.2 (634.2–642.9) | 624.4 (616.6–630.5) | +22.1% |
| 3.14 | 453.5 (450.5–460.4) | 560.5 (557.7–575.0) | 537.3 (534.0–543.9) | +18.3% |
| 3.13t | 717.5 (710.7–720.5) | 914.3 (903.1–918.3) | 837.7 (834.7–838.5) | +16.7% |
| 3.14t | 477.1 (473.9–480.8) | 603.6 (598.2–620.6) | 576.8 (569.6–588.4) | +20.4% |

## Threaded throughput

Values are median millions of IDs/second. Both shared locked implementations and the private-generator control passed every uniqueness trial. The unlocked shared generator is excluded from this comparison because its use across threads produces duplicates.

### Python 3.12

| Threads | Original ThreadSafeGenerator | PR Generator | Private Generator per worker |
|---:|---:|---:|---:|
| 1 | 1.391 | 1.441 | 1.779 |
| 2 | 1.404 | 1.440 | 1.762 |
| 4 | 1.398 | 1.436 | 1.765 |
| 6 | 1.392 | 1.432 | 1.759 |
| 8 | 1.399 | 1.436 | 1.758 |
| 9 | 1.388 | 1.433 | 1.751 |

Timing spread for the two shared locked implementations, in ns/ID:

| Threads | Original ThreadSafeGenerator median (range) | PR Generator median (range) |
|---:|---:|---:|
| 1 | 719.0 (707.2–730.5) | 694.2 (691.3–759.0) |
| 2 | 712.3 (710.1–717.3) | 694.6 (690.9–726.9) |
| 4 | 715.1 (708.7–718.3) | 696.2 (692.4–742.0) |
| 6 | 718.6 (712.6–731.0) | 698.3 (689.2–722.6) |
| 8 | 714.7 (709.8–718.2) | 696.6 (694.7–711.3) |
| 9 | 720.4 (712.1–749.7) | 697.6 (692.4–700.8) |

### Python 3.13

| Threads | Original ThreadSafeGenerator | PR Generator | Private Generator per worker |
|---:|---:|---:|---:|
| 1 | 1.484 | 1.510 | 1.843 |
| 2 | 1.473 | 1.516 | 1.822 |
| 4 | 1.472 | 1.511 | 1.815 |
| 6 | 1.466 | 1.515 | 1.804 |
| 8 | 1.467 | 1.503 | 1.792 |
| 9 | 1.475 | 1.515 | 1.803 |

Timing spread for the two shared locked implementations, in ns/ID:

| Threads | Original ThreadSafeGenerator median (range) | PR Generator median (range) |
|---:|---:|---:|
| 1 | 674.0 (669.3–682.3) | 662.5 (653.7–710.0) |
| 2 | 678.7 (673.1–695.1) | 659.8 (657.0–669.1) |
| 4 | 679.1 (672.5–681.2) | 661.6 (653.9–671.5) |
| 6 | 682.3 (674.4–684.0) | 660.2 (656.3–664.6) |
| 8 | 681.4 (673.6–722.0) | 665.4 (658.7–728.7) |
| 9 | 677.9 (673.4–684.9) | 660.1 (658.6–664.2) |

### Python 3.14

| Threads | Original ThreadSafeGenerator | PR Generator | Private Generator per worker |
|---:|---:|---:|---:|
| 1 | 1.678 | 1.755 | 2.032 |
| 2 | 1.675 | 1.748 | 1.985 |
| 4 | 1.677 | 1.750 | 1.984 |
| 6 | 1.669 | 1.740 | 1.998 |
| 8 | 1.669 | 1.735 | 1.995 |
| 9 | 1.663 | 1.724 | 1.981 |

Timing spread for the two shared locked implementations, in ns/ID:

| Threads | Original ThreadSafeGenerator median (range) | PR Generator median (range) |
|---:|---:|---:|
| 1 | 596.0 (591.0–603.6) | 569.9 (567.1–575.0) |
| 2 | 596.9 (592.9–653.4) | 571.9 (567.3–576.7) |
| 4 | 596.4 (588.0–648.3) | 571.3 (568.9–587.2) |
| 6 | 599.2 (592.9–602.6) | 574.6 (570.8–586.0) |
| 8 | 599.1 (595.0–603.9) | 576.4 (572.7–583.5) |
| 9 | 601.3 (597.1–606.2) | 580.1 (569.2–684.6) |

### Python 3.13t

| Threads | Original ThreadSafeGenerator | PR Generator | Private Generator per worker |
|---:|---:|---:|---:|
| 1 | 1.001 | 1.086 | 1.316 |
| 2 | 0.696 | 0.784 | 1.593 |
| 4 | 0.569 | 0.629 | 1.399 |
| 6 | 0.428 | 0.469 | 0.951 |
| 8 | 0.376 | 0.400 | 0.681 |
| 9 | 0.366 | 0.390 | 0.634 |

Timing spread for the two shared locked implementations, in ns/ID:

| Threads | Original ThreadSafeGenerator median (range) | PR Generator median (range) |
|---:|---:|---:|
| 1 | 998.7 (992.5–1003.6) | 921.0 (918.5–929.2) |
| 2 | 1437.5 (1368.6–1470.0) | 1275.7 (1245.8–1324.7) |
| 4 | 1755.9 (1700.7–1760.9) | 1590.2 (1544.4–1648.2) |
| 6 | 2338.3 (2240.9–2368.6) | 2134.2 (2095.6–2197.2) |
| 8 | 2658.7 (2613.4–2725.0) | 2499.9 (2436.9–2559.6) |
| 9 | 2731.4 (2609.8–2754.6) | 2567.2 (2427.1–2609.7) |

### Python 3.14t

| Threads | Original ThreadSafeGenerator | PR Generator | Private Generator per worker |
|---:|---:|---:|---:|
| 1 | 1.485 | 1.565 | 1.845 |
| 2 | 1.041 | 1.127 | 2.199 |
| 4 | 0.826 | 0.864 | 1.958 |
| 6 | 0.619 | 0.657 | 1.784 |
| 8 | 0.512 | 0.534 | 1.420 |
| 9 | 0.490 | 0.522 | 1.328 |

Timing spread for the two shared locked implementations, in ns/ID:

| Threads | Original ThreadSafeGenerator median (range) | PR Generator median (range) |
|---:|---:|---:|
| 1 | 673.6 (665.6–681.4) | 639.2 (635.2–646.6) |
| 2 | 961.0 (945.3–972.0) | 887.2 (870.0–897.3) |
| 4 | 1211.1 (1184.4–1240.0) | 1156.8 (1137.1–1184.0) |
| 6 | 1616.6 (1587.7–1637.0) | 1522.4 (1491.3–1569.2) |
| 8 | 1952.5 (1782.5–2002.0) | 1871.2 (1844.9–1885.2) |
| 9 | 2042.2 (1936.1–2094.3) | 1916.3 (1857.7–1975.0) |

## Unlocked shared-generator correctness

The following table is a misuse control. The original unlocked class is not the API for sharing one instance across threads. A zero count in one experiment does not prove thread safety. The throughput column comes from separate timing trials, so it is not a measure of unique IDs/second.

| Python | Threads | Raw million calls/s | Duplicates at normal interval / IDs | Duplicates at short interval / IDs |
|---|---:|---:|---:|---:|
| 3.12 | 1 | 1.778 | 0 / 2,000,000 (0.000%) | — |
| 3.12 | 2 | 1.745 | 6,575 / 2,000,000 (0.329%) | 54,644 / 200,000 (27.322%) |
| 3.12 | 4 | 1.764 | 5,142 / 2,000,000 (0.257%) | 93,548 / 200,000 (46.774%) |
| 3.12 | 6 | 1.755 | 5,594 / 2,000,000 (0.280%) | 97,560 / 200,000 (48.780%) |
| 3.12 | 8 | 1.749 | 4,378 / 2,000,000 (0.219%) | 89,176 / 200,000 (44.588%) |
| 3.12 | 9 | 1.751 | 2,579 / 2,000,000 (0.129%) | 89,107 / 200,000 (44.553%) |
| 3.13 | 1 | 1.845 | 0 / 2,000,000 (0.000%) | — |
| 3.13 | 2 | 1.812 | 7,810 / 2,000,000 (0.391%) | 47,442 / 200,000 (23.721%) |
| 3.13 | 4 | 1.805 | 3,647 / 2,000,000 (0.182%) | 93,153 / 200,000 (46.577%) |
| 3.13 | 6 | 1.811 | 5,865 / 2,000,000 (0.293%) | 90,828 / 200,000 (45.414%) |
| 3.13 | 8 | 1.808 | 5,190 / 2,000,000 (0.260%) | 87,551 / 200,000 (43.776%) |
| 3.13 | 9 | 1.814 | 3,808 / 2,000,000 (0.190%) | 85,526 / 200,000 (42.763%) |
| 3.14 | 1 | 2.030 | 0 / 2,000,000 (0.000%) | — |
| 3.14 | 2 | 1.984 | 8,500 / 2,000,000 (0.425%) | 43,505 / 200,000 (21.753%) |
| 3.14 | 4 | 1.969 | 3,006 / 2,000,000 (0.150%) | 95,329 / 200,000 (47.664%) |
| 3.14 | 6 | 1.999 | 2,001 / 2,000,000 (0.100%) | 93,905 / 200,000 (46.953%) |
| 3.14 | 8 | 1.987 | 4,459 / 2,000,000 (0.223%) | 89,367 / 200,000 (44.684%) |
| 3.14 | 9 | 1.990 | 3,957 / 2,000,000 (0.198%) | 87,566 / 200,000 (43.783%) |
| 3.13t | 1 | 1.262 | 0 / 2,000,000 (0.000%) | — |
| 3.13t | 2 | 0.646 | 767,353 / 2,000,000 (38.368%) | 76,524 / 200,000 (38.262%) |
| 3.13t | 4 | 0.382 | 1,252,188 / 2,000,000 (62.609%) | 125,554 / 200,000 (62.777%) |
| 3.13t | 6 | 0.247 | 1,361,632 / 2,000,000 (68.082%) | 137,478 / 200,000 (68.739%) |
| 3.13t | 8 | 0.185 | 1,450,148 / 2,000,000 (72.507%) | 144,611 / 200,000 (72.305%) |
| 3.13t | 9 | 0.188 | 1,468,103 / 2,000,000 (73.405%) | 147,516 / 200,000 (73.758%) |
| 3.14t | 1 | 1.840 | 0 / 2,000,000 (0.000%) | — |
| 3.14t | 2 | 1.692 | 696,345 / 2,000,000 (34.817%) | 71,266 / 200,000 (35.633%) |
| 3.14t | 4 | 1.318 | 1,270,887 / 2,000,000 (63.544%) | 127,496 / 200,000 (63.748%) |
| 3.14t | 6 | 0.924 | 1,492,434 / 2,000,000 (74.622%) | 149,525 / 200,000 (74.763%) |
| 3.14t | 8 | 0.881 | 1,565,470 / 2,000,000 (78.273%) | 158,959 / 200,000 (79.480%) |
| 3.14t | 9 | 0.834 | 1,589,258 / 2,000,000 (79.463%) | 163,073 / 200,000 (81.537%) |

The original `ThreadSafeGenerator`, PR `Generator`, and private-generator control collectively produced **zero duplicate IDs across 190,000,000 checked IDs**. Each worker's IDs were strictly increasing. Uniqueness was checked within each trial; each fresh trial starts independent state.

## Verification

The AST of the original `Generator.next_id()` body matches PR `Generator._next_id_locked()` after stripping the docstring. All five profiles produce identical 10,000-ID deterministic sequences across the original unlocked class, original locked class, and PR class on every interpreter. The deprecated PR subclass inherits the same `next_id` method as PR `Generator`, so a separate timing series for that alias would measure the same call path.

| Python | Base generator tests | PR generator and concurrency tests |
|---|---:|---:|
| 3.12 | 7 passed | 10 passed |
| 3.13 | 7 passed | 10 passed |
| 3.14 | 7 passed | 10 passed |
| 3.13t | 7 passed | 10 passed |
| 3.14t | 7 passed | 10 passed |

These checks cover the generator component. They do not run the encoder, packaging, or CLI test suites.

## Reproduction and files

The scripts use only the Python standard library. Both git revisions must be available locally. Update interpreter paths in `config.json` for another machine. Use a new output path for a fresh run; an existing output file resumes completed jobs.

```sh
python3 benchmarks/pr99/benchmark.py run benchmarks/pr99/config.json --output /tmp/pr99-results.jsonl
python3 benchmarks/pr99/benchmark.py summarize /tmp/pr99-results.jsonl
python3 benchmarks/pr99/verify.py
```

Run `verify.py` with each interpreter listed in `config.json` to repeat the verification across all five builds.

`results.jsonl.gz` contains every raw trial, source hashes, runtime and GIL metadata, elapsed time, CPU time, worker start/finish spreads, and correctness counts. `summary.json` contains per-case medians, extrema, and median absolute deviations. `verification.json` contains test output for all five interpreters. `config.json` records the run settings. `report.py` validates matrix completeness and writes this report.

Python's documentation distinguishes runtime GIL state from build capability and describes internal locks on built-in containers. The duplicate-ID race is a compound generator-state race; it does not establish interpreter-level dictionary corruption. See [Python free threading](https://docs.python.org/3/howto/free-threading-python.html).
