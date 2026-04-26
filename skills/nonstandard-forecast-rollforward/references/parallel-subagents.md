# Parallel Subagents

Use this pattern as the default pre-edit execution mode for every run under this workflow.

The concrete agent contracts live in [../AGENTS.md](../AGENTS.md).

## Goal

Produce a reviewable Chinese `forecast_basis.md` before any workbook edit happens.

The controller should first merge four bounded evidence-agent outputs:

- annual report extractor
- structured financial facts extractor
- notes and knowledge-base synthesizer
- workbook mapper
- risk reviewer

Wait for all four before merging.

Evidence priority inside this phase is fixed:

1. reference files supplied for the run, especially annual reports and research reports
2. local knowledge base
3. Alpha Pai

Alpha Pai recall is mandatory for every run.
It remains third-priority evidence and cannot override usable higher-priority evidence.
This phase must record explicit checks for:

- `reference_files_recalled`
- `local_kb_recalled`
- `alpha_pai_recalled`
- `alpha_pai_has_content`
- `alpha_pai_call_count`

Alpha Pai should not remain a single broad company query when the workbook already shows clear segment concentration or acceleration.

Trigger an additional Alpha Pai query for each segment whose:

- revenue share exceeds `30%`, or
- reported-year revenue growth exceeds `40%`

Use `company + normalized segment keyword` as the query form.

Restrict Alpha Pai recall types to:

- `roadShow`
- `roadShow_ir`
- `roadShow_us`
- `comment`

Do not query Alpha Pai `report` or `foreign_report` carriers inside this workflow.

Then hand the merged evidence to:

1. `Forecast Architect`
2. `Forecast Logic Reviewer`

Phase B must then be handed to `Workbook Patch Executor` only after:

- the basis is accepted
- the basis is normalized into `forecast_basis.json`
- `workbook_map.json` passes validation
- `forecast_basis.json` passes validation
- `cell_instructions.json` passes validation
- the completeness audit passes

## Required Role Boundaries

### 1. Annual Report Extractor

Scope:

- latest annual report only

Output:

- reference findings only
- page references
- file references

Must not:

- act as the structured financial anchor
- output deterministic `reported_facts`
- use meeting notes
- use the workbook

### 2. Structured Financial Facts Extractor

Scope:

- `Tushare` only

Output:

- `financial_facts.json`
- company-level structured facts
- coarse segment disclosure when available
- source endpoint / period trace

Must not:

- invent fine-grained splits that the workbook requires
- override workbook structure
- rely on annual-report parsing for deterministic facts
### 3. Notes and Knowledge-Base Synthesizer

Scope:

- research notes
- earnings-call notes
- local knowledge base
- Alpha Pai as mandatory third-priority recall

Output:

- only statements relevant to segment bridge logic and `FY1-FY3` drivers
- each point tagged as:
  - `fact`
  - `management_guidance`
  - `analyst_prior_logic`
  - `low_confidence_inference`

Must not:

- touch the workbook
- restate annual-report totals unless needed to resolve a contradiction

### 4. Workbook Mapper

Scope:

- forecast workbook only

Output:

- main modeling sheet
- forecast window
- driver rows
- formula rows
- display-only summary rows
- roll-forward pattern
- explanation of how revenue and margins are decomposed
- sheet identity and header metadata needed for Phase B validation
- row registry information needed for instruction compilation

Must not:

- change any cells
- propose forecast assumptions

### 5. Risk Reviewer

Scope:

- likely failure points in the update task

Output:

- checklist only

Must focus on:

- formula breakage
- wrong sheet targeting
- summary rows not extending
- post-cutoff leakage
- unsupported fine-split assumptions
- engine compatibility risk
- Unicode write risk

Must not:

- invent new evidence
- propose new numbers

### 6. Forecast Architect

Scope:

- annual report findings
- notes and KB findings
- workbook map
- mandatory Alpha Pai recall trace, even when no usable Alpha Pai content is ultimately used

Output:

- segment-by-segment future forecast logic
- explicit revenue-driver form
- volume logic
- ASP logic
- share or competitiveness logic
- gross-margin logic
- four-expense logic
- weak assumptions
- kill conditions

Must not:

- patch the workbook
- skip major segments
- reduce the future forecast to slogans or linear extrapolation without explanation

### 7. Forecast Logic Reviewer

Scope:

- forecast architecture
- supporting evidence

Output:

- logic pass or fail
- missing mechanism links
- residual bridge warnings
- missing kill conditions
- future-year coverage warnings
- must-fix items before Phase B

Must not:

- create new numbers
- patch the workbook
- quietly repair weak logic by adding assumptions

## Merge Contract

After evidence roles, forecast architect, and forecast logic reviewer finish, merge to `forecast_basis.md` with four sections:

- `已知事实`
- `解释与判断`
- `预测假设`
- `需人工复核的弱假设`

The merged file should also include:

- source file list
- cutoff date
- reported year
- old forecast window
- target forecast window
- risk checklist
- forecast logic review result
- completeness audit result

## Stop Rule

If this parallel path is used, do not edit the workbook until:

- `forecast_basis.md` has been reviewed or explicitly accepted when a checkpoint is requested
- `workbook_map.json` passes validation
- `forecast_basis.json` passes validation
- `cell_instructions.json` passes validation
- the completeness audit passes
