# Generator benchmark on this machine

Recorded on an Apple M1 Max against main at `4763e1a`. See [provenance](provenance.json), [longer trials](confirmation.md), and [worker recommendations](recommendation.md).

Baseline and Current identify the source snapshots recorded in config.json. Current is the checkout at the start of this run. Comparisons use the same settings and fresh processes, shuffled within each repetition.

| Python | Platform | Available CPUs | GIL enabled | Threads tested |
|---|---|---:|---|---|
| 3.12.14-gil | macOS-26.6.2-arm64-arm-64bit | 10 | True | 1, 2, 3, 4, 5, 6, 7, 8, 9 |
| 3.13.15-gil | macOS-26.6.2-arm64-arm-64bit-Mach-O | 10 | True | 1, 2, 3, 4, 5, 6, 7, 8, 9 |
| 3.14.7-gil | macOS-26.6.2-arm64-arm-64bit-Mach-O | 10 | True | 1, 2, 3, 4, 5, 6, 7, 8, 9 |
| 3.13.15-free | macOS-26.6.2-arm64-arm-64bit-Mach-O | 10 | False | 1, 2, 3, 4, 5, 6, 7, 8, 9 |
| 3.14.7-free | macOS-26.6.2-arm64-arm-64bit-Mach-O | 10 | False | 1, 2, 3, 4, 5, 6, 7, 8, 9 |

## Direct single-thread calls

Times are median ns/ID with the observed minimum–maximum sample range. These are sample ranges, not confidence intervals. Lower time is better.

| Python | Source | Profile | Class | Median ns/ID | Range |
|---|---|---|---|---:|---:|
| 3.12.14-gil | Baseline | four_machines | ThreadSafeGenerator | 712.8 | 707.0–763.1 |
| 3.12.14-gil | Current | four_machines | ThreadSafeGenerator | 597.6 | 586.9–614.3 |
| 3.12.14-gil | Baseline | four_machines | Generator | 570.0 | 560.2–602.4 |
| 3.12.14-gil | Current | four_machines | Generator | 475.2 | 461.8–486.8 |
| 3.12.14-gil | Baseline | millisecond | ThreadSafeGenerator | 709.3 | 685.6–714.5 |
| 3.12.14-gil | Current | millisecond | ThreadSafeGenerator | 574.2 | 557.3–595.1 |
| 3.12.14-gil | Baseline | millisecond | Generator | 563.6 | 530.9–578.8 |
| 3.12.14-gil | Current | millisecond | Generator | 443.0 | 433.9–453.2 |
| 3.12.14-gil | Baseline | minute | ThreadSafeGenerator | 674.1 | 667.8–702.6 |
| 3.12.14-gil | Current | minute | ThreadSafeGenerator | 556.7 | 542.6–577.2 |
| 3.12.14-gil | Baseline | minute | Generator | 525.8 | 520.1–551.2 |
| 3.12.14-gil | Current | minute | Generator | 425.9 | 424.6–441.1 |
| 3.12.14-gil | Baseline | second | ThreadSafeGenerator | 670.1 | 663.2–717.8 |
| 3.12.14-gil | Current | second | ThreadSafeGenerator | 552.4 | 551.6–554.7 |
| 3.12.14-gil | Baseline | second | Generator | 524.1 | 516.6–554.3 |
| 3.12.14-gil | Current | second | Generator | 436.2 | 421.7–438.8 |
| 3.13.15-free | Baseline | four_machines | ThreadSafeGenerator | 955.2 | 941.1–967.8 |
| 3.13.15-free | Current | four_machines | ThreadSafeGenerator | 734.0 | 706.9–749.8 |
| 3.13.15-free | Baseline | four_machines | Generator | 750.8 | 746.1–789.5 |
| 3.13.15-free | Current | four_machines | Generator | 592.7 | 589.0–619.9 |
| 3.13.15-free | Baseline | millisecond | ThreadSafeGenerator | 919.2 | 899.7–933.2 |
| 3.13.15-free | Current | millisecond | ThreadSafeGenerator | 679.1 | 676.4–707.0 |
| 3.13.15-free | Baseline | millisecond | Generator | 712.7 | 710.2–765.0 |
| 3.13.15-free | Current | millisecond | Generator | 574.9 | 558.1–583.5 |
| 3.13.15-free | Baseline | minute | ThreadSafeGenerator | 932.7 | 899.0–941.6 |
| 3.13.15-free | Current | minute | ThreadSafeGenerator | 705.8 | 679.3–716.0 |
| 3.13.15-free | Baseline | minute | Generator | 739.9 | 713.8–751.5 |
| 3.13.15-free | Current | minute | Generator | 564.0 | 562.0–590.3 |
| 3.13.15-free | Baseline | second | ThreadSafeGenerator | 911.0 | 899.4–1010.7 |
| 3.13.15-free | Current | second | ThreadSafeGenerator | 683.7 | 682.8–705.7 |
| 3.13.15-free | Baseline | second | Generator | 717.4 | 713.6–749.8 |
| 3.13.15-free | Current | second | Generator | 562.1 | 560.0–564.8 |
| 3.13.15-gil | Baseline | four_machines | ThreadSafeGenerator | 695.1 | 679.7–726.5 |
| 3.13.15-gil | Current | four_machines | ThreadSafeGenerator | 571.8 | 567.9–598.5 |
| 3.13.15-gil | Baseline | four_machines | Generator | 580.1 | 555.4–1951.5 |
| 3.13.15-gil | Current | four_machines | Generator | 465.8 | 461.4–470.4 |
| 3.13.15-gil | Baseline | millisecond | ThreadSafeGenerator | 649.3 | 641.1–676.3 |
| 3.13.15-gil | Current | millisecond | ThreadSafeGenerator | 532.3 | 530.9–559.1 |
| 3.13.15-gil | Baseline | millisecond | Generator | 520.2 | 517.6–547.3 |
| 3.13.15-gil | Current | millisecond | Generator | 437.0 | 421.8–457.6 |
| 3.13.15-gil | Baseline | minute | ThreadSafeGenerator | 652.8 | 642.5–671.8 |
| 3.13.15-gil | Current | minute | ThreadSafeGenerator | 549.9 | 533.5–565.1 |
| 3.13.15-gil | Baseline | minute | Generator | 522.7 | 519.5–548.4 |
| 3.13.15-gil | Current | minute | Generator | 421.8 | 420.1–439.4 |
| 3.13.15-gil | Baseline | second | ThreadSafeGenerator | 647.0 | 642.8–677.3 |
| 3.13.15-gil | Current | second | ThreadSafeGenerator | 533.5 | 528.6–535.3 |
| 3.13.15-gil | Baseline | second | Generator | 525.4 | 520.3–538.8 |
| 3.13.15-gil | Current | second | Generator | 443.9 | 421.3–447.5 |
| 3.14.7-free | Baseline | four_machines | ThreadSafeGenerator | 631.4 | 626.1–675.3 |
| 3.14.7-free | Current | four_machines | ThreadSafeGenerator | 499.3 | 497.4–535.3 |
| 3.14.7-free | Baseline | four_machines | Generator | 518.5 | 514.2–535.4 |
| 3.14.7-free | Current | four_machines | Generator | 411.8 | 410.8–425.9 |
| 3.14.7-free | Baseline | millisecond | ThreadSafeGenerator | 611.7 | 587.8–634.4 |
| 3.14.7-free | Current | millisecond | ThreadSafeGenerator | 478.8 | 458.9–489.2 |
| 3.14.7-free | Baseline | millisecond | Generator | 479.0 | 474.1–499.6 |
| 3.14.7-free | Current | millisecond | Generator | 385.8 | 368.8–388.6 |
| 3.14.7-free | Baseline | minute | ThreadSafeGenerator | 598.4 | 591.7–619.8 |
| 3.14.7-free | Current | minute | ThreadSafeGenerator | 461.1 | 460.2–484.0 |
| 3.14.7-free | Baseline | minute | Generator | 495.1 | 476.7–498.4 |
| 3.14.7-free | Current | minute | Generator | 373.4 | 371.5–388.9 |
| 3.14.7-free | Baseline | second | ThreadSafeGenerator | 608.3 | 591.3–622.6 |
| 3.14.7-free | Current | second | ThreadSafeGenerator | 473.4 | 461.6–485.0 |
| 3.14.7-free | Baseline | second | Generator | 494.3 | 473.1–506.6 |
| 3.14.7-free | Current | second | Generator | 385.4 | 371.3–389.1 |
| 3.14.7-gil | Baseline | four_machines | ThreadSafeGenerator | 594.0 | 591.8–622.2 |
| 3.14.7-gil | Current | four_machines | ThreadSafeGenerator | 469.3 | 468.1–486.9 |
| 3.14.7-gil | Baseline | four_machines | Generator | 492.8 | 491.3–518.1 |
| 3.14.7-gil | Current | four_machines | Generator | 389.4 | 388.8–408.1 |
| 3.14.7-gil | Baseline | millisecond | ThreadSafeGenerator | 568.1 | 548.5–580.4 |
| 3.14.7-gil | Current | millisecond | ThreadSafeGenerator | 431.1 | 426.6–443.2 |
| 3.14.7-gil | Baseline | millisecond | Generator | 454.0 | 447.3–473.7 |
| 3.14.7-gil | Current | millisecond | Generator | 351.5 | 348.2–368.6 |
| 3.14.7-gil | Baseline | minute | ThreadSafeGenerator | 572.5 | 554.4–578.3 |
| 3.14.7-gil | Current | minute | ThreadSafeGenerator | 428.4 | 426.5–451.4 |
| 3.14.7-gil | Baseline | minute | Generator | 458.7 | 449.7–485.5 |
| 3.14.7-gil | Current | minute | Generator | 348.7 | 347.0–363.9 |
| 3.14.7-gil | Baseline | second | ThreadSafeGenerator | 553.1 | 549.1–603.0 |
| 3.14.7-gil | Current | second | ThreadSafeGenerator | 434.0 | 428.0–449.7 |
| 3.14.7-gil | Baseline | second | Generator | 458.5 | 451.2–473.3 |
| 3.14.7-gil | Current | second | Generator | 351.2 | 345.9–362.7 |

## Threaded throughput

Values are aggregate million IDs/second. Shared uses one ThreadSafeGenerator; private uses one unlocked Generator per caller with disjoint machine IDs. The factory uses Generator.threadsafe with one group per caller when the snapshot supports it. Higher throughput is better.

| Python | Source | Ownership | Workers | Million IDs/s | Range |
|---|---|---|---:|---:|---:|
| 3.12.14-gil | Current | Generator.threadsafe factory | 1 | 1.609 | 1.555–1.663 |
| 3.12.14-gil | Current | Generator.threadsafe factory | 2 | 1.460 | 1.431–1.565 |
| 3.12.14-gil | Current | Generator.threadsafe factory | 3 | 1.504 | 1.490–1.555 |
| 3.12.14-gil | Current | Generator.threadsafe factory | 4 | 1.525 | 1.477–1.545 |
| 3.12.14-gil | Current | Generator.threadsafe factory | 5 | 1.488 | 1.454–1.515 |
| 3.12.14-gil | Current | Generator.threadsafe factory | 6 | 1.521 | 1.470–1.557 |
| 3.12.14-gil | Current | Generator.threadsafe factory | 7 | 1.506 | 1.476–1.535 |
| 3.12.14-gil | Current | Generator.threadsafe factory | 8 | 1.508 | 1.462–1.548 |
| 3.12.14-gil | Current | Generator.threadsafe factory | 9 | 1.506 | 1.436–1.539 |
| 3.12.14-gil | Baseline | shared ThreadSafeGenerator | 1 | 1.431 | 1.373–1.445 |
| 3.12.14-gil | Current | shared ThreadSafeGenerator | 1 | 1.717 | 1.634–1.734 |
| 3.12.14-gil | Baseline | shared ThreadSafeGenerator | 2 | 1.432 | 1.325–1.444 |
| 3.12.14-gil | Current | shared ThreadSafeGenerator | 2 | 1.704 | 1.631–1.723 |
| 3.12.14-gil | Baseline | shared ThreadSafeGenerator | 3 | 1.400 | 1.352–1.440 |
| 3.12.14-gil | Current | shared ThreadSafeGenerator | 3 | 1.704 | 1.646–1.716 |
| 3.12.14-gil | Baseline | shared ThreadSafeGenerator | 4 | 1.411 | 1.297–1.433 |
| 3.12.14-gil | Current | shared ThreadSafeGenerator | 4 | 1.713 | 1.635–1.724 |
| 3.12.14-gil | Baseline | shared ThreadSafeGenerator | 5 | 1.399 | 1.367–1.436 |
| 3.12.14-gil | Current | shared ThreadSafeGenerator | 5 | 1.706 | 1.641–1.711 |
| 3.12.14-gil | Baseline | shared ThreadSafeGenerator | 6 | 1.419 | 1.353–1.443 |
| 3.12.14-gil | Current | shared ThreadSafeGenerator | 6 | 1.713 | 1.636–1.731 |
| 3.12.14-gil | Baseline | shared ThreadSafeGenerator | 7 | 1.417 | 1.375–1.424 |
| 3.12.14-gil | Current | shared ThreadSafeGenerator | 7 | 1.659 | 1.638–1.715 |
| 3.12.14-gil | Baseline | shared ThreadSafeGenerator | 8 | 1.370 | 1.360–1.439 |
| 3.12.14-gil | Current | shared ThreadSafeGenerator | 8 | 1.641 | 1.609–1.710 |
| 3.12.14-gil | Baseline | shared ThreadSafeGenerator | 9 | 1.379 | 1.351–1.434 |
| 3.12.14-gil | Current | shared ThreadSafeGenerator | 9 | 1.688 | 1.621–1.706 |
| 3.12.14-gil | Baseline | private Generator per caller | 1 | 1.761 | 1.725–1.817 |
| 3.12.14-gil | Current | private Generator per caller | 1 | 2.123 | 2.018–2.182 |
| 3.12.14-gil | Baseline | private Generator per caller | 2 | 1.771 | 1.702–1.800 |
| 3.12.14-gil | Current | private Generator per caller | 2 | 2.163 | 2.054–2.183 |
| 3.12.14-gil | Baseline | private Generator per caller | 3 | 1.777 | 1.715–1.788 |
| 3.12.14-gil | Current | private Generator per caller | 3 | 2.166 | 2.083–2.192 |
| 3.12.14-gil | Baseline | private Generator per caller | 4 | 1.774 | 1.685–1.791 |
| 3.12.14-gil | Current | private Generator per caller | 4 | 2.086 | 2.046–2.175 |
| 3.12.14-gil | Baseline | private Generator per caller | 5 | 1.751 | 1.704–1.770 |
| 3.12.14-gil | Current | private Generator per caller | 5 | 2.116 | 2.043–2.121 |
| 3.12.14-gil | Baseline | private Generator per caller | 6 | 1.745 | 1.685–1.770 |
| 3.12.14-gil | Current | private Generator per caller | 6 | 2.063 | 0.549–2.155 |
| 3.12.14-gil | Baseline | private Generator per caller | 7 | 1.747 | 1.693–1.774 |
| 3.12.14-gil | Current | private Generator per caller | 7 | 2.076 | 2.055–2.160 |
| 3.12.14-gil | Baseline | private Generator per caller | 8 | 1.699 | 1.669–1.767 |
| 3.12.14-gil | Current | private Generator per caller | 8 | 2.143 | 2.033–2.172 |
| 3.12.14-gil | Baseline | private Generator per caller | 9 | 1.735 | 1.691–1.775 |
| 3.12.14-gil | Current | private Generator per caller | 9 | 2.131 | 0.517–2.147 |
| 3.13.15-free | Current | Generator.threadsafe factory | 1 | 1.329 | 1.275–1.337 |
| 3.13.15-free | Current | Generator.threadsafe factory | 2 | 1.803 | 1.759–2.141 |
| 3.13.15-free | Current | Generator.threadsafe factory | 3 | 2.462 | 1.851–2.952 |
| 3.13.15-free | Current | Generator.threadsafe factory | 4 | 3.000 | 2.025–3.640 |
| 3.13.15-free | Current | Generator.threadsafe factory | 5 | 2.413 | 2.315–2.578 |
| 3.13.15-free | Current | Generator.threadsafe factory | 6 | 2.451 | 2.428–2.659 |
| 3.13.15-free | Current | Generator.threadsafe factory | 7 | 2.411 | 2.364–2.441 |
| 3.13.15-free | Current | Generator.threadsafe factory | 8 | 2.213 | 2.123–2.351 |
| 3.13.15-free | Current | Generator.threadsafe factory | 9 | 2.051 | 2.039–2.177 |
| 3.13.15-free | Baseline | shared ThreadSafeGenerator | 1 | 0.974 | 0.949–1.005 |
| 3.13.15-free | Current | shared ThreadSafeGenerator | 1 | 1.334 | 1.269–1.342 |
| 3.13.15-free | Baseline | shared ThreadSafeGenerator | 2 | 0.672 | 0.642–0.703 |
| 3.13.15-free | Current | shared ThreadSafeGenerator | 2 | 0.894 | 0.874–0.915 |
| 3.13.15-free | Baseline | shared ThreadSafeGenerator | 3 | 0.667 | 0.555–0.692 |
| 3.13.15-free | Current | shared ThreadSafeGenerator | 3 | 0.847 | 0.761–0.888 |
| 3.13.15-free | Baseline | shared ThreadSafeGenerator | 4 | 0.614 | 0.502–0.627 |
| 3.13.15-free | Current | shared ThreadSafeGenerator | 4 | 0.805 | 0.637–0.807 |
| 3.13.15-free | Baseline | shared ThreadSafeGenerator | 5 | 0.422 | 0.282–0.485 |
| 3.13.15-free | Current | shared ThreadSafeGenerator | 5 | 0.610 | 0.527–0.619 |
| 3.13.15-free | Baseline | shared ThreadSafeGenerator | 6 | 0.443 | 0.379–0.447 |
| 3.13.15-free | Current | shared ThreadSafeGenerator | 6 | 0.570 | 0.454–0.576 |
| 3.13.15-free | Baseline | shared ThreadSafeGenerator | 7 | 0.409 | 0.368–0.413 |
| 3.13.15-free | Current | shared ThreadSafeGenerator | 7 | 0.494 | 0.453–0.503 |
| 3.13.15-free | Baseline | shared ThreadSafeGenerator | 8 | 0.375 | 0.356–0.390 |
| 3.13.15-free | Current | shared ThreadSafeGenerator | 8 | 0.439 | 0.429–0.474 |
| 3.13.15-free | Baseline | shared ThreadSafeGenerator | 9 | 0.349 | 0.240–0.359 |
| 3.13.15-free | Current | shared ThreadSafeGenerator | 9 | 0.448 | 0.407–0.452 |
| 3.13.15-free | Baseline | private Generator per caller | 1 | 1.270 | 1.252–1.310 |
| 3.13.15-free | Current | private Generator per caller | 1 | 1.670 | 1.611–1.698 |
| 3.13.15-free | Baseline | private Generator per caller | 2 | 1.738 | 1.539–1.944 |
| 3.13.15-free | Current | private Generator per caller | 2 | 2.974 | 2.749–3.171 |
| 3.13.15-free | Baseline | private Generator per caller | 3 | 2.134 | 1.468–2.855 |
| 3.13.15-free | Current | private Generator per caller | 3 | 4.382 | 3.586–4.567 |
| 3.13.15-free | Baseline | private Generator per caller | 4 | 2.097 | 1.438–2.291 |
| 3.13.15-free | Current | private Generator per caller | 4 | 4.952 | 3.816–5.620 |
| 3.13.15-free | Baseline | private Generator per caller | 5 | 1.182 | 1.119–1.429 |
| 3.13.15-free | Current | private Generator per caller | 5 | 5.144 | 4.642–5.853 |
| 3.13.15-free | Baseline | private Generator per caller | 6 | 1.005 | 0.945–1.045 |
| 3.13.15-free | Current | private Generator per caller | 6 | 5.666 | 5.464–6.251 |
| 3.13.15-free | Baseline | private Generator per caller | 7 | 0.828 | 0.802–0.979 |
| 3.13.15-free | Current | private Generator per caller | 7 | 5.918 | 5.046–8.068 |
| 3.13.15-free | Baseline | private Generator per caller | 8 | 0.679 | 0.658–0.702 |
| 3.13.15-free | Current | private Generator per caller | 8 | 5.676 | 5.225–7.072 |
| 3.13.15-free | Baseline | private Generator per caller | 9 | 0.617 | 0.606–0.736 |
| 3.13.15-free | Current | private Generator per caller | 9 | 4.970 | 4.840–5.410 |
| 3.13.15-gil | Current | Generator.threadsafe factory | 1 | 1.707 | 1.666–1.749 |
| 3.13.15-gil | Current | Generator.threadsafe factory | 2 | 1.510 | 1.481–1.573 |
| 3.13.15-gil | Current | Generator.threadsafe factory | 3 | 1.550 | 1.507–1.570 |
| 3.13.15-gil | Current | Generator.threadsafe factory | 4 | 1.558 | 1.492–1.569 |
| 3.13.15-gil | Current | Generator.threadsafe factory | 5 | 1.562 | 1.468–1.564 |
| 3.13.15-gil | Current | Generator.threadsafe factory | 6 | 1.555 | 1.503–1.566 |
| 3.13.15-gil | Current | Generator.threadsafe factory | 7 | 1.552 | 1.499–1.560 |
| 3.13.15-gil | Current | Generator.threadsafe factory | 8 | 1.526 | 1.497–1.558 |
| 3.13.15-gil | Current | Generator.threadsafe factory | 9 | 1.536 | 1.456–1.541 |
| 3.13.15-gil | Baseline | shared ThreadSafeGenerator | 1 | 1.473 | 1.405–1.478 |
| 3.13.15-gil | Current | shared ThreadSafeGenerator | 1 | 1.721 | 1.675–1.770 |
| 3.13.15-gil | Baseline | shared ThreadSafeGenerator | 2 | 1.432 | 1.393–1.467 |
| 3.13.15-gil | Current | shared ThreadSafeGenerator | 2 | 1.722 | 1.684–1.771 |
| 3.13.15-gil | Baseline | shared ThreadSafeGenerator | 3 | 1.406 | 1.383–1.464 |
| 3.13.15-gil | Current | shared ThreadSafeGenerator | 3 | 1.749 | 1.696–1.777 |
| 3.13.15-gil | Baseline | shared ThreadSafeGenerator | 4 | 1.405 | 1.394–1.466 |
| 3.13.15-gil | Current | shared ThreadSafeGenerator | 4 | 1.746 | 1.663–1.760 |
| 3.13.15-gil | Baseline | shared ThreadSafeGenerator | 5 | 1.454 | 1.395–1.466 |
| 3.13.15-gil | Current | shared ThreadSafeGenerator | 5 | 1.765 | 1.685–1.776 |
| 3.13.15-gil | Baseline | shared ThreadSafeGenerator | 6 | 1.451 | 1.417–1.467 |
| 3.13.15-gil | Current | shared ThreadSafeGenerator | 6 | 1.705 | 1.694–1.748 |
| 3.13.15-gil | Baseline | shared ThreadSafeGenerator | 7 | 1.448 | 1.398–1.463 |
| 3.13.15-gil | Current | shared ThreadSafeGenerator | 7 | 1.705 | 1.677–1.762 |
| 3.13.15-gil | Baseline | shared ThreadSafeGenerator | 8 | 1.433 | 1.402–1.464 |
| 3.13.15-gil | Current | shared ThreadSafeGenerator | 8 | 1.739 | 1.677–1.759 |
| 3.13.15-gil | Baseline | shared ThreadSafeGenerator | 9 | 1.406 | 1.374–1.460 |
| 3.13.15-gil | Current | shared ThreadSafeGenerator | 9 | 1.759 | 1.696–1.769 |
| 3.13.15-gil | Baseline | private Generator per caller | 1 | 1.813 | 1.737–1.817 |
| 3.13.15-gil | Current | private Generator per caller | 1 | 2.199 | 2.115–2.201 |
| 3.13.15-gil | Baseline | private Generator per caller | 2 | 1.785 | 1.713–1.805 |
| 3.13.15-gil | Current | private Generator per caller | 2 | 2.149 | 2.081–2.181 |
| 3.13.15-gil | Baseline | private Generator per caller | 3 | 1.763 | 1.721–1.793 |
| 3.13.15-gil | Current | private Generator per caller | 3 | 2.104 | 2.046–2.178 |
| 3.13.15-gil | Baseline | private Generator per caller | 4 | 1.775 | 1.714–1.796 |
| 3.13.15-gil | Current | private Generator per caller | 4 | 2.152 | 2.107–2.183 |
| 3.13.15-gil | Baseline | private Generator per caller | 5 | 1.774 | 1.716–1.789 |
| 3.13.15-gil | Current | private Generator per caller | 5 | 2.155 | 2.077–2.176 |
| 3.13.15-gil | Baseline | private Generator per caller | 6 | 1.760 | 1.698–1.784 |
| 3.13.15-gil | Current | private Generator per caller | 6 | 2.134 | 1.990–2.166 |
| 3.13.15-gil | Baseline | private Generator per caller | 7 | 1.703 | 1.683–1.785 |
| 3.13.15-gil | Current | private Generator per caller | 7 | 2.087 | 1.850–2.166 |
| 3.13.15-gil | Baseline | private Generator per caller | 8 | 1.747 | 1.704–1.763 |
| 3.13.15-gil | Current | private Generator per caller | 8 | 2.106 | 2.065–2.162 |
| 3.13.15-gil | Baseline | private Generator per caller | 9 | 1.747 | 1.687–1.761 |
| 3.13.15-gil | Current | private Generator per caller | 9 | 2.064 | 2.043–2.115 |
| 3.14.7-free | Current | Generator.threadsafe factory | 1 | 1.881 | 1.856–1.940 |
| 3.14.7-free | Current | Generator.threadsafe factory | 2 | 2.930 | 1.733–3.002 |
| 3.14.7-free | Current | Generator.threadsafe factory | 3 | 3.813 | 2.489–4.113 |
| 3.14.7-free | Current | Generator.threadsafe factory | 4 | 3.594 | 3.174–5.057 |
| 3.14.7-free | Current | Generator.threadsafe factory | 5 | 3.801 | 2.968–3.893 |
| 3.14.7-free | Current | Generator.threadsafe factory | 6 | 3.690 | 0.623–3.920 |
| 3.14.7-free | Current | Generator.threadsafe factory | 7 | 3.943 | 3.757–4.057 |
| 3.14.7-free | Current | Generator.threadsafe factory | 8 | 4.017 | 3.987–4.400 |
| 3.14.7-free | Current | Generator.threadsafe factory | 9 | 3.968 | 3.676–4.310 |
| 3.14.7-free | Baseline | shared ThreadSafeGenerator | 1 | 1.464 | 1.417–1.504 |
| 3.14.7-free | Current | shared ThreadSafeGenerator | 1 | 1.927 | 1.857–1.934 |
| 3.14.7-free | Baseline | shared ThreadSafeGenerator | 2 | 1.016 | 0.414–1.089 |
| 3.14.7-free | Current | shared ThreadSafeGenerator | 2 | 1.456 | 1.414–1.520 |
| 3.14.7-free | Baseline | shared ThreadSafeGenerator | 3 | 0.962 | 0.884–0.983 |
| 3.14.7-free | Current | shared ThreadSafeGenerator | 3 | 1.187 | 1.031–1.239 |
| 3.14.7-free | Baseline | shared ThreadSafeGenerator | 4 | 0.802 | 0.682–0.870 |
| 3.14.7-free | Current | shared ThreadSafeGenerator | 4 | 0.888 | 0.824–1.149 |
| 3.14.7-free | Baseline | shared ThreadSafeGenerator | 5 | 0.659 | 0.627–0.666 |
| 3.14.7-free | Current | shared ThreadSafeGenerator | 5 | 0.881 | 0.831–0.906 |
| 3.14.7-free | Baseline | shared ThreadSafeGenerator | 6 | 0.604 | 0.496–0.625 |
| 3.14.7-free | Current | shared ThreadSafeGenerator | 6 | 0.814 | 0.793–0.840 |
| 3.14.7-free | Baseline | shared ThreadSafeGenerator | 7 | 0.542 | 0.501–0.582 |
| 3.14.7-free | Current | shared ThreadSafeGenerator | 7 | 0.700 | 0.373–0.720 |
| 3.14.7-free | Baseline | shared ThreadSafeGenerator | 8 | 0.488 | 0.312–0.519 |
| 3.14.7-free | Current | shared ThreadSafeGenerator | 8 | 0.646 | 0.567–0.656 |
| 3.14.7-free | Baseline | shared ThreadSafeGenerator | 9 | 0.485 | 0.448–0.493 |
| 3.14.7-free | Current | shared ThreadSafeGenerator | 9 | 0.617 | 0.611–0.811 |
| 3.14.7-free | Baseline | private Generator per caller | 1 | 1.875 | 1.679–1.897 |
| 3.14.7-free | Current | private Generator per caller | 1 | 2.464 | 2.339–2.477 |
| 3.14.7-free | Baseline | private Generator per caller | 2 | 2.877 | 2.086–2.904 |
| 3.14.7-free | Current | private Generator per caller | 2 | 3.787 | 3.258–4.453 |
| 3.14.7-free | Baseline | private Generator per caller | 3 | 3.149 | 2.073–3.722 |
| 3.14.7-free | Current | private Generator per caller | 3 | 5.954 | 4.900–6.506 |
| 3.14.7-free | Baseline | private Generator per caller | 4 | 3.526 | 1.983–3.831 |
| 3.14.7-free | Current | private Generator per caller | 4 | 7.681 | 5.786–8.617 |
| 3.14.7-free | Baseline | private Generator per caller | 5 | 2.018 | 1.871–2.109 |
| 3.14.7-free | Current | private Generator per caller | 5 | 6.316 | 6.009–6.376 |
| 3.14.7-free | Baseline | private Generator per caller | 6 | 1.858 | 1.737–1.869 |
| 3.14.7-free | Current | private Generator per caller | 6 | 6.301 | 6.013–6.799 |
| 3.14.7-free | Baseline | private Generator per caller | 7 | 1.584 | 1.579–1.609 |
| 3.14.7-free | Current | private Generator per caller | 7 | 5.456 | 5.307–5.523 |
| 3.14.7-free | Baseline | private Generator per caller | 8 | 1.392 | 1.370–1.447 |
| 3.14.7-free | Current | private Generator per caller | 8 | 4.557 | 4.494–4.786 |
| 3.14.7-free | Baseline | private Generator per caller | 9 | 1.281 | 1.255–1.465 |
| 3.14.7-free | Current | private Generator per caller | 9 | 4.199 | 3.775–4.578 |
| 3.14.7-gil | Current | Generator.threadsafe factory | 1 | 2.107 | 2.087–2.172 |
| 3.14.7-gil | Current | Generator.threadsafe factory | 2 | 1.845 | 1.771–1.878 |
| 3.14.7-gil | Current | Generator.threadsafe factory | 3 | 1.791 | 1.724–1.863 |
| 3.14.7-gil | Current | Generator.threadsafe factory | 4 | 1.838 | 1.774–1.865 |
| 3.14.7-gil | Current | Generator.threadsafe factory | 5 | 1.857 | 1.753–1.864 |
| 3.14.7-gil | Current | Generator.threadsafe factory | 6 | 1.843 | 1.788–1.856 |
| 3.14.7-gil | Current | Generator.threadsafe factory | 7 | 1.821 | 1.765–1.839 |
| 3.14.7-gil | Current | Generator.threadsafe factory | 8 | 1.841 | 1.782–1.856 |
| 3.14.7-gil | Current | Generator.threadsafe factory | 9 | 1.826 | 1.783–1.864 |
| 3.14.7-gil | Baseline | shared ThreadSafeGenerator | 1 | 1.700 | 1.648–1.715 |
| 3.14.7-gil | Current | shared ThreadSafeGenerator | 1 | 2.082 | 2.073–2.154 |
| 3.14.7-gil | Baseline | shared ThreadSafeGenerator | 2 | 1.675 | 1.643–1.710 |
| 3.14.7-gil | Current | shared ThreadSafeGenerator | 2 | 2.064 | 2.051–2.176 |
| 3.14.7-gil | Baseline | shared ThreadSafeGenerator | 3 | 1.697 | 1.613–1.710 |
| 3.14.7-gil | Current | shared ThreadSafeGenerator | 3 | 2.160 | 2.067–2.172 |
| 3.14.7-gil | Baseline | shared ThreadSafeGenerator | 4 | 1.695 | 1.632–1.695 |
| 3.14.7-gil | Current | shared ThreadSafeGenerator | 4 | 2.156 | 2.050–2.162 |
| 3.14.7-gil | Baseline | shared ThreadSafeGenerator | 5 | 1.635 | 1.572–1.700 |
| 3.14.7-gil | Current | shared ThreadSafeGenerator | 5 | 2.137 | 2.066–2.156 |
| 3.14.7-gil | Baseline | shared ThreadSafeGenerator | 6 | 1.694 | 1.672–1.703 |
| 3.14.7-gil | Current | shared ThreadSafeGenerator | 6 | 2.147 | 2.068–2.159 |
| 3.14.7-gil | Baseline | shared ThreadSafeGenerator | 7 | 1.692 | 1.620–1.704 |
| 3.14.7-gil | Current | shared ThreadSafeGenerator | 7 | 2.146 | 2.043–2.159 |
| 3.14.7-gil | Baseline | shared ThreadSafeGenerator | 8 | 1.674 | 1.618–1.699 |
| 3.14.7-gil | Current | shared ThreadSafeGenerator | 8 | 2.064 | 1.958–2.147 |
| 3.14.7-gil | Baseline | shared ThreadSafeGenerator | 9 | 1.627 | 1.604–1.697 |
| 3.14.7-gil | Current | shared ThreadSafeGenerator | 9 | 2.081 | 2.050–2.161 |
| 3.14.7-gil | Baseline | private Generator per caller | 1 | 2.012 | 1.971–2.065 |
| 3.14.7-gil | Current | private Generator per caller | 1 | 2.547 | 2.478–2.633 |
| 3.14.7-gil | Baseline | private Generator per caller | 2 | 2.033 | 1.943–2.056 |
| 3.14.7-gil | Current | private Generator per caller | 2 | 2.491 | 2.452–2.602 |
| 3.14.7-gil | Baseline | private Generator per caller | 3 | 2.019 | 1.939–2.040 |
| 3.14.7-gil | Current | private Generator per caller | 3 | 2.560 | 2.445–2.591 |
| 3.14.7-gil | Baseline | private Generator per caller | 4 | 1.958 | 1.945–2.030 |
| 3.14.7-gil | Current | private Generator per caller | 4 | 2.501 | 2.458–2.580 |
| 3.14.7-gil | Baseline | private Generator per caller | 5 | 1.959 | 1.742–2.040 |
| 3.14.7-gil | Current | private Generator per caller | 5 | 2.497 | 2.412–2.570 |
| 3.14.7-gil | Baseline | private Generator per caller | 6 | 2.016 | 1.937–2.023 |
| 3.14.7-gil | Current | private Generator per caller | 6 | 2.505 | 2.482–2.566 |
| 3.14.7-gil | Baseline | private Generator per caller | 7 | 2.022 | 1.939–2.025 |
| 3.14.7-gil | Current | private Generator per caller | 7 | 2.534 | 2.456–2.567 |
| 3.14.7-gil | Baseline | private Generator per caller | 8 | 1.998 | 1.935–2.009 |
| 3.14.7-gil | Current | private Generator per caller | 8 | 2.479 | 2.455–2.567 |
| 3.14.7-gil | Baseline | private Generator per caller | 9 | 2.018 | 1.969–2.032 |
| 3.14.7-gil | Current | private Generator per caller | 9 | 2.557 | 2.455–2.567 |

## Observed worker recommendations

| Python | Ownership | Best tested workers | Million IDs/s |
|---|---|---:|---:|
| 3.12.14-gil | shared ThreadSafeGenerator | 1 | 1.717 |
| 3.12.14-gil | private Generator per caller | 3 | 2.166 |
| 3.12.14-gil | Generator.threadsafe factory | 1 | 1.609 |
| 3.13.15-gil | shared ThreadSafeGenerator | 5 | 1.765 |
| 3.13.15-gil | private Generator per caller | 1 | 2.199 |
| 3.13.15-gil | Generator.threadsafe factory | 1 | 1.707 |
| 3.14.7-gil | shared ThreadSafeGenerator | 3 | 2.160 |
| 3.14.7-gil | private Generator per caller | 3 | 2.560 |
| 3.14.7-gil | Generator.threadsafe factory | 1 | 2.107 |
| 3.13.15-free | shared ThreadSafeGenerator | 1 | 1.334 |
| 3.13.15-free | private Generator per caller | 7 | 5.918 |
| 3.13.15-free | Generator.threadsafe factory | 4 | 3.000 |
| 3.14.7-free | shared ThreadSafeGenerator | 1 | 1.927 |
| 3.14.7-free | private Generator per caller | 4 | 7.681 |
| 3.14.7-free | Generator.threadsafe factory | 8 | 4.017 |

Recommendations select the highest median among tested counts, with fewer workers breaking an exact tie. Close results and overlapping ranges require longer trials. The default compares one and six workers; use --sweep for a machine-wide search. These results measure integer generation, excluding encoding and application work.

## Correctness and method

570 correctness trials checked 57,000,000 IDs with zero duplicates and strictly increasing IDs within each worker. Each source is checked separately; snapshots do not share an ID domain.

Each timing case has 5 fresh-process samples of 500,000 calls. The measured path is warmed with 20,000 calls. Private generators and factory bindings are warmed inside each caller before timing. Threaded calls are divided evenly; a barrier starts the clock and the last caller stops it. Thread creation, imports, and uniqueness checks are outside timing. Cyclic GC is disabled during measurement. Correctness trials retain IDs, run separately, and include extra shared-generator checks with a 1 µs thread-switch interval. Their timings do not contribute to throughput estimates.

The direct profiles use millisecond, second, and minute resolution with one machine, plus a millisecond profile with four machine IDs. The threaded profile uses millisecond resolution and 22 sequence bits. Its machine bit width fits the largest tested count and is identical across sources and ownership modes. Each worker's machine ID is its zero-based index in private mode; shared mode uses machine ID zero. Factory mode supplies IDs zero through callers minus one and sets threads to the caller count. Full configuration and runtime metadata are in results.jsonl.gz.

The CPU count uses process availability when supported, then CPU affinity, then the operating system's logical CPU count. Affinity and frequency are not controlled by this benchmark. Run without competing workloads for less variation. Free-threaded builds are checked after every trial to ensure the GIL remains disabled.

config.json records the exact jobs and source hashes; snapshots/ preserves the measured source. results.jsonl.gz contains every raw trial; summary.json contains per-case medians, ranges, and median absolute deviations. A nonzero exit status indicates an incomplete run or a correctness failure. Timing differences never fail a test.
