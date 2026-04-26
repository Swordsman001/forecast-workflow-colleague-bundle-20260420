# Workbook Map

`workbook_map.json` is the single-company workbook structure map.

Its job is to stop the workflow from re-learning the same workbook structure on every run and to give Phase B a validated structure contract.

## Minimal Schema

```json
{
  "workbook": "model.xlsx",
  "main_modeling_sheet": "Model",
  "main_modeling_sheet_index": 0,
  "header_row": 2,
  "label_column": "B",
  "historical_columns": ["J"],
  "forecast_columns": ["K", "L", "M"],
  "rollforward_pattern": {
    "reported_col": "K",
    "forecast_start_col": "L",
    "new_far_year_col": "N"
  },
  "current_headers": {
    "J": "2024A",
    "K": "2025E",
    "L": "2026E"
  },
  "current_forecast_window": ["2025E", "2026E"],
  "summary_extension_status": {
    "adjacent_forecast_populated_new_far_year_blank": 0
  },
  "row_registry": [
    {
      "row_id": "summary_segment_alpha_revenue",
      "sheet": "Model",
      "row": 118,
      "label": "分部A收入",
      "role": "display_formula",
      "writable": false,
      "formula_template": "={col}51",
      "source_row_id": "segment_alpha_revenue",
      "display_write_mode": "rewrite",
      "required_years": ["2025A", "2026E", "2027E", "2028E"],
      "must_extend_to_far_year": true,
      "style_source_col": "L",
      "validation": {
        "non_blank_if_previous_year_non_blank": true,
        "expected_reference_row": 51
      }
    }
  ],
  "writable_driver_targets": ["segment_alpha_revenue_2026E"],
  "formula_rows": ["gross_profit_total_2026E"],
  "display_rows": ["summary_segment_alpha_revenue_2026E"],
  "map_validation_hints": {
    "must_match_headers": true,
    "must_resolve_targets": true
  }
}
```

## Rules

- Keep it structural.
- Do not store forecast judgment here.
- Prefer semantic keys and row identifiers over raw coordinates alone.
- Separate writable targets from formula-driven rows and display-only rows.
- Include enough current-state snapshot data that the controller does not have to reopen the workbook just to learn headers or extension status.
- Include enough row-level metadata that instruction compilation can detect missing future-year coverage before patching.
- Include enough metadata that Phase B can validate the map before writing.
- Keep display rows verification-only by default; only rows explicitly marked with `display_write_mode: "rewrite"` should compile into display formula writes.
