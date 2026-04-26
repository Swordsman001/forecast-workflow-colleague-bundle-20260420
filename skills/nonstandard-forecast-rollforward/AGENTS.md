# Forecast Rollforward Agents

This skill defines four bounded evidence agents for the pre-edit phase, one dedicated forecasting agent, one dedicated forecast logic review agent, and one bounded execution agent for Phase B.

The controller should:

1. freeze the run frame and start phase timing
2. run an engine smoke test and a Unicode write test
3. dispatch the four evidence agents in parallel
4. wait for all four
5. hand their outputs to `Forecast Architect`
6. hand the architecture to `Forecast Logic Reviewer`
7. merge everything into `forecast_basis.md`
8. materialize or refresh `workbook_map.json`
9. convert the accepted basis into `forecast_basis.json`
10. validate `workbook_map.json`
11. validate `forecast_basis.json`
12. run a completeness audit
13. compile `cell_instructions.json`
14. validate `cell_instructions.json`
15. return the basis for review only if the user explicitly asked for an analysis-only checkpoint
16. only begin workbook editing after the contracts are coherent and accepted
17. hand Phase B to `Workbook Patch Executor`
18. run post-patch parity audit and then verification in strict sequence

## Agents

- [Annual Report Extractor](agents/annual-report-extractor.md)
- [Notes and KB Synthesizer](agents/notes-kb-synthesizer.md)
- [Workbook Mapper](agents/workbook-mapper.md)
- [Risk Reviewer](agents/risk-reviewer.md)
- [Forecast Architect](agents/forecast-architect.md)
- [Forecast Logic Reviewer](agents/forecast-logic-reviewer.md)
- [Workbook Patch Executor](agents/workbook-patch-executor.md)

## Shared Rules

- Keep scopes disjoint.
- Do not let one agent do another agent's job.
- Do not edit the workbook in the pre-edit phase.
- Do not let the Phase B executor reinterpret evidence or re-run forecast judgment.
- Do not mix facts, interpretation, and forecast assumptions in one undifferentiated blob.
- Do not patch the workbook before segment-level future logic is explicit.
- Enforce evidence priority in analysis and forecasting: reference files first, local knowledge base second, Alpha Pai last.
- All user-facing explanatory outputs should default to Chinese unless the user explicitly asks otherwise.
- All Chinese markdown and JSON artifacts should be written through UTF-8 file-based paths.

Every merged basis should be easy to separate into:

- 已知事实
- 解释与判断
- 预测假设
- 需人工复核的弱假设

## Merge Output

The merged `forecast_basis.md` should contain:

- company
- source files
- cutoff date
- reported year
- old forecast window
- target forecast window
- 已知事实
- 解释与判断
- 预测假设
- 需人工复核的弱假设
- risk checklist
- completeness audit result

The normalized `forecast_basis.json` should contain at least:

- approved facts
- approved assumptions
- segment assumption cards
- target sheets
- writable driver references
- non-writable formula rows
- roll-forward instructions
- review flags to preserve
- completeness audit status
- output artifact targets including `cell_instructions.json` and `patch_log.json`

The `workbook_map.json` should contain at least:

- workbook path or identifier
- main modeling sheet
- main modeling sheet index
- header row
- a row registry
- writable driver targets
- formula-driven rows
- display-only rows
- roll-forward pattern
- current workbook snapshot relevant to this run
- validation hints for Phase B

The `cell_instructions.json` should contain at least:

- instruction identifiers
- resolved sheet and cell targets
- row identifiers
- year
- write type
- basis reference
- formula preservation state
- review flags
- allowed write status

## Stop Rule

If this agent framework is used, do not edit the workbook until:

- the merged basis is coherent
- `workbook_map.json` passes validation
- `forecast_basis.json` passes validation
- `cell_instructions.json` passes validation
- the completeness audit passes
- the basis has been reviewed or explicitly accepted when a checkpoint is requested
