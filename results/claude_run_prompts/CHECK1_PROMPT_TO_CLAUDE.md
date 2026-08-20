# Prompt to give Claude Code — Check 1 (text + Excel artifact)

You are given input/destination_performance.csv and input/brief.txt.

Create exactly two final deliverables under final/:

1. report.txt
2. analysis.xlsx

report.txt must be a concise management analysis of the data. It should identify the most important performance patterns, quantify the conclusions, and call out material tradeoffs or risks.

analysis.xlsx must be a usable workbook, not a CSV renamed to xlsx. It must contain:
- Raw Data
- Destination Summary
- Monthly Summary
- Key Metrics

Preserve the source data in Raw Data. Derive useful summary metrics from the source data and use formulas where appropriate rather than hard-coding every summary value.

Do not include charts, pictures, or other image assets in this check.

Before finishing, verify that both files exist and that the workbook opens successfully.

Do not create any other final deliverables.
