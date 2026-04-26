# Update Rules

## Freeze Time

Start every case by writing:

- `cutoff_date`
- `reported_year`
- `old_forecast_window`
- `new_forecast_window`

Example:

- `cutoff_date = 2025-05-31`
- `reported_year = 2024A`
- `old_forecast_window = 2024E-2026E`
- `new_forecast_window = 2025E-2027E`

If the task uses delegated analysis, also write:

- `source_files`
- `analysis_roles`
- `evidence_store = evidence_store.jsonl`
- `pre_edit_output = forecast_basis.md`
- `workbook_structure_map = workbook_map.json`
- `phase_b_basis_contract = forecast_basis.json`
- `phase_b_instruction_contract = cell_instructions.json`
- `phase_b_patch_log = patch_log.json`
- `artifact_hashes = artifact_hashes.json`
- `phase_timers = {source_prep, engine_smoke_test, unicode_write_test, evidence, architecture, logic_review, merge, map_validation, basis_validation, completeness, instruction_compile, instruction_validation, patch, parity_audit, verification}`

Also record an expected time budget or checkpoint expectation for each phase. If a phase materially overruns, log the blocker and switch method instead of silently continuing to retry.

## Early Branching

Before full analysis or any workbook writeback, perform:

1. a workbook-engine smoke test
2. a Unicode-safe Chinese artifact write test

The engine smoke test must decide and log one branch:

- `spreadsheet_engine_path`
- `deterministic_writeback_path`

Do not defer this branch choice until after patching the candidate workbook.

## Parallel Pre-Edit Analysis

Split the work into four parallel evidence roles before any workbook edit:

1. annual report extractor
1. structured financial facts extractor (`Tushare`)
2. notes and knowledge-base synthesizer
3. workbook mapper
4. risk reviewer

After those four finish:

1. run `Forecast Architect`
2. run `Forecast Logic Reviewer`
3. merge their findings into `forecast_basis.md`

Enforce source roles throughout this phase:

1. `Tushare` for structured company-level and coarse segment financial facts
2. reference files supplied for the run, especially annual reports and research reports, for business context and mechanism evidence
3. local knowledge base
4. Alpha Pai

Do not let annual-report parsing replace `Tushare` as the deterministic source for:

- total revenue
- gross profit
- gross margin
- four expenses
- tax
- attributable net profit
- coarse disclosed segment facts

Query Alpha Pai on every run.
Do not let Alpha Pai outrank the first two layers for material judgments.
Emit and persist explicit recall checks for `reference_files`, `local_kb`, and `alpha_pai` before moving past source prep.
Do not stop at one company-level Alpha Pai query if segment thresholds imply narrower recalls.
If a segment has either `revenue_share > 30%` or `reported_year_growth > 40%`, add one Alpha Pai query for that segment keyword.
Restrict Alpha Pai recall carriers to meeting-note and seller-commentary types only: `roadShow`, `roadShow_ir`, `roadShow_us`, `comment`.
Do not let this workflow query Alpha Pai `report` or `foreign_report` carriers.
Do not let stale forecast lines from old research reports become the direct basis for the new run's forecast numbers.

After those roles finish, separate:

- 已知事实
- 解释与判断
- 预测假设
- 需人工复核的弱假设

Do not let the delegated path collapse into one mixed analysis blob.

Before Phase B, ensure:

- `workbook_map.json` exists
- `forecast_basis.json` exists
- `cell_instructions.json` exists

## Map Validation Gate

Before Phase B, validate `workbook_map.json` against the actual workbook snapshot.

At minimum confirm:

- `main_modeling_sheet` exists
- `main_modeling_sheet_index` matches
- `header_row` is correct
- `current_headers` match the workbook
- `row_registry` resolves
- `writable_driver_targets` resolve
- `formula_rows` and `display_rows` are both present where expected
- `summary_extension_status` is populated

If the map validation fails, stop. Do not let `Workbook Patch Executor` guess around a broken map.

## Basis Validation Gate

Before Phase B, validate `forecast_basis.json`.

At minimum confirm:

- the schema is valid
- each major segment has future-year coverage
- each major segment has revenue logic and margin logic
- each major segment has at least one kill condition
- weak assumptions and review flags are explicit
- no residual bridge is being used as unsupported business proof

If the basis validation fails, stop.

## Calibration Gate

For a workbook that has not yet been calibrated under this workflow, do not move straight from validated basis artifacts to real workbook patching.

First produce:

- a transmission-chain table
- a calibration test list
- a calibration result

The transmission-chain table should identify, for each major segment:

- the driver rows expected to move
- the segment output rows expected to respond
- the parent totals expected to change
- the profit-bridge rows expected to change

The calibration tests should use small controlled edits on representative drivers and verify that:

- the expected segment output row changes
- the expected parent total changes
- the expected profit-bridge row changes

If those checks fail, first classify the issues into auto-repairable structure defects and hard blockers. Repair the deterministic issues immediately, rerun calibration, and only stop if hard blockers remain.

## Forecast Architecture Gate

Before workbook patching, explicitly build future-year logic for each major segment.

For each major segment, the basis must include:

- revenue-driver form
- volume logic
- ASP logic
- share or competitiveness logic
- gross-margin logic
- evidence summary
- weak assumptions
- kill conditions

The basis must also include:

- selling expense logic
- admin expense logic
- R&D expense logic
- financial expense logic
- net-margin bridge

If the future-year section mostly restates actual-year bridging and does not explain `FY1-FY3`, the run is not ready for Phase B.

## Completeness Audit

Before patching the workbook, verify:

- every major segment is covered for every forecast year
- each major segment has both revenue logic and margin logic
- four-expense logic is present if it materially drives net profit
- weak assumptions are labeled rather than hidden
- no major line is carried forward without explanation

If the audit fails, do not proceed to Phase B.

## Instruction Compilation

Compile `workbook_map.json` and `forecast_basis.json` into `cell_instructions.json`.

The compiler must:

- resolve basis assumptions to writable driver cells or row anchors
- convert formula-driven rows into explicit formula instructions where needed
- keep display rows as verification targets by default
- only compile a display row into a write target when the workbook map explicitly marks it for rewrite
- fail when a required mapping is missing
- fail when a required assumption is missing
- fail when a write would target a non-writable row

Do not allow Phase B to begin unless `cell_instructions.json` passes validation.

The expected deterministic execution chain is:

- `validate_evidence_store`
- `validate_workbook_map`
- `validate_forecast_basis`
- `build_cell_instructions`
- `validate_cell_instructions`
- `Workbook Patch Executor`
- `validate_patch_log`
- `verify_contract_patch`

A minimal contract-driven runner may wrap the chain as:

- `run_contract_workflow(evidence_store, workbook_map, forecast_basis, workbook) -> artifact_hashes + cell_instructions + candidate + patch_log + verification_report`

## Rollforward and Phase B

Maintain the workbook's time logic.

- Convert the latest `E` year to actual
- Shift the remaining forecast years left by one slot conceptually
- Add one new far-year estimate
- Preserve formulas when they still represent the intended structure
- Copy format intentionally, not blindly
- Extend formula-driven and display rows into the new far-year column; do not leave the far-year blank just because the row is formula-based

Before running the full workbook update, prove that the chosen workbook engine can persist a minimal edit to disk.

Recommended smoke test:

- open an isolated candidate
- change one harmless header or note cell
- save
- reopen through a second read path
- confirm the change persisted

If this fails, do not proceed with the full workflow on that path.

If a `Workbook Patch Executor` is used for Phase B, it should:

- consume `workbook_map.json`
- consume `cell_instructions.json`
- update only approved writable instructions
- preserve formula-driven rows where instructions say not to hardcode
- write a candidate workbook
- emit `patch_log.json`
- run a parity audit before verification starts

The public workflow should only emit data artifacts during a normal run. Do not generate runtime executable code such as `.py`, `.ps1`, `.bat`, `.cmd`, or `.sh` inside the run output directory.

The executor must not:

- reinterpret source materials
- create new forecast assumptions
- silently expand scope beyond the accepted instructions
- skip structural completeness checks

The executor must also preserve prediction-basis traceability outputs required by the workflow, including:

- workbook `Forecast Basis` sheet content
- links between key rows and basis references when the workbook style supports it

## Chinese Output Requirement

User-facing explanatory outputs should default to Chinese unless the user explicitly asks for another language.

This applies to:

- `forecast_basis.md`
- `verification-summary.md`
- `run-log.md`
- workbook `Forecast Basis` sheet text
- assumptions or review notes added for the user

The final user-facing response must explicitly surface the basis deliverables instead of assuming the user will find them inside the run directory.

At minimum, name or link:

- `forecast_basis.md`
- `forecast_basis.json`
- workbook `Forecast Basis` sheet

## Encoding Safety

Treat Unicode handling as a data-integrity issue, not a cosmetic issue.

- If newly written workbook text shows `?`, `??`, or obviously garbled Chinese, treat the run as failed.
- Do not write Chinese sheet names, comments, or basis-sheet text through inline shell snippets unless Unicode safety has been verified.
- Prefer UTF-8 script files on disk over shell-piped inline scripts for markdown, JSON, or workbook-writing steps.
- Prefer ASCII-safe temporary filenames when COM or shell handling of Chinese paths is unstable.
- Verify representative written cells after save by reopening the workbook and checking their text values.
- Do not treat terminal rendering of Chinese as sufficient verification of file integrity.

## Spreadsheet-Aware Review

Before handoff, inspect at least these relationships:

- segment rows sum to their parent total
- gross profit equals revenue times gross margin where that is the intended structure
- design revenue plus distribution revenue ties to total revenue
- profit rows tie through tax and minority interest logic
- summary sheets mirror the source sheets correctly
- any new far-year formulas copied as intended without off-by-one range errors
- every important row populated in the adjacent forecast column is intentionally handled in the new far-year column

Verification discipline:

- identify the main modeling sheet explicitly
- do not verify by workbook tab order once review sheets have been added
- audit both driver sections and summary-display sections
- run parity checks such as:
  - `previous forecast column populated / new forecast column blank`
  - `detail section populated / summary section blank`
- run verification only after the candidate file is fully finalized
- require candidate hash to match the patch log output hash

Verification should be dual-track whenever possible:

- spreadsheet-engine recalculation
- deterministic verification from approved basis, approved instructions, and formula or tie-out logic

Do not wait for spreadsheet-engine failure before preparing deterministic verification.

## Prediction Basis Traceability

Do not treat the forecast basis as an internal implementation detail.

The workflow must produce a reviewer-friendly basis package that explains, at minimum:

- each major segment's revenue logic
- each major segment's margin logic
- key four-expense logic
- the bridge from segment assumptions to consolidated revenue and profit

If the workbook was patched but the forecast basis is not surfaced to the reviewer, the run is incomplete.
