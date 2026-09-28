"""Validate and regenerate the recorded SDK comparison and longer trials."""

import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run as runner


def main() -> None:
    config = json.loads((HERE / "config.json").read_text())
    for name, source in config["sources"].items():
        snapshot = HERE / "snapshots" / f"{name}.py.txt"
        if hashlib.sha256(snapshot.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"Snapshot hash mismatch: {name}")
    runner.write_report(HERE, config)
    report = HERE / "README.md"
    text = report.read_text().replace("results.jsonl", "results.jsonl.gz")
    text = text.replace(
        "# Generator benchmark on this machine\n",
        "# Generator benchmark on this machine\n\nRecorded on an Apple M1 Max against main at `4763e1a`. See [provenance](provenance.json), [longer trials](confirmation.md), and [worker recommendations](recommendation.md).\n",
    )
    report.write_text(text)
    confirmation = json.loads((HERE / "confirmation-config.json").read_text())
    path = HERE / "confirmation-results.jsonl"
    contents = (
        path.read_text()
        if path.exists()
        else gzip.decompress(path.with_suffix(".jsonl.gz").read_bytes()).decode()
    )
    rows = [json.loads(line) for line in contents.splitlines()]
    if len(rows) != len(confirmation["jobs"]):
        raise ValueError("Incomplete confirmation results")
    for index, row in enumerate(rows):
        if row["job_index"] != index or any(
            row[key] != value for key, value in confirmation["jobs"][index].items()
        ):
            raise ValueError(f"Confirmation job mismatch: {index}")
        if row["source_sha256"] != config["sources"]["current"]["sha256"]:
            raise ValueError(f"Confirmation source mismatch: {index}")
        if row["runtime"]["gil_enabled"]:
            raise ValueError(f"GIL enabled during confirmation: {index}")
    summary = runner.bench.summarize_rows(rows)
    (HERE / "confirmation-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    lines = [
        "# Longer SDK worker-count trials",
        "",
        "Apple M1 Max, 10 cores. Each case has five fresh-process samples of five million IDs. These trials measure the current snapshot from the SDK matrix. GIL-disabled builds only; generation excludes encoding and application I/O.",
        "",
        "| Python | Ownership | Workers | Median million IDs/s | Sample range |",
        "|---|---|---:|---:|---:|",
    ]
    for row in sorted(summary, key=lambda r: (r["label"], r["variant"], r["threads"])):
        lines.append(
            f"| {row['label']} | {runner.OWNERSHIP[row['variant']]} | {row['threads']} | {row['million_ids_per_second']:.3f} | {1000 / row['max_ns']:.3f}–{1000 / row['min_ns']:.3f} |"
        )
    lines += [
        "",
        "## Highest observed medians",
        "",
        "| Python | Ownership | Workers | Million IDs/s | Six workers relative to peak |",
        "|---|---|---:|---:|---:|",
    ]
    for label in confirmation["interpreters"]:
        for variant in ("factory", "private"):
            cases = [
                r for r in summary if r["label"] == label and r["variant"] == variant
            ]
            peak = max(
                cases, key=lambda r: (r["million_ids_per_second"], -r["threads"])
            )
            six = next(r for r in cases if r["threads"] == 6)
            lines.append(
                f"| {label} | {runner.OWNERSHIP[variant]} | {peak['threads']} | {peak['million_ids_per_second']:.3f} | {100 * six['million_ids_per_second'] / peak['million_ids_per_second']:.1f}% |"
            )
    lines += [
        "",
        "The table selects the highest measured median. Overlapping sample ranges do not establish a statistically distinct optimum. Six remains the SDK default; run the portable sweep on the deployment machine to choose its count.",
        "",
        "The factory locks each persistent group and dispatches through thread-local storage. Private mode gives each caller its own unlocked generator and disjoint machine ID. This measures the cost of sharing the public factory as well as the best throughput available with application-managed ownership.",
        "",
        "Recreate these longer trials using the interpreter and snapshot paths in confirmation-config.json, adjusted for the local checkout:",
        "",
        "```sh",
        "python3.14 benchmarks/pr99/benchmark.py run benchmarks/sdk/confirmation-config.json --output /tmp/sdk-confirmation.jsonl",
        "```",
        "",
        "Regenerate the archived reports and verify every recorded job and source hash:",
        "",
        "```sh",
        "python3.14 benchmarks/sdk/report_sdk.py",
        "```",
        "",
        "For a new machine, use benchmarks/run.py with --sweep and the installed --python executables. Increase --calls to 5000000 for longer samples. The original runtime paths, hashes, and test results are recorded in provenance.json and tests.json.",
    ]
    (HERE / "confirmation.md").write_text("\n".join(lines) + "\n")
    print(
        f"Validated {len(config['jobs'])} matrix trials and {len(rows)} confirmation trials"
    )


if __name__ == "__main__":
    main()
