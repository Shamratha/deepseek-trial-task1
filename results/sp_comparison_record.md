# SP Comparison Record — check1 (text_excel) — 2026-08-20

Task: benchmarks/check1_text_excel (destination_performance.csv → report.txt + analysis.xlsx)
Freeze: b55b14155074c6a1  ·  Repo: https://github.com/lakshitsachdeva/deepseek-trial  ·  Base commit: 3a66972

## Runs
- Run A (baseline / first attempt): `matrix-20260820T124825Z-bb2c94`
- Run B (recovered run, all arms PASS): `matrix-20260820T132719Z-6a0bd4`

## Comparison matrix

| Run | Arm | Wall (s) | Exit | Verifier score | Input tok | Cached in | Output tok | Cost (USD) | Final response |
|-----|-----|---------:|-----:|---------------:|----------:|----------:|-----------:|------------:|----------------|
| A | control_native_codex | 7.6 | 1 | 0 | — | — | — | — | no (auth error) |
| A | exp_codexcli_deepseek | 745.8 | 0 | 100 | 1,520,414 | 1,224,448 | 27,065 | — | yes |
| A | exp_claudecode_deepseek | 20.2 | 0 | 0 | 52,127 | 0 | 867 | 0.28231 | no (no files) |
| B | control_native_codex | 521.3 | 0 | 100 | 571,668 | 520,704 | 25,567 | — | yes |
| B | exp_codexcli_deepseek | 487.0 | 0 | 100 | 1,250,867 | 1,082,880 | 26,131 | — | yes |
| B | exp_claudecode_deepseek | 281.4 | 0 | 100 | 71,471 | 713,728 | 21,748 | 1.25792 | yes |

## Notes
- Run A: control failed with stale native auth (refresh_token_reused); claude code stopped after ~20s with no deliverables.
- Run B: all 3 arms PASS verifier 100/100, each producing report.txt + analysis.xlsx.
- Artifact hashes (Run B): control report `58f026c5...` xlsx `c5688294...`; codexcli report `ec30fa81...` xlsx `be2aebe2...`; claude report `0f5cc4f9...` xlsx `eb9d64d6...`
- Full captured responses/telemetry: `results/sp_response_record.json` (final assistant text per arm, usage, verifier, timing).
- Machine-readable summary: `results/all_runs.json` + `results/all_runs.csv` (6 rows).
