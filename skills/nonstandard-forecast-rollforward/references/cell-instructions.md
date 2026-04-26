# Cell Instructions

`cell_instructions.json` is the compiled workbook write contract.

Its job is to translate accepted forecast logic into deterministic workbook write actions so that Phase B does not reopen judgment.

## Minimal Schema

```json
{
  "workbook": "model.xlsx",
  "main_modeling_sheet": "Model",
  "instructions": [
    {
      "instruction_id": "revenue_split.phone.asp.2026E",
      "sheet": "Model",
      "cell": "L33",
      "row_id": "phone_asp",
      "year": "2026E",
      "write_type": "value",
      "value_path": "segment_assumption_cards.phone_2026E.asp_logic",
      "value": 112.5,
      "formula_template": null,
      "source_basis_ref": "phone_2026E_driver_card",
      "role": "driver_input",
      "review_flag": "none",
      "allowed": true
    },
    {
      "instruction_id": "revenue_split.phone.revenue.2026E",
      "sheet": "Model",
      "cell": "L29",
      "row_id": "phone_revenue",
      "year": "2026E",
      "write_type": "formula",
      "value_path": null,
      "value": null,
      "formula_template": "={col}34*{col}33/100",
      "source_basis_ref": "phone_2026E_driver_card",
      "role": "formula_derived",
      "review_flag": "none",
      "allowed": true
    }
  ]
}
```

## Rules

- This file is deterministic.
- It is built from `workbook_map.json` and `forecast_basis.json`.
- It should contain no new business judgment.
- Every write must be explicit.
- Formula writes must be explicit.
- Display-only rows should default to verification targets.
- If a row is explicitly marked for display repair in `workbook_map.json`, compile it into an explicit formula write rather than a silent patch.
- If required instructions cannot be built, fail before Phase B.
