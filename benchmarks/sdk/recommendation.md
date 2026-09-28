# SDK worker recommendation on this M1 Max

Use one generation worker on standard CPython. For the shared factory on this
10-core M1 Max, use `threads=4` on free-threaded Python. Four has the highest
median in the longer trials on both free-threaded builds. Six remains the SDK
default, and callers can select a count explicitly.

| Runtime | Factory groups | Million IDs/s | Six groups, million IDs/s |
|---|---:|---:|---:|
| CPython 3.13.15, GIL disabled | 4 | 3.284 | 2.663 |
| CPython 3.14.7, GIL disabled | 4 | 4.873 | 4.194 |

Each cell comes from five fresh processes generating five million IDs each.
On 3.13t, every four-group sample exceeds every six-group sample. On 3.14t,
their ranges overlap: 4.290–5.222 versus 4.031–4.423 million IDs/s. Four is the
observed winner; these ranges do not establish a statistically distinct optimum.
The shorter 500,000-call matrix ranks eight groups first on 3.14t, which makes
trial length relevant to this recommendation.

Private unlocked generators give higher throughput when the application owns
one generator and disjoint machine IDs per caller. The longer trials peak at
seven workers on 3.13t (6.108 million IDs/s) and four on 3.14t (7.837 million
IDs/s). Six private workers on 3.13t reach 99.1% of the seven-worker median,
with overlapping ranges. The factory adds a group lock and thread-local dispatch
to support one object shared by arbitrary application threads, including callers
above the configured group count.

## Single-thread cost

Direct `Generator.next_id()` uses no lock. The millisecond profile has these
median times against main at `4763e1a`:

| Python | Main ns/ID | Current ns/ID | Time reduction |
|---|---:|---:|---:|
| 3.12.14, GIL enabled | 563.6 | 443.0 | 21.4% |
| 3.13.15, GIL enabled | 520.2 | 437.0 | 16.0% |
| 3.14.7, GIL enabled | 454.0 | 351.5 | 22.6% |
| 3.13.15, GIL disabled | 712.7 | 574.9 | 19.3% |
| 3.14.7, GIL disabled | 479.0 | 385.8 | 19.5% |

The implementation caches the resolution's integer value, binds the clock
directly, and reduces repeated packing work. `ThreadSafeGenerator` calls the
unlocked body directly while holding its lock. Clock replacement and stopped
resolution reassignment remain supported. The [earlier isolated experiments](../refactor/README.md)
measure the optimization candidates; the [current matrix](README.md) measures
their combined behavior with the current rounding and sleeping-wait code.

## Throughput as caller count grows

A shared `ThreadSafeGenerator` serializes calls on one lock. More callers add
contention without executing generation in parallel. Standard CPython also
serializes Python execution through the GIL; the small differences among some
standard-build worker counts do not demonstrate CPU parallelism.

The factory and private generators can execute concurrently on free-threaded
Python. Their throughput still peaks before all nine tested callers. Scheduling,
cache traffic, and runtime coordination are plausible contributors to the decline;
these trials do not profile those mechanisms or attribute the decline to one cause.
All samples, including slow outliers, remain in the raw results.

Run `python3.14 benchmarks/run.py --sweep --output out/benchmark` on the deployment
machine, passing each installed runtime with `--python`. Use `--calls 5000000`
for longer samples. Application I/O and encoding are outside these measurements.
The [confirmation table](confirmation.md) contains every tested count; [tests.json](tests.json)
records 95 passing tests on each of five builds, plus 26 subtests per build.
