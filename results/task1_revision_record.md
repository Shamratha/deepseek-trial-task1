# Task 1 (check1) dataset revision record

Date: 2026-08-20
Repo: https://github.com/lakshitsachdeva/deepseek-trial
Base commit: 3a66972 (main)

## Intent
Modify Task 1 benchmark data "a bit" while preserving the exact benchmark format
(CSV + task.md + brief.txt + manifest.json + deterministic generator, workbook
deliverables `report.txt` + `analysis.xlsx`, same 10 columns).

## What changed
- `benchmarks/check1_text_excel/generate_input.py`: seed 20260820 -> 20260731;
  8 destinations -> 12 (added Singapore, Vancouver, Marrakech, Queenstown);
  revised pricing/tiering/seasonality/risk formulas; row count 96 -> 144.
  Format (columns, filenames, manifest schema) unchanged.
- `benchmarks/check1_text_excel/input/destination_performance.csv`: regenerated.
- `benchmarks/check1_text_excel/manifest.json`: seed/rows/sha256 updated.
- `benchmarks/check2_visual_artifact/generate_input.py`: derive manifest `rows`
  from the copied CSV instead of hardcoding 96.
- `benchmarks/check2_visual_artifact/input/destination_performance.csv`:
  byte-identical copy of the new shared dataset (shared_dataset_with check1).
- `benchmarks/check2_visual_artifact/manifest.json`: seed/rows/sha256 updated.
- `deepseek_v4_flash_harness_eval_infra_spec.md` section 9.1: seed + shape updated.
- `tests/test_infrastructure.py`: shape/seed assertions updated (144 rows, 12 dests).

## New hashes
- CSV (shared): `499587d2285a8b9c595b6b680854b5fd2aa93bb7324fc89e38f9cae3e015f5eb`
- check1 manifest: `166ad588f55ed371e2a51adf4e1cc267c7145f50a1ed96bf34dafb31d044b46c`
- check2 manifest: `f2e2ad748684529bf5858aad52b8b56563c79c3c2c2268a63ccbf1bc62147582`

## Old hashes (baseline, for reference)
- CSV: `0f29f24f6f326b7ebca146603c018e6c76fcf080298572b2c18dec8dea0d0a4a`
- check1 manifest: `883f9e9` git blob; generator: seed 20260820

## Validation
- `pytest -q`: 20 passed.
- check1 verifier against generated artifact: pass 100/100.
- check2 shared dataset: byte-identical copy confirmed.

## Task 1 deliverables (sample output)
Location: `results/task1_output/` (report.txt + analysis.xlsx)
- verifier: PASS 100/100 (all checks true, 191 formulas)
- report.txt: 3847 bytes
- analysis.xlsx sheets: Raw Data, Destination Summary, Monthly Summary, Key Metrics
