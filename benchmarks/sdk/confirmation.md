# Longer SDK worker-count trials

Apple M1 Max, 10 cores. Each case has five fresh-process samples of five million IDs. These trials measure the current snapshot from the SDK matrix. GIL-disabled builds only; generation excludes encoding and application I/O.

| Python | Ownership | Workers | Median million IDs/s | Sample range |
|---|---|---:|---:|---:|
| 3.13.15-free | Generator.threadsafe factory | 1 | 1.332 | 1.106–1.341 |
| 3.13.15-free | Generator.threadsafe factory | 2 | 2.110 | 1.589–2.125 |
| 3.13.15-free | Generator.threadsafe factory | 3 | 2.808 | 1.119–2.918 |
| 3.13.15-free | Generator.threadsafe factory | 4 | 3.284 | 2.982–3.590 |
| 3.13.15-free | Generator.threadsafe factory | 5 | 2.554 | 2.468–2.655 |
| 3.13.15-free | Generator.threadsafe factory | 6 | 2.663 | 2.606–2.768 |
| 3.13.15-free | Generator.threadsafe factory | 7 | 2.469 | 2.426–2.500 |
| 3.13.15-free | Generator.threadsafe factory | 8 | 2.290 | 1.732–2.344 |
| 3.13.15-free | Generator.threadsafe factory | 9 | 2.074 | 2.042–2.093 |
| 3.13.15-free | private Generator per caller | 1 | 1.688 | 1.678–1.692 |
| 3.13.15-free | private Generator per caller | 2 | 3.150 | 1.988–3.162 |
| 3.13.15-free | private Generator per caller | 3 | 4.346 | 4.300–4.508 |
| 3.13.15-free | private Generator per caller | 4 | 5.694 | 5.353–5.933 |
| 3.13.15-free | private Generator per caller | 5 | 5.529 | 5.290–5.856 |
| 3.13.15-free | private Generator per caller | 6 | 6.051 | 5.754–6.307 |
| 3.13.15-free | private Generator per caller | 7 | 6.108 | 3.394–6.454 |
| 3.13.15-free | private Generator per caller | 8 | 5.794 | 5.702–6.308 |
| 3.13.15-free | private Generator per caller | 9 | 4.918 | 4.830–4.961 |
| 3.14.7-free | Generator.threadsafe factory | 1 | 1.931 | 1.927–1.932 |
| 3.14.7-free | Generator.threadsafe factory | 2 | 2.959 | 2.555–3.003 |
| 3.14.7-free | Generator.threadsafe factory | 3 | 4.036 | 3.063–4.231 |
| 3.14.7-free | Generator.threadsafe factory | 4 | 4.873 | 4.290–5.222 |
| 3.14.7-free | Generator.threadsafe factory | 5 | 4.015 | 3.823–4.063 |
| 3.14.7-free | Generator.threadsafe factory | 6 | 4.194 | 4.031–4.423 |
| 3.14.7-free | Generator.threadsafe factory | 7 | 4.210 | 4.077–4.503 |
| 3.14.7-free | Generator.threadsafe factory | 8 | 4.160 | 3.889–4.368 |
| 3.14.7-free | Generator.threadsafe factory | 9 | 4.248 | 4.102–4.407 |
| 3.14.7-free | private Generator per caller | 1 | 2.456 | 2.069–2.475 |
| 3.14.7-free | private Generator per caller | 2 | 4.238 | 3.599–4.409 |
| 3.14.7-free | private Generator per caller | 3 | 6.351 | 6.326–6.413 |
| 3.14.7-free | private Generator per caller | 4 | 7.837 | 6.846–8.093 |
| 3.14.7-free | private Generator per caller | 5 | 7.115 | 6.248–7.155 |
| 3.14.7-free | private Generator per caller | 6 | 6.553 | 3.220–6.654 |
| 3.14.7-free | private Generator per caller | 7 | 5.710 | 5.538–5.791 |
| 3.14.7-free | private Generator per caller | 8 | 4.745 | 4.648–4.995 |
| 3.14.7-free | private Generator per caller | 9 | 3.924 | 3.828–4.083 |

## Highest observed medians

| Python | Ownership | Workers | Million IDs/s | Six workers relative to peak |
|---|---|---:|---:|---:|
| 3.13.15-free | Generator.threadsafe factory | 4 | 3.284 | 81.1% |
| 3.13.15-free | private Generator per caller | 7 | 6.108 | 99.1% |
| 3.14.7-free | Generator.threadsafe factory | 4 | 4.873 | 86.1% |
| 3.14.7-free | private Generator per caller | 4 | 7.837 | 83.6% |

The table selects the highest measured median. Overlapping sample ranges do not establish a statistically distinct optimum. Six remains the SDK default; run the portable sweep on the deployment machine to choose its count.

The factory locks each persistent group and dispatches through thread-local storage. Private mode gives each caller its own unlocked generator and disjoint machine ID. This measures the cost of sharing the public factory as well as the best throughput available with application-managed ownership.

Recreate these longer trials using the interpreter and snapshot paths in confirmation-config.json, adjusted for the local checkout:

```sh
python3.14 benchmarks/pr99/benchmark.py run benchmarks/sdk/confirmation-config.json --output /tmp/sdk-confirmation.jsonl
```

Regenerate the archived reports and verify every recorded job and source hash:

```sh
python3.14 benchmarks/sdk/report_sdk.py
```

For a new machine, use benchmarks/run.py with --sweep and the installed --python executables. Increase --calls to 5000000 for longer samples. The original runtime paths, hashes, and test results are recorded in provenance.json and tests.json.
