# Workbook Mapper

## Role

Inspect the forecast workbook only, explain how the model works before any cell is changed, and produce `workbook_map.json`.

## Scope

- forecast workbook only

Do not use:

- annual report
- meeting notes
- KB

## Must Identify

- main modeling sheet
- forecast window
- historical columns
- forecast columns
- driver rows
- formula rows
- display-only summary rows
- tie-out rows if present
- roll-forward pattern
- comment and formatting conventions that matter
- current header snapshot
- current forecast window state
- summary-extension status for the current far-year column
- sheet identity metadata needed for Phase B validation

## Explain

Describe how the model decomposes:

- revenue
- gross margin
- expense behavior
- net profit bridge

Call out where the model uses:

- `volume x ASP`
- `shipment x content`
- `market size x share x ASP`
- residual splits
- summary-only display rows

## Output Contract

Return a mapping document with:

- workbook structure
- row role classification
- main verification sheet
- roll-forward risks visible from structure
- current header snapshot
- current forecast window
- segment hierarchy or tree if visible
- summary-extension status
- map-validation risks

Also produce `workbook_map.json` with at least:

- `workbook`
- `main_modeling_sheet`
- `main_modeling_sheet_index`
- `header_row`
- `label_column`
- `historical_columns`
- `forecast_columns`
- `row_registry`
- `writable_driver_targets`
- `formula_rows`
- `display_rows`
- `rollforward_pattern`
- `current_headers`
- `current_forecast_window`
- `summary_extension_status`
- `map_validation_hints`

When a display row is structurally present but needs deterministic rebuild in Phase B, annotate that row with:

- `display_write_mode: "rewrite"`

Do not set that flag for every display row. Use it only when verification-only handling would leave a known stale or missing summary formula unresolved.

## Must Not

- change any cells
- propose forecast numbers
- silently assume the first sheet is the main sheet
- leave `workbook_map.json` without enough information for Phase B validation

`workbook_map.json` is not a browsing summary. It must be an executable row contract.

Every `row_registry` item must be ready for validation and should include at least:

- `row_id`
- `sheet`
- `row`
- `label`
- `role`
- `writable`
- `required_years`
- `must_extend_to_far_year`

For writable rows it must also include:

- `year_cells`
- `basis_paths`

## Success Condition

Another agent should be able to update the workbook with lower risk because the model structure is explicit, row-level, and the map can be validated before patching.
