# Check 2 HARD — comparison (native Codex vs Codex CLI + DeepSeek)

Date: 2026-08-20
Task: benchmarks/check2_hard (authored by native Codex)
- Adds: Scenario & Sensitivity sheet (3 formula scenarios), 3 charts (combo + stacked seasonal) on chart-only sheets, >=2 embedded + captioned images, Executive Brief with 5 range-cited insights, reload-verification README.
- Inputs byte-identical to check2 (144 rows, same CSV/manifest schema, 10 image candidates).
- Text-only guidance added for DeepSeek arm: use bin/vision-helper for image inspection; never attach images to the model API.

## Results (final, all PASS)

| Arm | Model | Context | Wall (s) | Verifier | Score | Charts | Images | Files |
|-----|-------|---------|----------|----------|-------|--------|--------|-------|
| **Control (native Codex)** | gpt-5.6-sol (multimodal) | 1,050,000 | 1150.0 | PASS | 105/105 | 3 | 2 | visual_brief.xlsx + README.txt |
| **Exp (Codex CLI + DeepSeek)** | deepseek-v4-flash-0731 (text-only) | 1,310,720 | 1069.9 | PASS | 105/105 | 4 | 4 | visual_brief.xlsx + README.txt |

## Why first attempt failed, and fix
- Codex CLI 0.148 requires wire_api=responses; DeepSeek Flash is text-only. First attempt: agent tried to attach an image to the model -> OpenRouter 404 "no endpoints support image input".
- Fix: appended task guidance that the model is text-only; use bin/vision-helper for any image inspection, and embed images locally via openpyxl (no image input to the model API). Retry then passed 105/105 in 1069.9s.
- Finding: native Codex (multimodal) completed on first try; DeepSeek required text-only adaptation.

## Run IDs
- control: hard2-20260820T182837Z-1e531d (wall 1150.0)
- codexcli-pass: hard2b-20260820T190413Z-abc2df (wall 1069.9)
- codexcli-fail (pre-fix): hard2-20260820T184747Z-2b82bb (exit 1, 404 image input)
