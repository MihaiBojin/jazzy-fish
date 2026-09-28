# Longer worker-count confirmation

Each case generates 5,000,000 IDs, divided evenly among workers, in five fresh processes. These trials measure the optimized snapshot with a separate unlocked generator per worker. They run after the full baseline/optimized matrix. All nine worker counts are tested on both free-threaded builds; the GIL remains disabled.

The setup matches the main matrix: 20,000 warmup calls, distinct machine IDs, 4 machine bits, 22 sequence bits, millisecond resolution, and a barrier before timing. Only one process runs at a time; case order is shuffled within each repetition. CPU/wall is process CPU time divided by elapsed wall time. CPU ns/ID measures total process CPU work per ID, including worker teardown and joins.

Recorded from 2026-09-27T23:54:43Z to 2026-09-27T23:56:53Z: 90 trials and 450,000,000 timed calls.

## 3.13t

| Workers | Median M IDs/s | Range M IDs/s | MAD, ns/ID | CPU/wall | CPU ns/ID |
|---:|---:|---:|---:|---:|---:|
| 1 | 1.465 | 1.453–1.468 | 1.56 | 1.00 | 680.4 |
| 2 | 2.283 | 2.232–2.615 | 9.97 | 1.99 | 871.7 |
| 3 | 3.013 | 2.979–3.232 | 3.79 | 2.78 | 915.6 |
| 4 | 3.897 | 3.861–3.976 | 1.99 | 3.92 | 992.0 |
| 5 | 4.641 | 4.489–4.732 | 1.91 | 4.71 | 1011.4 |
| 6 | 5.234 | 5.146–5.375 | 1.37 | 5.52 | 1045.3 |
| 7 | 5.654 | 5.576–5.801 | 2.30 | 6.63 | 1167.5 |
| 8 | 5.306 | 5.250–5.449 | 1.82 | 7.29 | 1358.4 |
| 9 | 4.771 | 4.668–4.875 | 3.84 | 8.22 | 1729.9 |

## 3.14t

| Workers | Median M IDs/s | Range M IDs/s | MAD, ns/ID | CPU/wall | CPU ns/ID |
|---:|---:|---:|---:|---:|---:|
| 1 | 2.097 | 2.074–2.115 | 2.33 | 0.99 | 474.4 |
| 2 | 3.537 | 3.224–3.616 | 3.86 | 1.98 | 557.8 |
| 3 | 4.136 | 4.070–4.192 | 2.90 | 2.78 | 672.8 |
| 4 | 5.344 | 5.122–5.425 | 2.81 | 3.68 | 677.9 |
| 5 | 5.854 | 5.817–6.172 | 1.10 | 4.74 | 803.9 |
| 6 | 6.079 | 5.997–6.249 | 0.11 | 5.67 | 933.7 |
| 7 | 5.468 | 5.296–5.500 | 1.00 | 6.78 | 1235.9 |
| 8 | 4.605 | 4.540–4.645 | 1.88 | 7.59 | 1648.8 |
| 9 | 4.080 | 3.843–4.373 | 5.02 | 8.37 | 2073.3 |

These ranges describe five observed samples, not confidence intervals. [confirmation-results.jsonl.gz](confirmation-results.jsonl.gz) contains the raw measurements; [confirmation-config.json](confirmation-config.json) contains every job and interpreter path. Reproduce from the repository root:

```sh
python3 benchmarks/pr99/benchmark.py run benchmarks/refactor/confirmation-config.json --output /tmp/refactor-confirmation.jsonl
```
