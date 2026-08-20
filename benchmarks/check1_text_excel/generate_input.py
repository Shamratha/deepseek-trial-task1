#!/usr/bin/env python3
"""Generate the frozen deterministic benchmark dataset."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from pathlib import Path

SEED = 20260731
DESTINATIONS = [
    ("Paris", "Europe"), ("Tokyo", "Asia"), ("Sydney", "Oceania"),
    ("New York", "North America"), ("Cape Town", "Africa"),
    ("Rio de Janeiro", "South America"), ("Dubai", "Middle East"),
    ("Barcelona", "Europe"), ("Singapore", "Asia"), ("Vancouver", "North America"),
    ("Marrakech", "Africa"), ("Queenstown", "Oceania"),
]
FIELDS = ["month", "destination", "region", "bookings", "gross_revenue",
          "refunds", "marketing_spend", "customer_rating", "cancellations",
          "avg_trip_days"]


def generate(output: Path) -> None:
    rng = random.Random(SEED)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for di, (destination, region) in enumerate(DESTINATIONS):
        base = 420 + di * 71
        price = 920 + (di % 5) * 215 + 90 * (di // 5)
        longhaul = 1.5 if di % 3 == 0 else (0.9 if di % 3 == 1 else 0.0)
        tier = 0.04 if di % 4 == 0 else (0.055 if di % 4 == 1 else (0.07 if di % 4 == 2 else 0.085))
        for month in range(1, 13):
            seasonal = 1 + 0.33 * math.sin((month - 2 + di % 3) * math.pi / 6)
            bookings = max(120, round(base * seasonal + rng.gauss(0, 38)))
            revenue = round(bookings * (price + rng.gauss(0, 42)), 2)
            refunds = round(revenue * (0.014 + (di % 4) * 0.007 + rng.uniform(0, 0.004)), 2)
            marketing = round((92000 + di * 12400) * (0.92 + month / 46) + rng.gauss(0, 4200), 2)
            rating = round(min(5, max(3.2, 4.58 - (di % 5) * 0.07 + rng.uniform(-0.11, 0.11))), 2)
            cancellations = max(0, round(bookings * (tier + rng.uniform(-0.004, 0.004))))
            trip_days = round(3.4 + longhaul + (di % 4) * 0.22 + rng.uniform(-0.3, 0.3), 1)
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
