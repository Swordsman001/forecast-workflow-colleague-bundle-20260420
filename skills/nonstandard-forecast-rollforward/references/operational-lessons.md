# Operational Lessons

These are hard lessons from real runs of this workflow.

## 1. Time Control

- Do not begin with a long open-ended exploration loop.
- Freeze the run frame first: source files, cutoff, target window, output contract, and execution branch.
- Record phase timing from the start rather than reconstructing it afterward.
- Add checkpoints early:
  - engine smoke test checkpoint
  - Unicode write checkpoint
  - fact extraction checkpoint
  - forecast architecture checkpoint
  - forecast logic review checkpoint
  - workbook compatibility checkpoint
  - instruction compilation checkpoint
  - recalculation checkpoint
  - output readability checkpoint
- If a path is failing, stop early and switch methods. Do not spend a long time repeatedly probing the same failure mode.
- Rework that pushes a run to twenty minutes without a clear blocker log is a workflow failure.

## 2. Contract Discipline

- A rule in prose is not enough.
- If a contract matters, it must have:
  - a schema
  - a validator
  - a compiler or linter where relevant
- `workbook_map.json` should be executable.
- `forecast_basis.json` should be auditable.
- `cell_instructions.json` should be deterministic.
- If a validator fails, stop. Do not let the next phase guess around it.

## 3. Excel Process Safety

- Hidden background automation is preferred.
- User-visible Excel is only for explicit manual review or when the user asks to watch the edits.
- Never operate inside the user's existing Excel session by default.
- Use a dedicated Excel instance when possible.
- Close only the workbook and Excel instance created for the task.
- Never use `taskkill /IM EXCEL.EXE /F` or equivalent broad cleanup in this workflow.
- If Excel automation becomes stuck and isolation is uncertain, stop and tell the user rather than risking their open workbooks.

## 4. Workbook Engine Choice

- Some workbooks survive `openpyxl` round-tripping; some do not.
- Run a small compatibility smoke test before committing to the engine.
- If `openpyxl` breaks Excel compatibility, do not use it for the final artifact.
- In that case, use Excel automation, LibreOffice, or a safer workbook-preserving path.
- Decide the engine branch early and record it in the run log. Do not discover the branch only after the workbook patch is already done.

## 5. Unicode and Chinese Text Safety

- `?` replacing Chinese text means the text was corrupted before or during write.
- This is not fixed by installing fonts.
- Corrupted text requires a Unicode-safe write path.

Required practice:

- keep markdown and JSON writing logic in UTF-8 script files on disk
- avoid piping Chinese workbook text through inline shell snippets
- prefer ASCII-safe temporary artifact filenames if path encoding is unstable
- verify representative text cells, comments, sheet names, and markdown files after save
- treat a failed Unicode round-trip as a run failure, not a cosmetic issue

## 6. Verification Scope

- Do not verify by workbook tab order.
- Explicitly identify the main modeling sheet and verify that sheet by name or by pre-recorded identity.
- If a `Forecast Basis` sheet is added, expect sheet order to change.
- New-year verification must cover:
  - driver rows
  - derived rows
  - summary-display rows
  - comments or note cells added for traceability
- Run verification only after the candidate file is finalized.
- Verification should check:
  - instruction coverage
  - workbook structural integrity
  - numeric tie-out

## 7. Candidate File Hygiene

- Copied workbooks may inherit `ReadOnly`.
- Before deleting or overwriting a prior candidate, normalize file attributes first.
- If a stale candidate is locked or unsafe to reuse, switch to a fresh output path rather than fighting the same file handle repeatedly.
- Prefer temporary files plus atomic rename over writing and reading the same final target concurrently.
- Record output hashes in patch logs and verification outputs.

## 8. Forecast-First Discipline

- Do not let the desire to finish the workbook outrun the depth of the forecast logic.
- Build segment-level future logic before patching cells.
- For each major segment, explain revenue drivers, competitiveness, and margin logic.
- Do not treat a partially forecast model as complete because consolidated outputs exist.
- If only some segments are deeply modeled and others are silently carried forward, stop and fix the basis first.

## 9. Instruction-Driven Phase B

- Patch executors should not consume raw business judgment.
- Compile accepted logic into `cell_instructions.json`.
- Make Phase B instruction-driven, not narrative-driven.
- Ban fallback sheet selection, default share guesses, and hardcoded row repair inside the executor.

## 10. Incremental Reruns

- Failure in Phase B should not require a full rerun of evidence extraction and forecast reasoning.
- Prefer artifact DAGs with upstream hashes so patch and verification can rerun independently.
