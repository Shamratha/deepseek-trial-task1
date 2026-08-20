# Operator runbook

This repository contains setup infrastructure only. Do not run measured arms until preflight, smoke, and freeze all pass. The setup session has not consumed any model routes.

```bash
./scripts/bootstrap.sh
```

Obtain an untouched Codex subscription, OpenRouter access to the pinned DeepSeek model, one confirmed cheap vision model, Athena or Gemini judge access, and the Check 3 team handoff.

```bash
export CONTROL_CODEX_HOME="$HOME/.codex-toby-control-20260820"
mkdir -p "$CONTROL_CODEX_HOME"
CODEX_HOME="$CONTROL_CODEX_HOME" codex login
```

Never copy an existing `auth.json`. Put secrets in the shell environment or `config/.env.local` (mode `0600`). Then run:

```bash
. .venv/bin/activate
python scripts/preflight.py
python scripts/smoke.py             # DeepSeek Codex/Claude + local/HTTPS vision setup probes
python scripts/freeze_experiment.py
```

The native control smoke is excluded by default. Add `--control` only if explicitly willing to consume a tiny call labeled `setup_smoke_not_measured`.

Measured execution (only after freeze):

```bash
python scripts/run_matrix.py --check check1 --parallel 3
python scripts/verify.py --check check1
python scripts/judge.py --check check1
python scripts/collect.py

python scripts/run_matrix.py --check check2 --parallel 3
python scripts/verify.py --check check2
python scripts/judge.py --check check2
python scripts/collect.py
```

Populate and validate `benchmarks/check3_e2e/source.lock.yaml` before the analogous Check 3 commands. Finish with:

```bash
python scripts/summarize.py
python scripts/package_results.py
```

Every measured run must use a fresh run ID and workspace. Never edit a frozen task, config, rubric, or input in place.
