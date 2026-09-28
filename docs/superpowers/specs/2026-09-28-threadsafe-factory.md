# Application-owned generator threads

`Generator(...)` provides unlocked generation for one caller. The new factory
`Generator.threadsafe(epoch, resolution, machine_ids, machine_id_bits,
sequence_bits, *, threads=6)` returns a generator that application-owned threads
can share. It creates no worker threads.

The factory partitions the caller's distinct machine IDs into `threads` groups.
Every group has an independent `ThreadSafeGenerator`. Each calling thread caches
a bound `next_id` method in thread-local storage. An assignment lock selects a
group once per calling thread. Assignment cycles through the groups; callers
above the configured count safely share group locks. Group state persists when
application threads finish, so replacement threads cannot reset an ID sequence.

`threads` must be a positive integer. The allocation must contain at least that
many distinct machine IDs. Existing bit-width validation applies. The factory
preserves the caller's epoch, resolution, machine IDs, and bit widths. It never
allocates machine IDs outside the caller's domain or silently widens the ID layout.
The default is six groups; `threads=1` may return the existing locked class.

The return value supports `next_id`, `max_id_at`, and `exhausts_at`, and is a
`Generator`. Clock and resolution assignment propagates to every group while
generation is stopped. Machine IDs and bit widths are configured at construction.
No global ordering across groups is promised. Exceptions from a clock propagate
to callers. The existing `ThreadSafeGenerator` keeps its single-lock behavior and
has no deprecation warning.

The portable benchmark runs installed Python executables, preserves source
snapshots, checks correctness separately from timing, and records the GIL state.
It compares the public factory against a shared locked generator and private
unlocked generators. Default caller counts are one and six; `--sweep` tests one
through available CPUs minus one. Reports identify the tested optimum and sample
spread without asserting a universal fastest count.

The implementation targets Python 3.12 and newer and adds no runtime dependencies.
PR #99 is updated in place, preserving its commit history and current main's
rounding, machine-order, epoch-validation, and sleeping-wait behavior.
