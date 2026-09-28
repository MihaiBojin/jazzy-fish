# Worker recommendation

Use one generation worker on standard CPython. On this M1 Max, use seven private
workers on free-threaded 3.13 and six on free-threaded 3.14 for maximum measured
integer-ID throughput. Each private worker owns one unlocked `Generator` and a
distinct machine ID.

| Python | Recommended workers | Median million IDs/s | Measurement |
|---|---:|---:|---|
| 3.12.14, GIL enabled | 1 | 1.878 | Seven trials of 500,000 IDs |
| 3.13.15, GIL enabled | 1 | 1.922 | Seven trials of 500,000 IDs |
| 3.14.7, GIL enabled | 1 | 2.224 | Seven trials of 500,000 IDs |
| 3.13.15, GIL disabled | 7 | 5.654 | Five trials of 5,000,000 IDs |
| 3.14.7, GIL disabled | 6 | 6.079 | Five trials of 5,000,000 IDs |

Seven and six have the highest median throughput in both the full matrix and the
longer confirmation. On 3.13t, all five seven-worker samples exceed every
six-worker and eight-worker sample. On 3.14t, six workers lead five workers by
3.8% in median throughput, with overlapping observed ranges. Six is the measured
winner for this workload; the smaller margin warrants remeasurement in an
application that competes for CPU time.

The [full matrix](README.md) compares both implementations at every count from
one through nine. The [longer confirmation](confirmation.md) repeats every count
on both free-threaded builds and includes sample ranges and CPU costs. The machine
has ten cores, eight performance and two efficiency, and ran as a live workstation
without affinity or frequency controls. These counts apply to integer generation
with the tested bit allocation. Encoding, I/O, different hardware, and deliberate
sequence exhaustion require measurement of the complete workload.

## Sharing an instance

Use `ThreadSafeGenerator` when application threads need to share an instance.
One caller gives the highest shared-instance median on all five builds. A pool
whose workers all call the same generator adds serialization and scheduling cost;
it provides no parallel generation path. Application threads doing other work
can still call the shared instance safely.

## Why throughput declines above the peak

The shared generator holds one lock through each `next_id()` call. More callers
compete for the same critical section. On 3.14t, shared throughput falls from
1.640 million IDs/s with one caller to 0.515 million with nine in the full matrix.

Private generators remove that shared application lock, but additional workers
still consume CPU and runtime resources. The longer trials measure increasing
CPU work per ID above the throughput peak:

| Runtime | At recommended count | At nine workers | Throughput loss |
|---|---|---|---:|
| 3.13t | 5.654 M IDs/s; 1,168 CPU ns/ID | 4.771 M IDs/s; 1,730 CPU ns/ID | 15.6% |
| 3.14t | 6.079 M IDs/s; 934 CPU ns/ID | 4.080 M IDs/s; 2,073 CPU ns/ID | 32.9% |

Nine workers use more aggregate CPU while producing fewer IDs. These measurements
do not isolate the contribution of runtime synchronization, cache traffic, or
scheduling across the machine's different core types. They do establish that
`CPU count - 1` is slower than the recommended counts for this workload.

## API and validation

`Generator` has no lock. `ThreadSafeGenerator` acquires one lock and directly calls
the common generation body. The clock callable is replaceable, and assigning
`resolution` updates its cached divisor. Bit packing preserves the configured
identifier layout.

Both classes improve across all four direct single-thread profiles and all five
builds. In the millisecond profile, paired median time reductions are 19.9–22.9%
for `Generator` and 18.3–24.9% for `ThreadSafeGenerator`, relative to the baseline
commit recorded in the full report.

The suite passes 41 tests on each build, for 205 executions. The optimized
implementation produces zero duplicates across 188 million checked IDs in 220
correctness trials, with strictly increasing values within each worker. Ruff
0.16.9 and mypy 2.3.1 pass for the changed package code, new tests, and benchmark
scripts. Independent reviews found no actionable code or measurement issue.
