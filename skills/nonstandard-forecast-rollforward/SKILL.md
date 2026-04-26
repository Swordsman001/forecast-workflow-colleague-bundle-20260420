---
name: nonstandard-forecast-rollforward
description: Use when updating a company-specific nonstandard earnings forecast workbook from a newly released annual report, management meeting notes, local knowledge sources, and market evidence while preserving future years as estimates and producing an auditable candidate workbook.
---

# Nonstandard Forecast Rollforward

## Overview

Use this skill for nonstandard sell-side style models where workbook layout, line items, formulas, and split logic are company-specific.

The core principle is:

- Excel remains the final presentation layer, not the primary reasoning object.
- The main reasoning artifacts should be:
  - `financial_facts.json`
  - `segment_mapping.json`
  - `reconciliation_audit.json`
  - `workbook_map.json`
  - `forecast_basis.md`
  - `forecast_basis.json`
  - `cell_instructions.json`
- Forecast judgment must happen before workbook patching.
- Patch execution must be deterministic and instruction-driven.

Do not reduce this task to a fixed script. Deterministic scripts are allowed for file I/O, schema validation, instruction compilation, patch execution, parity audit, verification, hashing, and logging. They are not allowed to replace company understanding, segment bridge logic, or future forecast judgment.

The preferred deterministic chain is now explicit:

- collect and validate `financial_facts.json`
- validate `evidence_store.jsonl`
- validate `workbook_map.json`
- validate `forecast_basis.json`
- compile `cell_instructions.json`
- validate `cell_instructions.json`
- execute patch from instructions
- validate `patch_log.json`
- verify candidate workbook against instruction lineage

When the user provides the annual report, use it as reference evidence for business analysis and forecasting. Structured company-level financial facts should come from `Tushare`, not from annual-report parsing.

This skill should follow spreadsheet-grade behavior:

- be formula-aware rather than value-only
- preserve workbook formatting and style conventions
- recalculate formulas before handoff when possible
- review the rendered workbook or recalculated workbook before claiming the result is usable

## When To Use

Use this skill when all of the following are true:

- The input is a real Excel model with nonstandard rows, formulas, or segment splits.
- The latest annual report has been released and the reported year must be converted from `E` to actual.
- The forecast window must roll forward by one year, such as `2024E-2026E` to `2025E-2027E`.
- Official disclosure is too coarse, but meeting notes, research reports, local KB, or Alpha Pai can justify finer downstream splits.

Do not use this skill for:

- Standardized template models with fixed schemas.
- Pure data extraction with no forecast judgment.
- Cases where the user only wants a summary of the annual report.

## Inputs

Expected inputs:

- Historical model workbook (`.xlsx`)
- `Tushare` access for structured financial anchors
- Latest annual report (`.pdf`)
- Management meeting notes or transcript (`.docx`, `.txt`, or `.md`)
- Optional helper tables extracted from the annual report
- Optional local KB results
- Alpha Pai recall trace for every run

## Evidence Priority

In the analysis and forecasting phases, use evidence in this order:

1. `Tushare` for structured financial facts
2. reference files supplied for the run, especially annual reports and research reports, for business context
3. local knowledge base
4. Alpha Pai

Apply this as a hard priority rule:

- `Tushare` is the default primary basis for structured facts
- annual report and research report are the default primary basis for forecast framing and mechanism evidence
- local knowledge base may supplement mechanism chains, historical context, and prior analyst logic
- Alpha Pai must be queried on every run as a mandatory cross-check layer
- Alpha Pai remains third-priority evidence even when it is mandatorily recalled
- Alpha Pai must not override annual-report facts, explicit research-report conclusions, or higher-priority local knowledge without an explicit contradiction note
- if a material forecast point relies on Alpha Pai, mark it explicitly in the basis as lower-priority support
- do not use one broad company-only Alpha Pai recall as the sole query shape when segment thresholds indicate more targeted recalls are needed
- trigger additional Alpha Pai recalls by business keyword whenever a segment has either `revenue_share > 30%` or `reported_year_growth > 40%`
- for those triggered recalls, query the company plus the normalized business keyword, such as `豪威集团 手机CIS`
- Alpha Pai recall types must be restricted to meeting-note and seller-commentary carriers only: `roadShow`, `roadShow_ir`, `roadShow_us`, and `comment`
- do not recall `report`, `foreign_report`, or other research-report carriers from Alpha Pai in this workflow
- research-report sentences that contain prior analyst forecast numbers or explicit future-year targets should be treated as `stale_forecast` support and must not directly justify the new run's forecast values
- research reports may still support historical context or mechanism explanation when the retained sentence is not itself a stale forecast line

Always identify the information cutoff before forecasting. The cutoff is usually the annual report release date plus any documents the user explicitly allows. Do not use realized information after the cutoff to fill forecast years.

Example:

- Annual report released on `2025-04-16`
- Allowed information through `2025-05-31`
- `2024E` becomes actual `2024A`
- `2025E` stays an estimate, even if `2026` or later facts are known today

`2025Q1` or other disclosed interim results before the cutoff may inform `2025E`, but they do not turn `2025E` into actual.

## Core Workflow

### 1. Freeze the run frame and start timing

Before touching the workbook, state:

- company
- source files
- information cutoff
- latest reported full year
- current forecast window
- target forecast window after rollforward

Also start a timed run log with at least these phases:

- source prep
- engine smoke test
- Unicode write test
- pre-edit evidence collection
- forecast architecture
- forecast logic review
- basis merge
- map validation
- basis validation
- instruction compilation
- instruction validation
- workbook patch
- post-patch parity audit
- verification

Before any heavy analysis or writeback, run and log two early checks:

- a workbook-engine smoke test
- a Unicode-safe artifact-write test for Chinese output

The smoke test must decide the execution branch up front:

- `engine_path = spreadsheet-engine`
- `engine_path = deterministic-writeback-plus-deterministic-verification`

Do not discover engine incompatibility only after the candidate workbook is already written.

### 2. Run a bounded pre-edit evidence phase

Dispatch these four evidence roles in parallel for every run:

- `Annual Report Extractor`
- `Notes and KB Synthesizer`
- `Workbook Mapper`
- `Risk Reviewer`

Wait for all four before proceeding.

Role boundaries live in [AGENTS.md](AGENTS.md) and [references/parallel-subagents.md](references/parallel-subagents.md).

Within this phase, the controller should enforce the source priority:

- reference files first
- local knowledge base second
- Alpha Pai last
- but Alpha Pai recall itself is mandatory and must be logged even when it returns no usable content
- source prep must emit explicit recall checks for `reference_files`, `local_kb`, and `alpha_pai`
- source prep must also emit `alpha_pai_call_count`, the query plan, and per-query success or failure details

### 3. Run forecast architecture before any workbook edit

After the parallel evidence phase returns, hand the evidence to `Forecast Architect`.

This role is mandatory for material forecast work. It must not patch the workbook. It must explain how the future forecast is actually built.

For each major segment, it must explicitly produce:

- business definition
- revenue driver form, such as `volume x ASP` or `market size x share x ASP`
- volume logic
- ASP logic
- share or competitiveness logic
- gross-margin logic
- kill conditions
- key evidence and source references
- weak assumptions

Segment naming must come from the current workbook and current disclosure:

- do not silently reuse prior-case segment labels
- keep the segment labels that the current workbook already uses unless there is a clear current-case reason to normalize them
- only use labels such as `手机CIS` or `汽车CIS` when the current workbook and current evidence explicitly support them
- reusing an old-case label is a workflow failure

The architect must also explain:

- consolidated four-expense logic
- tax, minority interest, and non-recurring bridge where relevant
- why the old model split is still the right split, if retained

The architect must receive and preserve the Alpha Pai recall trace for every run.
If the architect uses Alpha Pai materially, it must still say why reference files and local KB were not sufficient and must label the resulting support as lower-priority.

### 4. Run forecast logic review before basis merge

After `Forecast Architect`, run `Forecast Logic Reviewer`.

This reviewer does not add numbers. It only checks whether the forecast logic is complete enough to deserve workbook patching.

It must also verify that the run contains explicit Alpha Pai recall checks from:

- source prep
- forecast architecture
- logic review itself

It must hard-fail if:

- a major segment has only directionally vague language
- a major segment lacks a mechanism chain from business driver to revenue and margin
- a residual bridge is being used as proof of durable competitiveness
- a major segment has no kill condition
- the basis explains the reported year in depth but leaves `FY1-FY3` under-explained

Apply materiality before failing smooth future trajectories:

- if a segment has `revenue_share > 30%` or `reported_year_growth > 40%`, it must show year-specific tempo
- if a segment is low-share and low-growth, controlled linear extrapolation is allowed when the stability rationale is explicit

### 5. Merge to Chinese basis artifacts before any workbook change

After evidence collection, forecast architecture, and forecast logic review are complete, materialize:

- `financial_facts.json`
- `segment_mapping.json`
- `reconciliation_audit.json`
- `workbook_map.json`
- `forecast_basis.md`
- `forecast_basis.json`

All user-facing narrative artifacts must default to Chinese, including:

- `forecast_basis.md`
- `run-log.md`
- `verification-summary.md`
- workbook `Forecast Basis` sheet content

All Chinese explanatory artifacts must be written through UTF-8 file-based paths.

Do not use shell here-strings, shell inline snippets, or terminal echo as the primary write path for:

- `forecast_basis.md`
- `forecast_basis.json` explanatory text
- `run-log.md`
- `verification-summary.md`
- workbook `Forecast Basis` sheet notes or comments

Keep machine-readable keys in English if useful, but the explanatory text must be Chinese by default unless the user explicitly asks otherwise.

`forecast_basis.md` must explicitly separate:

`Forecast Basis` must be rendered from structured evidence rows, not raw text blobs:

- every fact and every material forecast judgment must carry structured `evidence_items`
- each `evidence_item` must contain a short claim, a precise source label, and a source tier
- markdown output and workbook-sheet output must be rendered from the same structured contract
- if a basis item can only be expressed as a pasted long paragraph, the basis is not ready
- facts should default to annual-report evidence unless a contradiction note explicitly requires another primary source
- duplicated evidence rows should be collapsed deterministically; do not repeat the same source and same claim across one basis card

- 已知事实
- 解释与判断
- 预测假设
- 需人工复核的弱假设

Immediately after writing these artifacts, reopen representative files or cells with a Unicode-safe reader and confirm Chinese text integrity before moving on.

### 6. Validate contracts before workbook patching

Do not enter workbook patching until all of the following pass:

- `workbook_map.json` validation
- `forecast_basis.json` validation
- completeness audit

`forecast_basis.json` validation must reject:

- segment labels borrowed from a prior unrelated case instead of the current workbook
- facts without structured `evidence_items`
- major segment cards without structured `evidence_items`
- future-year logic that only carries raw long text instead of concise evidence rows

`workbook_map.json` must be an executable structure contract, not a loose note dump.

`forecast_basis.json` must be an assumption contract, not only a narrative summary.

If either contract fails validation, stop and fix the contract first. Do not let the patch executor improvise.

### 6.5. Run a calibration gate before first real workbook patch

For a company workbook that has not yet been calibrated under this workflow, do not move directly from basis validation to workbook patching.

First produce a lightweight calibration package:

- a transmission-chain table for major segments and major consolidated outputs
- a list of critical driver rows
- a list of expected downstream output rows
- a small set of calibration tests

The transmission-chain table should answer:

- which driver row is expected to control which segment output row
- which segment output row is expected to roll into which parent total
- which total is expected to affect which gross-profit, opex, and profit-bridge rows

The calibration tests should make small controlled edits to representative drivers and confirm that the expected downstream rows move in the expected direction.

If calibration surfaces deterministic structure defects, repair them automatically and rerun calibration before stopping.

Examples of repairable defects include:

- summary formulas that did not extend into the new forecast columns
- display rows that point to the wrong source row when the intended row can be inferred safely
- formula-copy gaps that can be fixed without reopening forecast judgment

Only treat calibration as a hard stop when unresolved blockers remain after repair.

### 7. Compile contracts into `cell_instructions.json`

Before workbook patching, compile:

- `workbook_map.json`
- `forecast_basis.json`

into:

- `cell_instructions.json`

This compilation step must be deterministic.

The compiler must:

- map approved assumptions to approved writable cells or row anchors
- map formula-derived rows to formula instructions
- keep display rows as verification targets by default
- allow explicitly flagged display rows to compile into deterministic formula writes when the map says they must be rebuilt
- reject missing values, missing write targets, and ambiguous mappings

Do not let `Workbook Patch Executor` consume business logic directly from the basis.

### 8. Patch the workbook only from compiled instructions

After the basis is coherent, validated, and compiled, hand workbook patching to `Workbook Patch Executor`.

Workbook patching should consume:

- `workbook_map.json`
- `cell_instructions.json`

Workbook patching must not reopen judgment.

The patch role must:

- validate `workbook_map.json` against the live workbook snapshot
- validate `cell_instructions.json`
- write the candidate workbook strictly from approved instructions
- emit `patch_log.json`
- preserve formula-driven rows unless the instructions explicitly authorize replacement
- run an immediate post-patch parity audit before any verification starts
- preserve or populate workbook-level basis traceability outputs required by the workflow

The immediate post-patch parity audit must cover at least:

- previous populated forecast column versus new forecast column blanks
- driver sections
- formula-derived sections
- summary-display sections
- the new far-year column extending formula and display rows, not only hardcoded numeric rows

Do not treat a run as patched successfully if only bottom-line formulas work while summary rows remain unextended.

### 9. Verification must be dual-track and strictly serial

Run both whenever possible:

- spreadsheet-engine verification
- deterministic verification from approved basis, approved instructions, and tie-out logic

Verification must start only after:

- the candidate workbook has been fully written
- the post-patch parity audit has passed
- the final candidate file has been atomically committed to its final path
- the final candidate hash matches the patch log output hash

Do not run patching and verification in parallel against the same target workbook or the same final artifact path.

### 10. Timing and fail-fast discipline

Do not allow long, silent drift.

At minimum:

- record elapsed time per phase in the run log
- note the blocker when a phase exceeds expectations
- switch methods instead of probing the same failing path repeatedly

Twenty minutes of repeated rework is a workflow failure, not just a slow run.

### 11. No runtime code generation in public workflow

The reusable public workflow may generate run artifacts, but it must not generate executable code during a normal run.

Allowed runtime artifacts are data or review outputs such as:

- `json`
- `jsonl`
- `md`
- `txt`
- `xlsx`

The public workflow must reject or flag any runtime-generated executable artifact such as:

- `.py`
- `.ps1`
- `.bat`
- `.cmd`
- `.sh`

If a temporary helper is required, keep it as a non-executable data artifact inside the run directory and record it in the run log.

## Forecasting Rules

### 1. Actualize and decompose the reported year

Convert the latest reported year from forecast to actual:

- update revenue, gross profit, gross margin, opex, tax, net profit, and official segment figures
- use the annual report first
- supplement missing detail with helper tables, meeting notes, or other allowed evidence

Do not stop at replacing top-line totals.

The reported year must become a coherent segment-level actual base:

- map official disclosure into workbook buckets
- bridge coarse disclosure into the model's finer rows
- revise segment margins where evidence supports it
- revise the expense and profit bridge so the reported year becomes the new base year

### 2. Forecast future years from segment drivers, not from convenience

The default forecasting chain is:

1. forecast segment revenue drivers
2. build segment revenue
3. forecast segment gross margins
4. aggregate to consolidated gross profit and gross margin
5. forecast selling, admin, R&D, and financial expense behavior
6. bridge tax, minority interest, and non-recurring items where relevant
7. arrive at attributable net profit and net margin

Preferred revenue-driver hierarchy:

- `volume x ASP`
- `shipment x content`
- `market size x share x ASP`
- `customer program ramp x price curve`
- only if the model truly has no better driver layer: a documented growth-rate bridge

Do not default to shallow linear extrapolation.

### 3. Do not patch a partial forecast

For each major segment and forecast year, be able to answer:

- what changes in volume
- what changes in ASP or content
- what changes in share or competitiveness
- what changes in gross margin
- which evidence supports the view
- what makes the estimate fragile

If only some segments are properly forecast and the rest are implicit carry-forwards without disclosure, the run is incomplete.

## Output Contract

This workflow defaults to a single end-to-end completion point.

### Optional analysis-only checkpoint

- `forecast_basis.md` in Chinese
- `forecast_basis.json`
- `workbook_map.json`
- calibration artifacts when the workbook is not yet calibrated
- a risk checklist if the parallel risk-review role was used
- a timed run log for completed phases
- no workbook edits yet
- only valid when the user explicitly asks to stop for review before patching

### Default full workbook update

- a candidate workbook, never overwriting the original file
- `workbook_map.json`
- `forecast_basis.json`
- `cell_instructions.json`
- `patch_log.json`
- a user-facing prediction-basis deliverable that is explicitly linked in the final answer
- a workbook `Forecast Basis` sheet
- a Markdown changelog
- a machine-readable changelog or evidence file
- unresolved review items
- formula recalculation status
- `verification-summary.md` in Chinese
- `run-log.md` with per-phase timing

The prediction-basis deliverable is mandatory.

At minimum, it must make it easy for a reviewer to trace:

- each major segment forecast
- each major segment margin view
- four-expense assumptions when they materially affect profit
- the bridge from segment assumptions to consolidated revenue, gross profit, and net profit

The final user-facing response must explicitly link or name:

- `forecast_basis.md`
- `forecast_basis.json`
- the workbook `Forecast Basis` sheet

Do not treat a run as complete if the model was updated but the reviewer cannot quickly find the forecast basis.

If the user asks for a review checkpoint first, stop after the optional analysis-only checkpoint and wait for approval before workbook patching.

## Guardrails

- Do not treat code as the forecasting brain.
- Do not overwrite the user's original workbook.
- Do not use information after the cutoff to backfill forecast years.
- Do not silently replace a detailed split with a new one that lacks evidence.
- Do not hide weak assumptions; mark them.
- Do not confuse quarterly disclosed data with full-year actualization.
- Do not search the web for annual-report fields that should have been read from the supplied annual report or helper tables.
- Do not leave a new far-year column with a visibly inconsistent format.
- Do not accept a run where the far-year column is only partially extended through display sections.
- Do not output forecast numbers without auditable contracts.
- Do not hardcode outputs when an existing formula structure can still express the logic.
- Do not update a visible summary row first and only later wonder which driver rows should have moved.
- Do not ignore comments, note cells, or formatting cues that indicate how the original analyst used the workbook.
- Do not present `FY1-FY3` logic as a few loose bullet points that mostly restate actual-year bridging.
- Do not claim a future forecast is well grounded unless you can explain segment revenue drivers, segment margin logic, and four-expense logic.
- Do not let user-facing forecast explanation default to English unless the user asks for English.
- Do not move into workbook patching if the completeness audit failed.
- Do not move into workbook patching if `workbook_map.json` or `forecast_basis.json` failed validation.
- Do not move into workbook patching on a first-time company workbook if the calibration gate failed after auto-repair and rerun.
- Do not let the patch executor read business judgment directly from `forecast_basis.json`.
- Do not claim the run is reviewable if the forecast basis was not surfaced as a user-facing deliverable.
- Do not use broad process-kill commands against Excel.
- Do not close or interfere with user-open Excel sessions.
- Do not send non-ASCII workbook content through unsafe shell text paths when a UTF-8 file-based path is available.
- Do not discover workbook-engine incompatibility only after the full patch path has already run.
- Do not run verification against a workbook that is still being patched or rewritten.

## References

- [AGENTS.md](AGENTS.md)
- [references/update-rules.md](references/update-rules.md)
- [references/parallel-subagents.md](references/parallel-subagents.md)
- [references/operational-lessons.md](references/operational-lessons.md)
- [references/workbook-map.md](references/workbook-map.md)
- [references/forecast-basis-json.md](references/forecast-basis-json.md)
- [references/cell-instructions.md](references/cell-instructions.md)
- [references/calibration.md](references/calibration.md)
- [schemas/workbook_map.schema.json](schemas/workbook_map.schema.json)
- [schemas/forecast_basis.schema.json](schemas/forecast_basis.schema.json)
- [schemas/evidence_store.schema.json](schemas/evidence_store.schema.json)
- [schemas/artifact_hashes.schema.json](schemas/artifact_hashes.schema.json)
- [schemas/cell_instructions.schema.json](schemas/cell_instructions.schema.json)
- [schemas/patch_log.schema.json](schemas/patch_log.schema.json)
- [references/forecast-basis-sheet.md](references/forecast-basis-sheet.md)
- [references/spreadsheet-modeling.md](references/spreadsheet-modeling.md)
