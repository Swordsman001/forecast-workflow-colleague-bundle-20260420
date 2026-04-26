# Calibration Gate

Use calibration only as a workflow gate, not as a replacement for forecast judgment.

Purpose:

- prove that the workbook map and formula dependencies are trustworthy enough for substantive patching
- detect broken transmission chains before a full forecast update
- prevent a run from appearing complete when drivers were written but outputs did not move as expected

## When To Use

Use calibration when:

- a company workbook is being onboarded for the first time
- the workbook structure changed materially
- a previous run showed that drivers were written but key outputs did not follow
- summary rows or parent totals appear disconnected from expected driver rows

## Required Calibration Artifacts

Produce:

- `transmission_chain.md` or equivalent structured note
- `calibration_cases.json`
- `calibration_result.json`

## Transmission Chain Template

For each major segment, record:

- `segment`
- `driver_rows`
- `expected_output_rows`
- `expected_parent_totals`
- `expected_profit_bridge_rows`
- `notes`

Example shape:

```json
{
  "segment": "segment_alpha",
  "driver_rows": ["segment_alpha_asp", "segment_alpha_volume", "segment_alpha_share", "segment_alpha_gm"],
  "expected_output_rows": ["segment_alpha_revenue", "segment_alpha_gp"],
  "expected_parent_totals": ["segment_total", "design_revenue", "total_revenue"],
  "expected_profit_bridge_rows": ["gross_profit", "operating_profit", "attributable_net_profit"],
  "notes": "segment_alpha_revenue should move first, then segment and consolidated rows should tie through"
}
```

## Calibration Test Pattern

Each calibration case should:

1. change one representative driver by a small controlled amount
2. observe whether the expected downstream rows move
3. verify that unrelated rows do not move unexpectedly

Examples:

- raise `segment_alpha_asp` by 1% and confirm `segment_alpha_revenue`, `segment_total`, and `gross_profit` move in the expected direction
- lower `segment_beta_share` by 1% and confirm `segment_beta_revenue` and parent totals decrease
- raise `selling_rate` modestly and confirm profit rows weaken without changing revenue rows

## Pass Criteria

Calibration passes only if:

- the expected segment output row changes
- the expected parent total changes
- the expected profit-bridge row changes when relevant
- the movement direction matches the transmission-chain expectation

## Fail Criteria

Calibration fails if:

- a driver row changes but the expected segment output row does not
- a segment output row changes but the expected parent total does not
- summary or display rows stay stale while lower rows move
- formula copy or rollforward logic points to the wrong year or wrong row

If calibration finds issues, first classify them:

- `auto_repairable_issues`
- `hard_blockers`

Auto-repairable issues should be repaired immediately and then calibration should be rerun on the repaired workbook state.

Typical auto-repairable issues include:

- summary or display formulas that did not extend into the new forecast columns
- simple summary rows that point to the wrong source row when the intended source can be inferred unambiguously
- deterministic rollforward copy gaps that can be repaired without reopening forecast judgment

Only stop when hard blockers remain after repair, such as:

- source-row ambiguity that cannot be resolved safely
- broken transmission chains where the expected driver-output-parent path is not identifiable
- display repair that would require inventing new business logic rather than restoring deterministic structure

Do not move into substantive patching until calibration passes, but do not treat auto-repairable issues as permanent stop conditions.
