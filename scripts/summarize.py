#!/usr/bin/env python3
from __future__ import annotations

from infra_lib import ROOT, read_run_rows, write_results


def fmt(value):
    return "" if value is None else str(value)


if __name__ == "__main__":
    rows = read_run_rows()
    write_results(rows)
    lines = ["# Experiment summary", "", "Measured results only; missing telemetry is blank, never zero.", "",
             "| Check | Arm | Quality | Time (s) | Main tokens | Vision tokens | Cost (USD) | Status |",
             "|---|---|---:|---:|---:|---:|---:|---|"]
    for row in rows:
        quality = row["judge_score"] if row["judge_score"] is not None else row["deterministic_score"]
        lines.append("| " + " | ".join(fmt(x) for x in (row["check_id"], row["arm"], quality,
                     row["wall_seconds"], row["total_tokens"], row["vision_input_tokens"],
                     row["combined_reported_cost_usd"], row["status"])) + " |")
    (ROOT / "results/summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(ROOT / "results/summary.md")

