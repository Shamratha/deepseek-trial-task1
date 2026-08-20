# Task 1 Comparison — text + Excel artifact

Run: `matrix-20260820T132719Z-6a0bd4` · date: 2026-08-20 · freeze: `b55b14155074c6a1`

## One-line summary

All 3 arms passed the official verifier with a perfect score (100/100). Claude Code + DeepSeek was
the **fastest and cheapest**; native Codex (control) was the slowest; Codex CLI + DeepSeek used the
most tokens.

## The table (easy version)

| Arm | What it is | Model | Wall time | Verifier | Input tokens | Output tokens | Cost (USD) | Files |
|-----|------------|-------|-----------|----------|--------------|---------------|------------|-------|
| 🎯 **Control** | Native Codex, your ChatGPT sub, no proxy | gpt-5.6-sol (native) | ~8 min 41 s* | ✅ 100/100 | 571.7k | 25.6k | not reported | `report.txt` + `analysis.xlsx` |
| 🧪 **Exp A** | Codex CLI via OpenRouter | deepseek-v4-flash-0731 | ~8 min 07 s* | ✅ 100/100 | 1.25M (1.08M cached) | 26.1k | not reported | `report.txt` + `analysis.xlsx` |
| 🧪 **Exp B** | Claude Code via OpenRouter | deepseek-v4-flash-0731 | ~4 min 41 s | ✅ 100/100 | 71.5k | 21.7k | **$1.26** | `report.txt` + `analysis.xlsx` |

\* Control and Exp A wall times are estimates from the last file write — the harness parent was
aborted after the arms finished, so their `end.json` is missing. Exp B's time is exact.

## Who wins what

- **All three**: verifier 100/100 — every arm produced a valid `report.txt` + `analysis.xlsx`.
- **Fastest**: Exp B (Claude Code + DeepSeek) — 281 s (~4.7 min).
- **Cheapest**: Exp B — $1.26 reported cost.
- **Most token-efficient**: Exp B — 71.5k input tokens vs 571.7k (control) and 1.25M (Exp A).
- **Control**: solid pass, but no cost/token-model detail exposed by the harness.

## Artifact hashes (sha256, first 16 chars)

| Arm | report.txt | analysis.xlsx |
|-----|-----------|---------------|
| control_native_codex | `58f026c58e09e146` | `c5688294a8073152` |
| exp_codexcli_deepseek | `ec30fa81195495b0` | `be2aebe213d72244` |
| exp_claudecode_deepseek | `0f5cc4f942e568e9` | `eb9d64d6bd871c57` |

## Raw run history (for the record)

- Run 1 `matrix-...124825Z`: codexcli PASS 100 (746 s); claude FAIL (no files — `unrecognized_model`); control FAIL (stale token).
- Run 2 `matrix-...132719Z`: all three PASS after login refresh + Claude fix.
- Claude arm in run 1 cost $0.28 with no output; in run 2 it produced files at $1.26.
