#!/usr/bin/env python3
"""Generate the frozen deterministic benchmark dataset."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from pathlib import Path

SEED = 20260820
DESTINATIONS = [
    ("Paris", "Europe"), ("Tokyo", "Asia"), ("Sydney", "Oceania"),
    ("New York", "North America"), ("Cape Town", "Africa"),
    ("Rio de Janeiro", "South America"), ("Dubai", "Middle East"),
    ("Barcelona", "Europe"),
]
FIELDS = ["month", "destination", "region", "bookings", "gross_revenue",
          "refunds", "marketing_spend", "customer_rating", "cancellations",
          "avg_trip_days"]


def generate(output: Path) -> None:
    rng = random.Random(SEED)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for di, (destination, region) in enumerate(DESTINATIONS):
        base = 650 + di * 63
        price = 1080 + di * 92
        for month in range(1, 13):
            seasonal = 1 + 0.23 * math.sin((month - 2 + di % 3) * math.pi / 6)
            bookings = max(100, round(base * seasonal + rng.gauss(0, 32)))
            revenue = round(bookings * (price + rng.gauss(0, 35)), 2)
            cancel_rate = 0.045 + (di % 4) * 0.009 + rng.uniform(-0.006, 0.006)
            cancellations = max(0, round(bookings * cancel_rate))
            refunds = round(revenue * (0.018 + di % 3 * 0.006 + rng.uniform(0, 0.006)), 2)
            marketing = round((135000 + di * 9000) * (0.9 + month / 50) + rng.gauss(0, 4500), 2)
            rating = round(min(5, max(3.3, 4.62 - di * 0.045 + rng.uniform(-0.12, 0.12))), 2)
            trip_days = round(4.4 + di * 0.37 + rng.uniform(-0.35, 0.35), 1)
            rows.append({
                "month": f"2025-{month:02d}", "destination": destination,
                "region": region, "bookings": bookings,
                "gross_revenue": f"{revenue:.2f}", "refunds": f"{refunds:.2f}",
                "marketing_spend": f"{marketing:.2f}",
                "customer_rating": f"{rating:.2f}", "cancellations": cancellations,
                "avg_trip_days": f"{trip_days:.1f}",
            })
    csv_path = output / "destination_performance.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "generator_seed": SEED,
        "rows": len(rows),
        "sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "columns": FIELDS,
    }
    (output.parent / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    generate(Path(__file__).resolve().parent / "input")

