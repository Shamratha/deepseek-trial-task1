# DeepSeek V4 Flash 0731 Harness Evaluation — Infrastructure Setup Specification

> **Purpose:** hand this file to a setup-only Codex session and ask it to build the experiment infrastructure exactly as specified.  
> **Do not run the measured experiments during infrastructure setup.**  
> **Do not use Parsewave `codx` for any measured arm.**  
> **Do not alter the assignment by adding planner/hybrid/Hermes/Ygg experiments.**

---

## 0. Assignment being implemented

We need to evaluate **DeepSeek V4 Flash 0731** under two different coding harnesses, with a **native non-proxy Codex subscription** as the gold control.

There are exactly three checks:

1. **Text + Excel artifact**
   - create an artifact workflow that produces text and Excel files.

2. **Graphs + web images artifact**
   - add one fixed, very cheap vision model from OpenRouter;
   - create an artifact containing useful graphs and web images.

3. **Full end-to-end task**
   - make a complete task in the field of **JobBench or OpenClaw**;
   - coordinate with someone from the OpenClaw team to obtain the current task format/pipeline, seed/idea, and official validation flow.

For **every check**, collect:
- quality,
- wall-clock time,
- tokens,
- cost,
- completion/failure,
- human interventions.

For **every check**, compare the same three arms:

| Arm | Harness | Main model/provider | Purpose |
|---|---|---|---|
| `control_native_codex` | plain Codex CLI | native Codex subscription, **not proxy** | gold control |
| `exp_codexcli_deepseek` | plain Codex CLI | OpenRouter → `deepseek/deepseek-v4-flash-0731` | experiment |
| `exp_claudecode_deepseek` | Claude Code CLI | OpenRouter → `deepseek/deepseek-v4-flash-0731` | experiment |

The experiment asks:

1. how close does DeepSeek V4 Flash 0731 get to native Codex on real artifact/task work?
2. with the **same DeepSeek model**, does Codex CLI or Claude Code extract better performance?

There is **no planner → executor handoff in this assignment**.

---

# 1. Non-negotiable experimental rules

## 1.1 Control means native Codex subscription

The control must use:

```text
plain `codex`
+
a fresh / untouched ChatGPT-Codex subscription
+
normal native Codex routing
```

The control must **not** use:

```text
codx
Parsewave proxy
OpenRouter as the main model route
OPENAI_BASE_URL overrides
custom model providers
copied auth from another measured arm
```

Do not select a control model silently. If the native subscription has a default model, record the actual model reported by the CLI at run time. If the operator explicitly pins a native Codex model later, record that exact model.

## 1.2 Experimental model must be pinned exactly

Use:

```text
deepseek/deepseek-v4-flash-0731
```

Do not use a latest alias, another DeepSeek revision, provider fallback to a different model, or a Parsewave alias.

## 1.3 Same task, same inputs, same permissions

Within a check, the three arms must receive the same task prompt bytes, input bytes, starting structure, output requirements, timeout, verifier, and judge rubric.

## 1.4 No cross-arm state

Each measured run starts in a fresh workspace.

Never resume a prior Codex thread, continue a Claude session, copy generated files from another arm, or share session/memory files.

Use Codex `--ephemeral` and Claude Code `--no-session-persistence` if the installed version supports it. Preflight must inspect the installed CLI help before assuming a flag exists.

## 1.5 Setup model is not an evaluated model

The Codex session receiving this specification is **infrastructure-only**. It may create directories, scripts, deterministic benchmark inputs, verifiers, configuration templates, and local tests.

It must **not** run the nine measured benchmark arms, consume the untouched Codex control subscription, judge experiment outputs, or fabricate results.

---

# 2. Verified external assumptions as of 2026-08-20

## 2.1 DeepSeek model

OpenRouter slug:

```text
deepseek/deepseek-v4-flash-0731
```

## 2.2 Codex CLI custom provider

Codex CLI supports a custom provider under `$CODEX_HOME/config.toml`.

For OpenRouter:

```toml
model = "deepseek/deepseek-v4-flash-0731"
model_provider = "openrouter"

[model_providers.openrouter]
name = "OpenRouter"
base_url = "https://openrouter.ai/api/v1"
env_key = "OPENROUTER_API_KEY"
wire_api = "responses"
```

Custom provider configuration must live in the user-level Codex home config, so use an isolated `CODEX_HOME`.

## 2.3 Claude Code through an LLM gateway

Route Claude Code through OpenRouter using:

```text
ANTHROPIC_BASE_URL=https://openrouter.ai/api
ANTHROPIC_AUTH_TOKEN=<OpenRouter key>
```

Pin DeepSeek for the main model and all default model slots so a hidden model/subagent switch cannot accidentally call Anthropic.

## 2.4 Do not use OpenRouter `ori` for measured runs

`ori` may be useful for diagnosis, but measured runs should use transparent explicit configuration so the exact harness configuration is reproducible.

---

# 3. Required repository layout

Create:

```text
deepseek-v4-harness-eval/
├── README_RUN_ME.md
├── INFRA_NOTES.md
├── experiment.yaml
├── pyproject.toml
├── uv.lock
├── .gitignore
├── config/
│   ├── env.example
│   ├── codex-deepseek-config.toml
│   ├── claude-deepseek.env.template
│   ├── judge.yaml
│   └── vision.yaml
├── benchmarks/
│   ├── check1_text_excel/
│   │   ├── task.md
│   │   ├── generate_input.py
│   │   ├── input/
│   │   │   ├── destination_performance.csv
│   │   │   └── brief.txt
│   │   └── manifest.json
│   ├── check2_visual_artifact/
│   │   ├── task.md
│   │   ├── generate_input.py
│   │   ├── input/
│   │   │   ├── destination_performance.csv
│   │   │   ├── brief.txt
│   │   │   └── image_candidates.txt
│   │   └── manifest.json
│   └── check3_e2e/
│       ├── README_WAIT_FOR_OPENCLAW_TEAM.md
│       ├── source.lock.yaml
│       └── input/
├── graders/
│   ├── check1_verify.py
│   ├── check2_verify.py
│   ├── check3_verify_adapter.py
│   ├── make_judge_packet.py
│   ├── run_judge.py
│   └── rubrics/
│       ├── check1.md
│       ├── check2.md
│       └── check3.md
├── tools/
│   ├── vision_daemon.py
│   ├── vision_helper.py
│   └── artifact_inspect.py
├── scripts/
│   ├── bootstrap.sh
│   ├── preflight.py
│   ├── smoke.py
│   ├── freeze_experiment.py
│   ├── prepare_workspaces.py
│   ├── run_arm.py
│   ├── run_matrix.py
│   ├── collect.py
│   ├── verify.py
│   ├── judge.py
│   ├── summarize.py
│   ├── package_results.py
│   └── secret_scan.py
├── state/
├── workspaces/
├── runs/
├── results/
└── packages/
```

The setup should be runnable on macOS.

---

# 4. Secrets and authentication

## 4.1 Never track credentials

Create `config/env.example`:

```bash
OPENROUTER_API_KEY=
VISION_MODEL=
VISION_OPENROUTER_API_KEY=
CONTROL_CODEX_HOME=
JUDGE_MODE=athena
ATHENA_BASE_URL=
ATHENA_API_KEY=
ATHENA_MODEL=
GEMINI_API_KEY=
GEMINI_JUDGE_MODEL=gemini-3.7-flash
```

Real values must come from shell environment or gitignored `config/.env.local` with mode `0600`.

Add to `.gitignore`:

```gitignore
config/.env.local
state/
workspaces/
runs/
packages/
*.secret
*.token
auth.json
```

## 4.2 Native Codex control home

The infrastructure creates **no auth token**.

The operator will later run:

```bash
export CONTROL_CODEX_HOME="$HOME/.codex-toby-control-20260820"
mkdir -p "$CONTROL_CODEX_HOME"
CODEX_HOME="$CONTROL_CODEX_HOME" codex login
```

Preflight must reject the control if its config contains OpenRouter, Parsewave, a custom model provider, or custom `OPENAI_BASE_URL`.

Do not copy an existing `~/.codex/auth.json` into this directory.

## 4.3 DeepSeek Codex home

Create `state/codex-deepseek-home/config.toml` from the tracked template:

```toml
model = "deepseek/deepseek-v4-flash-0731"
model_provider = "openrouter"
approval_policy = "never"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = true

[model_providers.openrouter]
name = "OpenRouter"
base_url = "https://openrouter.ai/api/v1"
env_key = "OPENROUTER_API_KEY"
wire_api = "responses"
```

Never store the key in this directory.

---

# 5. Harness commands

## 5.1 Native Codex control

Primary command:

```bash
CODEX_HOME="$CONTROL_CODEX_HOME" codex exec   --ephemeral   --json   --skip-git-repo-check   --sandbox workspace-write   "<EXACT TASK PROMPT>"
```

Do not pass `codx`, a custom provider, or Parsewave/OpenRouter main-model routing.

For networked checks, preflight network access first. If macOS sandbox networking fails, record the failure and require an explicit operator-approved fallback. Do not silently switch permissions.

## 5.2 Codex CLI + DeepSeek

```bash
CODEX_HOME="<ROOT>/state/codex-deepseek-home" OPENROUTER_API_KEY="$OPENROUTER_API_KEY" codex exec   --ephemeral   --json   --skip-git-repo-check   --sandbox workspace-write   "<EXACT TASK PROMPT>"
```

Snapshot the active sanitized config into run metadata.

## 5.3 Claude Code + DeepSeek

Routing environment:

```bash
ANTHROPIC_BASE_URL="https://openrouter.ai/api"
ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY"
ANTHROPIC_API_KEY=""
OPENROUTER_API_KEY="$OPENROUTER_API_KEY"

ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek/deepseek-v4-flash-0731"
ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek/deepseek-v4-flash-0731"
ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek/deepseek-v4-flash-0731"
CLAUDE_CODE_SUBAGENT_MODEL="deepseek/deepseek-v4-flash-0731"

CLAUDE_CODE_SKIP_FAST_MODE_ORG_CHECK=1
CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1
```

Primary command:

```bash
claude   -p   --model "deepseek/deepseek-v4-flash-0731"   --output-format stream-json   --verbose   --permission-mode bypassPermissions   --no-session-persistence   "<EXACT TASK PROMPT>"
```

Preflight must inspect `claude --help`.

### Compatibility tuning

Any Claude/OpenRouter compatibility adjustment is allowed **only during smoke testing**. Once smoke passes:
- freeze the exact environment;
- hash it;
- use it unchanged for all measured Claude-Code DeepSeek runs.

Do not patch compatibility mid-experiment.

---

# 6. Preflight

`scripts/preflight.py` should verify:

```text
codex exists
claude exists
python >= 3.11
git exists
curl exists
OPENROUTER_API_KEY present before experimental run
CONTROL_CODEX_HOME present before control run
native control auth exists
native control contains no proxy/custom provider
DeepSeek Codex config exists
DeepSeek slug is exact
Claude env pins all model slots
network works when required
vision model configured before check 2
judge configured before judging
check 3 source lock complete before check 3
```

Record versions into `results/environment.json`:

```text
codex --version
claude --version
python --version
git --version
uname -a
macOS version
```

Never print credential values.

---

# 7. Smoke tests

Create smoke tests but do not execute them automatically during setup.

Operator invokes:

```bash
python scripts/smoke.py
```

## 7.1 DeepSeek through Codex CLI

Exact reply:

```text
DEEPSEEK_CODEX_ROUTE_OK
```

Then a disposable file-write/read probe.

Validate process exit, file creation, exact model where exposed, and raw JSONL capture.

## 7.2 DeepSeek through Claude Code

Exact reply:

```text
DEEPSEEK_CLAUDE_ROUTE_OK
```

Then a file-write/read probe.

Validate process exit, model identity where exposed, and parseable stream-json.

## 7.3 Native control

Do not consume the control subscription unless the operator explicitly enables a tiny setup smoke call. Label such a call `setup_smoke_not_measured`.

## 7.4 Vision

After `VISION_MODEL` is confirmed, test one local image and one HTTPS image URL. Save raw response and exact reported usage/cost.

---

# 8. Shared run isolation

Measured workspaces:

```text
workspaces/<check>/<run_id>/<arm>/
```

Each begins with only:
- byte-identical `task.md`;
- byte-identical `input/`;
- `bin/vision-helper` when check 2 needs it.

Do not expose grader source, expected answers, judge rubric, other-arm output, hypothesis, or prior logs.

---

# 9. Check 1 — text + Excel artifact

This benchmark is locally created because the assignment specifies a capability, not a named task.

## 9.1 Dataset

Generate deterministic `destination_performance.csv` using seed `20260820`.

Suggested shape:
- 8 destinations;
- 12 months;
- 96 rows.

Columns:

```text
month
destination
region
bookings
gross_revenue
refunds
marketing_spend
customer_rating
cancellations
avg_trip_days
```

Create realistic synthetic variation. Do not encode narrative answer labels.

## 9.2 Task

Use:

```text
You are given destination_performance.csv and brief.txt.

Create exactly two final deliverables under final/:

1. report.txt
2. analysis.xlsx

report.txt must be a concise management analysis of the data. It should identify
the most important performance patterns, quantify the conclusions, and call out
material tradeoffs or risks.

analysis.xlsx must be a usable workbook, not a CSV renamed to xlsx. It must
contain:
- Raw Data
- Destination Summary
- Monthly Summary
- Key Metrics

Preserve the source data in Raw Data. Derive useful summary metrics from the
source data and use formulas where appropriate rather than hard-coding every
summary value.

Do not include charts, pictures, or other image assets in this check.

Before finishing, verify that both files exist and that the workbook opens
successfully.

Do not create any other final deliverables.
```

## 9.3 Deterministic verifier

Recompute truth from CSV and verify:
- both files exist;
- workbook opens;
- required sheets exist;
- raw row count matches;
- source data is preserved;
- summary sheets are non-trivial;
- a reasonable number of formulas exists;
- no obvious broken references;
- key metrics agree with independently recomputed values.

Do not require one exact visual layout.

## 9.4 Blind judge

Judge correctness, usefulness, clarity, workbook/report agreement, and spreadsheet usability.

---

# 10. Check 2 — graphs + web images + cheap vision

Use the same underlying dataset so added difficulty is visual/artifact work.

## 10.1 Vision model

Do not invent the final cheap model. Use:

```text
VISION_MODEL=<confirmed OpenRouter vision model>
```

Freeze it in `config/vision.yaml`.

Expose the same fixed helper to all three arms. The native Codex main model remains non-proxy/native.

## 10.2 Vision sidecar

Do not expose the vision key directly to native Codex.

Implement:

```text
runner
  -> vision_daemon.py
       owns VISION_OPENROUTER_API_KEY
       binds 127.0.0.1 only
       calls frozen OpenRouter vision model
       logs usage
       returns model answer

workspace/bin/vision-helper
  -> local daemon
```

Interface:

```bash
bin/vision-helper --url "https://..." --question "..."
bin/vision-helper --file "path/to/image.jpg" --question "..."
```

Log model, source, duration, exact reported tokens/cost, response id, and success/error. Missing telemetry is `null`.

## 10.3 Web image candidates

Create `image_candidates.txt` with at least 6 stable HTTPS image URLs from reputable public web sources relevant to the destinations.

During setup:
- verify each returns an image;
- record MIME type;
- prefer stable sources such as Wikimedia Commons.

The measured agent chooses which images to use.

## 10.4 Task

```text
You are given destination_performance.csv, brief.txt, and a list of candidate
web-image URLs in image_candidates.txt.

Create a polished Excel artifact at:

final/visual_brief.xlsx

The workbook must:
- contain the source data and useful summary analysis;
- contain at least two meaningful charts derived from the data;
- include at least two relevant images obtained from the web-image URLs;
- include the chosen images inside the workbook, not only as hyperlinks;
- contain a Sources sheet listing the source URL for each included web image;
- use the available `bin/vision-helper` when visual inspection of an image is
  needed;
- make the charts/images materially relevant rather than decorative.

Before finishing, verify that the workbook opens successfully and that the
requested charts, images, and source URLs are present.

Do not create any other final deliverable.
```

## 10.5 Deterministic verifier

Verify:
- workbook exists/opens;
- source data present;
- >= 2 chart objects;
- >= 2 embedded images;
- Sources sheet;
- >= 2 valid HTTPS source URLs from the candidate list;
- summary values consistent with CSV;
- no broken workbook relationships.

Aesthetics remain judge-scored.

## 10.6 Blind judge

Judge analytical correctness, chart choice/readability, image relevance, workbook organization, and overall usefulness.

---

# 11. Check 3 — full JobBench or OpenClaw task

Do **not** invent this benchmark during setup.

Create `benchmarks/check3_e2e/README_WAIT_FOR_OPENCLAW_TEAM.md` with:

```text
[ ] team contact / owner
[ ] field chosen: JobBench OR OpenClaw
[ ] source repository
[ ] pinned repository commit/ref
[ ] current task template or pipeline
[ ] one fixed idea/seed
[ ] exact authoring/build instruction
[ ] exact required output package
[ ] exact environment/bootstrap command
[ ] official deterministic verifier command
[ ] expected oracle/reference behavior if applicable
[ ] timeout recommendation
[ ] required credentials/resources
```

Create:

```yaml
# source.lock.yaml
ready: false
field: null
owner: null
repo: null
ref: null
seed: null
run_command: null
verify_command: null
notes: null
```

Refuse check 3 while `ready: false`.

Once the team provides the known-good setup:
- freeze one seed/idea;
- make three identical starting copies;
- let each arm produce the full task;
- run the same official verifier.

---

# 12. Timing

Measure externally with UTC wall clock plus `time.monotonic_ns()`.

Store:

```json
{
  "start_utc": "...",
  "end_utc": "...",
  "wall_seconds": 0.0,
  "timeout_seconds": 3600,
  "timed_out": false,
  "exit_code": 0
}
```

Agent wall time excludes verifier and judge time. Vision helper time occurs inside agent wall time but is also logged separately.

---

# 13. Raw telemetry

For each run:

```text
runs/<check>/<run_id>/<arm>/
├── manifest.json
├── task.md
├── input_manifest.json
├── command.json
├── start.json
├── end.json
├── stdout.jsonl
├── stderr.txt
├── exit_code.txt
├── usage.json
├── vision_usage.json
├── verifier.json
├── judge.json
├── human_interventions.jsonl
└── output/
```

`command.json` contains environment variable names, never secret values.

---

# 14. Token and cost collection

Collect exact telemetry only.

Never:
- invent token counts;
- treat missing as zero;
- double-count reasoning tokens that are already included in output.

Use `null` when absent.

## Codex

Parse exact fields when emitted:
- input tokens;
- cached input;
- output;
- reasoning output;
- total;
- actual model/provider where emitted.

## Claude Code

Capture:
- final result event;
- duration;
- API duration;
- turns;
- reported total cost;
- per-message usage;
- modelUsage if present;
- actual model where present.

Typical usage fields may include:
- `input_tokens`;
- `cache_read_input_tokens`;
- `cache_creation_input_tokens`;
- `output_tokens`.

## OpenRouter

Prefer exact provider-reported cost. If unavailable, `reported_cost_usd = null`. A separate `estimated_cost_usd` may be computed later from a frozen price snapshot, but never called actual spend.

## Vision

Track main and vision spend separately. Only populate combined actual cost when both components are known exactly.

---

# 15. Human interventions

Create an empty `human_interventions.jsonl` for every run.

Any manual action after agent launch that modifies process/workspace/output is logged with UTC timestamp, action, reason, and changed files.

If none: `0`.

---

# 16. Neutral prompts

Do not tell evaluated agents:
- which arm they are;
- that they are cheap;
- that they compete against Codex;
- expected outcome;
- experiment hypothesis.

Same task bytes for all arms.

---

# 17. Blind judging

Preferred judge: Athena. Fallback: Gemini 3.7 Flash.

Before judging:
1. randomize outputs into A/B/C;
2. store mapping separately;
3. give identical rubric;
4. require structured JSON;
5. do not reveal native Codex identity.

`config/judge.yaml`:

```yaml
mode: athena

athena:
  base_url_env: ATHENA_BASE_URL
  api_key_env: ATHENA_API_KEY
  model_env: ATHENA_MODEL

gemini:
  api_key_env: GEMINI_API_KEY
  model: gemini-3.7-flash
```

Do not hardcode Athena details until confirmed.

---

# 18. Final metrics schema

```text
check_id
run_id
arm
harness
configured_model
actual_model
provider
status
exit_code
timed_out
wall_seconds
input_tokens
cached_input_tokens
cache_creation_input_tokens
output_tokens
reasoning_output_tokens
total_tokens
main_model_reported_cost_usd
vision_calls
vision_input_tokens
vision_output_tokens
vision_reported_cost_usd
combined_reported_cost_usd
deterministic_score
official_verifier_pass
official_verifier_score
judge_score
human_interventions
files_created
notes
```

Export:
- `results/all_runs.csv`
- `results/all_runs.json`
- `results/summary.md`

---

# 19. Matrix execution

Support:

```bash
python scripts/run_matrix.py --check check1 --parallel 3
python scripts/run_matrix.py --check check2 --parallel 3
python scripts/run_matrix.py --check check3 --parallel 3
```

Each arm gets separate CWD, logs, temp directory, output directory, and process group.

Default artifact timeout: 3600 seconds. Check 3 timeout comes from the team handoff.

---

# 20. Freeze step

Before measured runs:

```bash
python scripts/freeze_experiment.py
```

Create `results/frozen_manifest.json` containing:
- DeepSeek slug;
- CLI versions;
- sanitized Codex config hash;
- sanitized Claude environment hash;
- task hashes;
- input tree hashes;
- vision model;
- judge config;
- timeouts;
- grader hashes;
- check 3 source lock when ready.

After freeze, changing measured task/config requires a new freeze ID.

---

# 21. Infrastructure unit tests

During setup, run only local non-model tests:

```text
benchmark generators deterministic
input hashes stable
workspace copies byte-equivalent
secret redaction works
Codex config contains exact slug
Claude env pins all model slots
runner captures timing/stdout/stderr/exit
timeout kills process group
collector maps absent telemetry to null
collector does not double-count reasoning
check1 verifier catches malformed workbook
check2 verifier detects chart/image counts
judge anonymization works
result schema stable
secret scanner catches fake-token fixtures
```

Use synthetic JSONL telemetry fixtures.

---

# 22. Packaging and secret scan

Package:
- frozen sanitized configs;
- exact prompts;
- input manifests;
- raw logs;
- timings;
- usage;
- vision logs;
- outputs;
- verifier evidence;
- judge evidence;
- summary;
- environment versions;
- human intervention logs.

Never package:
- `auth.json`;
- `.env.local`;
- API keys;
- OAuth/access/refresh tokens.

Abort package generation if secret scan finds likely values such as `sk-or-`, bearer tokens, access tokens, or refresh tokens.

---

# 23. Central experiment config

Create `experiment.yaml`:

```yaml
experiment:
  name: deepseek-v4-flash-0731-harness-eval
  assignment: toby
  measured_arms:
    - control_native_codex
    - exp_codexcli_deepseek
    - exp_claudecode_deepseek

model:
  deepseek: deepseek/deepseek-v4-flash-0731

arms:
  control_native_codex:
    harness: codex_cli
    provider: native_subscription
    model: native_default
    proxy_allowed: false

  exp_codexcli_deepseek:
    harness: codex_cli
    provider: openrouter
    model: deepseek/deepseek-v4-flash-0731

  exp_claudecode_deepseek:
    harness: claude_code
    provider: openrouter
    model: deepseek/deepseek-v4-flash-0731

checks:
  check1:
    name: text_excel_artifact
    timeout_seconds: 3600
    vision_enabled: false

  check2:
    name: graphs_web_images_artifact
    timeout_seconds: 3600
    vision_enabled: true

  check3:
    name: jobbench_or_openclaw_e2e
    timeout_seconds: null
    requires_external_lock: true

judge:
  preferred: athena
  fallback: gemini-3.7-flash
  blind: true
```

---

# 24. Operator README sequence

Generate `README_RUN_ME.md` with:

```bash
./scripts/bootstrap.sh
```

Then operator obtains:
- untouched Codex sub;
- OpenRouter/DeepSeek access;
- cheap vision model;
- Athena or Gemini judge access;
- OpenClaw/JobBench team handoff.

Authenticate control manually:

```bash
export CONTROL_CODEX_HOME="$HOME/.codex-toby-control-20260820"
CODEX_HOME="$CONTROL_CODEX_HOME" codex login
```

Then:

```bash
python scripts/preflight.py
python scripts/smoke.py
python scripts/freeze_experiment.py
```

Run check 1:

```bash
python scripts/run_matrix.py --check check1 --parallel 3
python scripts/verify.py --check check1
python scripts/judge.py --check check1
python scripts/collect.py
```

Run check 2:

```bash
python scripts/run_matrix.py --check check2 --parallel 3
python scripts/verify.py --check check2
python scripts/judge.py --check check2
python scripts/collect.py
```

Populate check 3 team lock, then:

```bash
python scripts/run_matrix.py --check check3 --parallel 3
python scripts/verify.py --check check3
python scripts/judge.py --check check3
python scripts/collect.py
```

Finally:

```bash
python scripts/summarize.py
python scripts/package_results.py
```

---

# 25. Do not guess unresolved resources

Leave explicit blockers rather than inventing:
- which untouched Codex account;
- whether a native Codex model should be pinned;
- final cheap vision model;
- Athena endpoint/key/model;
- OpenClaw/JobBench owner;
- exact check 3 repo/ref/template/seed/verifier;
- check 3 timeout.

---

# 26. Do not expand scope

Do not add:
- planner → DeepSeek;
- Hermes;
- Yggdrasil harness comparison;
- OpenCode;
- GLM;
- Kimi;
- Meta Muse;
- extra DeepSeek versions;
- multiple vision models;
- multiple control baselines.

---

# 27. Expected final comparison

| Check | Arm | Quality | Time | Main tokens | Vision tokens | Cost | Status |
|---|---|---:|---:|---:|---:|---:|---|
| text + Excel | native Codex | | | | — | | |
| text + Excel | DeepSeek / Codex CLI | | | | — | | |
| text + Excel | DeepSeek / Claude Code | | | | — | | |
| graphs + web images | native Codex | | | | | | |
| graphs + web images | DeepSeek / Codex CLI | | | | | | |
| graphs + web images | DeepSeek / Claude Code | | | | | | |
| full JobBench/OpenClaw | native Codex | | | | | | |
| full JobBench/OpenClaw | DeepSeek / Codex CLI | | | | | | |
| full JobBench/OpenClaw | DeepSeek / Claude Code | | | | | | |

Keep separate:
- process completion;
- deterministic verifier quality;
- LLM judge quality;
- actual/reported spend;
- estimates.

---

# 28. Definition of infrastructure complete

```text
[ ] repository layout exists
[ ] no real secrets tracked
[ ] native control isolated from proxy/custom providers
[ ] DeepSeek Codex has isolated CODEX_HOME
[ ] Claude Code pins DeepSeek in all model slots
[ ] check 1 input/task/verifier exist
[ ] check 2 input/task/verifier + vision sidecar exist
[ ] check 3 blocked pending team handoff
[ ] runner captures raw telemetry/time/exit/output
[ ] collector preserves missing values as null
[ ] blind judge flow exists
[ ] parallel three-arm execution exists
[ ] freeze/hash mechanism exists
[ ] packaging + secret scan exist
[ ] local infrastructure tests pass
[ ] measured experiments have NOT been run
```

At the end of setup, print only:

```text
INFRA_READY=<true|false>
LOCAL_TESTS=<passed>/<total>
CONTROL_AUTH_READY=<true|false>
OPENROUTER_READY=<true|false>
VISION_MODEL_READY=<true|false>
JUDGE_READY=<true|false>
CHECK3_TEAM_LOCK_READY=<true|false>

NEXT_BLOCKERS:
- ...
```

Then stop. Do not launch measured experiments automatically.

---

# 29. Reproducibility rules

1. Keep raw logs even if parsing fails.
2. Never rewrite model output.
3. Never manually repair artifacts without recording intervention.
4. Keep setup/smoke traffic separate from measured traffic.
5. One frozen benchmark instance per check for all arms.
6. Harness incompatibility is a result unless proven to be shared infrastructure failure.
7. Shared infrastructure bugs require a new freeze ID and full affected-check rerun.
8. Never reuse an invalid run as measured.
9. Never alter judge rubric after unblinding.
10. Preserve exact CLI versions.

---

# 30. Reference assumptions

Validated on 2026-08-20 against current OpenAI Codex custom-provider behavior, OpenRouter Codex/Claude Code integration guidance, the OpenRouter DeepSeek V4 Flash 0731 model page, and Anthropic Claude Code CLI/gateway documentation.

If installed CLI behavior disagrees:
1. capture installed version;
2. capture relevant `--help`;
3. adapt only during preflight/smoke;
4. document the change;
5. freeze final measured configuration before any real run.
