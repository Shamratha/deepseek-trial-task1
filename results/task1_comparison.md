# Task 1 Comparison Record (check1_text_excel)

Date: 2026-08-20
Status: **NOT YET MEASURED** — arm runs pending. This table is the scaffold; blanks will be filled by harness runs.

## Comparison matrix

| Arm | Status | Wall time | Verifier | Judge | Artifact SHA |
|-----|--------|-----------|----------|-------|--------------|
| control_native_codex (native, no proxy) | pending | — | — | — | — |
| exp_codexcli_deepseek (codexcli + deepseek/deepseek-v4-flash-0731 via OpenRouter) | pending | — | — | — | — |
| exp_claudecode_deepseek (claude code + deepseek/deepseek-v4-flash-0731 via OpenRouter) | pending | — | — | — | — |

## Reference artifacts recorded so far (NOT measured arm runs)
- Dataset revision record: results/task1_revision_record.md
- Sample artifact produced locally by setup agent: results/task1_output/report.txt + analysis.xlsx
  - verifier: PASS 100/100 (this is a hand-made gold-ish sample, not an arm run, and carries no harness wall-clock)
- Claude prompts saved: results/claude_run_prompts/CHECK1_PROMPT_TO_CLAUDE.md

## What must be captured per arm when run
- wall_seconds (timing) from run starts/ends
- stdout.jsonl + stderr.txt per run
- verify.py result (score/pass)
- judge.py result (blind judge score)
- artifact hashes (report.txt, analysis.xlsx)
- run_id + freeze_id

## Blockers before measurement
- Claude binary must work (currently n/a in this sandbox).
- OPENROUTER_API_KEY must be present.
- Control CODEX_HOME (native login) must be provisioned.
- check1 timeouts configured (done: 3600s).
