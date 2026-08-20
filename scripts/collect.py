#!/usr/bin/env python3
from infra_lib import read_run_rows, write_results

if __name__ == "__main__":
    rows = read_run_rows()
    write_results(rows)
    print(f"collected {len(rows)} runs")

