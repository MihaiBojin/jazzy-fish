# Method dispatch experiment

The original opt-in wrapper forwards through `super().next_id()`. PR #99 forwards through `self._next_id_locked()`. This experiment keeps the original opt-in class and lock, assigns the original unlocked method to a class attribute, and calls that attribute through `self`. Library files are unchanged.

Each case has seven shuffled fresh-process trials, 20,000 warmup calls, and 500,000 timed calls. Values below are median ns/ID. These are new trials with a separate measurement loop; compare implementations within this table rather than subtracting these times from the earlier report.

| Python | Original opt-in | Opt-in with direct dispatch | PR | Direct dispatch versus PR |
|---|---:|---:|---:|---:|
| 3.12 | 795.4 | 767.6 | 771.2 | -0.47% |
| 3.13 | 747.1 | 726.6 | 728.0 | -0.19% |
| 3.14 | 655.4 | 630.0 | 628.8 | +0.19% |
| 3.13t | 1057.1 | 972.0 | 974.9 | -0.29% |
| 3.14t | 696.6 | 669.1 | 670.3 | -0.18% |

The direct-dispatch opt-in wrapper matches the PR within 0.5% on every build. This supports method dispatch as the explanation for the measured wrapper speed difference. The generator algorithm and locking contract are identical between the two opt-in variants.

Run `python3 benchmarks/pr99/dispatch.py` to repeat the experiment using the interpreters in `config.json`. Raw trials are in `dispatch-results.json`.
