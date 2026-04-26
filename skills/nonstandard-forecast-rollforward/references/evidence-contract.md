# Evidence Contract

Every material workbook change should be traceable.

Structured financial anchors should come from `Tushare`, not from annual-report parsing.

The annual report remains a reference-evidence source for business analysis, mechanism chains, and forecast reasoning.

Minimum fields:

- `sheet`
- `row_label`
- `year`
- `before`
- `after`
- `change_type`
- `evidence`
- `rationale`
- `confidence`
- `review_flag`

For the workbook-level `预测依据` / `Forecast Basis` sheet, minimum fields are:

- `sheet`
- `target_row`
- `year`
- `value`
- `basis_type`
- `driver`
- `evidence_summary`
- `source_ref`
- `confidence`
- `review_flag`
- `model_role`
- `affected_by`

Recommended `change_type` values:

- `actualized_from_annual_report`
- `rolled_forward`
- `bridged_from_meeting_notes`
- `supported_by_local_kb`
- `supported_by_alpha_pai`
- `retained_prior_logic`
- `manual_review_required`

Recommended `basis_type` values for the basis sheet:

- `tushare_fact`
- `annual_report_reference`
- `annual_report_bridge`
- `meeting_note_bridge`
- `local_kb_support`
- `alpha_pai_support`
- `retained_prior_logic`
- `manual_judgment_conservative_extension`

Recommended `model_role` values for the basis sheet:

- `driver_input`
- `derived_output`
- `summary_display`
- `tie_out_check`

Recommended `confidence` values:

- `high`: directly supported by official disclosure
- `medium`: supported by management comments or multiple secondary clues
- `low`: mainly retained prior logic or single weak clue

Recommended `review_flag` values:

- `none`
- `check_split`
- `check_driver`
- `check_formula`
- `missing_primary_source`

Evidence should name the source precisely:

- `Tushare` endpoint and period for deterministic facts
- annual report page or section for narrative reference
- meeting note excerpt or topic
- helper workbook sheet and row
- KB query and snippet
- Alpha Pai query and snippet

Evidence should also carry its source tier explicitly:

- `reference_file`
- `local_kb`
- `alpha_pai`

Every run should also persist recall checks at minimum for:

- `reference_files_recalled`
- `reference_files_have_content`
- `local_kb_recalled`
- `alpha_pai_recalled`
- `alpha_pai_has_content`
- `alpha_pai_call_count`
- `alpha_pai_query_plan`

Evidence rows should also be classifiable by role when needed:

- `fact`
- `mechanism`
- `historical_context`
- `stale_forecast`

Priority rule:

- prefer `reference_file` over `local_kb`
- prefer `local_kb` over `alpha_pai`
- recall `alpha_pai` on every run even when higher-priority sources are sufficient
- if any segment crosses `30%` revenue share or `40%` reported-year growth, recall Alpha Pai again with the company plus that segment keyword
- keep Alpha Pai recall types limited to `roadShow`, `roadShow_ir`, `roadShow_us`, and `comment`
- do not use Alpha Pai `report` or `foreign_report` carriers in this workflow
- if a lower-priority source is used for a material forecast point, explain why higher-priority sources were insufficient
- if a research-report line is a stale forecast line, do not let it justify the new run's forecast number directly

If a number cannot be traced to a concrete source, say so explicitly.

If a forecast number is material but cannot be defended in one or two lines on the basis sheet, the forecast is not ready for handoff.

For reusable workflows, do not rely on prompt obedience alone. Enforce basis formatting through:

- structured `evidence_items` in `forecast_basis.json`
- validation that rejects missing or blob-style evidence
- deterministic markdown and workbook-sheet renderers that consume the structured contract

If a formula was replaced by a hardcoded value, say so explicitly and explain why the original formula was no longer appropriate.

User-facing explanatory outputs should default to Chinese unless the user explicitly asks otherwise.
