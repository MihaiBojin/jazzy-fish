# Thread-safe factory implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development to implement and review these tasks. Track execution in the plan's workspace.

**Goal:** Publish an opt-in application-thread factory and a portable performance comparison in PR #99.

**Architecture:** The existing generation body serves unlocked callers and locked state groups. A factory assigns application threads to persistent groups through thread-local bound methods. The benchmark reuses the existing process-isolated harness.

**Tech Stack:** Python standard library, unittest, Ruff, mypy, GitHub CLI.

**Spec:** `docs/superpowers/specs/2026-09-28-threadsafe-factory.md`

## Global constraints

- Python 3.12 and newer; no new runtime dependencies.
- Application-owned threads; the SDK creates no worker threads.
- Six groups by default, with caller-owned machine IDs and unchanged bit widths.
- Preserve current main's clock rounding, machine order, validation, and sleeping waits.
- Preserve `Generator` and `ThreadSafeGenerator` hot paths.
- Update PR #99 without merging it into main.

## Task 1: SDK factory

Files: `python/src/jazzy_fish/generator.py`,
`python/tests/test_threaded_generator.py`.

Interface: `Generator.threadsafe(epoch, resolution, machine_ids, machine_id_bits,
sequence_bits, *, threads=6) -> Generator`.

- [x] Write a failing test using
  `Generator.threadsafe(0, Resolution.SECOND, list(range(6)), 3, 20)` and an
  injected constant clock. Synchronize six application callers with a barrier;
  assert all six machine IDs occur and every ID is unique.
- [x] Add tests for custom counts, insufficient distinct IDs, invalid counts,
  callers above the group count, thread replacement, capacity methods, and
  clock/resolution reassignment. Worker futures must propagate exceptions.
- [x] Run `PYTHONPATH=python/src python3.14 -m unittest discover -s python/tests -p test_threaded_generator.py` and confirm failure for the missing factory.
- [x] Implement the factory and an internal `Generator` subclass. Partition
  IDs with `machine_ids[index::threads]`. Each group owns a
  `ThreadSafeGenerator`; cache its bound method in `threading.local`. Protect
  initial assignment with a lock and cycle through groups. Keep generation
  outside the assignment lock. Cache lookup must not catch exceptions from
  executing the generation method.
- [x] Propagate stopped-generation clock and resolution updates to group state.
  Retain one machine/sequence layout for capacity calculations.
- [x] Run the focused tests on standard and free-threaded Python, then obtain
  an independent review of the ownership and uniqueness guarantees.

## Task 2: Portable comparison and publication

Files: `benchmarks/run.py`, `benchmarks/pr99/benchmark.py`,
`python/tests/test_benchmark_cli.py`, `python/README.md`, `benchmarks/README.md`.

Interface: `python3.14 benchmarks/run.py --sweep --python /path/to/python
--baseline REVISION_OR_FILE --output NEW_DIRECTORY`.

- [x] Add a CLI integration test that runs from another directory and preserves
  existing output; confirm failure before implementing the runner.
- [x] Generate runtime-specific jobs, immutable snapshots, raw records, and
  Markdown/JSON reports; avoid hardcoded interpreter paths and CPU counts.
- [x] Add the SDK factory as a measured ownership mode. Use the requested caller
  count as the group count, and warm each caller's thread-local binding before
  timing. Snapshot support must omit this mode for baselines without the factory.
- [x] Verify metadata on platforms without load averages and generation beyond
  sixteen machine IDs. Run CLI tests on all five installed Python builds.
- [x] Document `Generator(...)` and `Generator.threadsafe(..., threads=6)` with
  executable examples and the machine-ID allocation requirement.
- [x] Run the full test suite on five builds. Run the portable comparison against
  current main, including every caller count from one through nine.
- [x] Run Ruff, mypy, report integrity checks, and an independent final review.
- [x] Commit the session changes, push to `fix/generator-always-lock`, rewrite
  PR #99's title/body around the final API, and check CI at the pushed commit.
