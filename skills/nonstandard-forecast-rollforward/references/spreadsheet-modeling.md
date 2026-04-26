# Spreadsheet Modeling

This skill should borrow the working style of a spreadsheet-specific workflow while staying focused on nonstandard earnings models.

## Core Excel Behavior

Treat the workbook as a living model, not a static report.

Before editing, inspect:

- row labels
- year headers
- formulas on the target row
- formulas on nearby summary rows
- comments and note cells
- formatting that distinguishes inputs, formulas, links, and forecasts

Prefer to update model inputs and preserve formulas.

## Default Editing Order

1. Actualize the latest reported year
2. Identify the rows that are real inputs versus displayed outputs
3. Update the driver layer
4. Rebuild split logic only where evidence changes it
5. Recalculate
6. Review the rendered or recalculated workbook

## Driver-First Principle

Good candidates to edit directly:

- share assumptions
- volume assumptions
- ASP assumptions
- margin assumptions
- expense ratios
- tax rate
- non-operating recurring assumptions

Rows to avoid hardcoding first unless necessary:

- total revenue
- total gross profit
- total net profit
- display-only summary tables

## Formula Awareness

When copying formulas into a new far-year column:

- check absolute and relative references
- check that the range did not shift one row too far
- check that totals still sum the intended rows
- check that copied formulas do not accidentally point into the new note column

Avoid introducing complicated modern Excel-only functions unless the workbook already uses them.

## Recalculation

Preferred order:

1. Excel local engine if available
2. LibreOffice if available
3. preserve formulas and document that recalculation is pending

If you cannot recalculate, do not bluff. State it.

When using Excel automation:

- prefer a hidden isolated instance over a user-visible shared session
- close only the workbook you opened
- never use global process-kill cleanup that could close the user's active workbooks
- if isolated automation is unstable, stop and switch methods instead of touching the user's live Excel session

## Visual Review

Review representative sheets or areas for:

- inconsistent formats in the new year column
- clipped text
- broken borders or fills
- unexpected blank cells
- formulas showing as text
- totals that no longer line up visually

## Intelligent Participation

The model should not be treated as a passive container for your forecast.

Use it to learn:

- which variables the prior analyst thought mattered
- which relationships were intended to remain stable
- where the workbook itself is signaling doubt, caution, or manual override

Then revise the model with evidence and judgment instead of overwriting it mechanically.

## Unicode Safety

Spreadsheet readability can be destroyed by bad text encoding even when the numbers are correct.

- Treat `?` replacing Chinese text as data corruption, not a font issue.
- Prefer UTF-8 script files for any workbook-writing logic that includes Chinese text.
- Avoid inline shell here-strings for non-ASCII workbook content unless the shell encoding has already been verified.
- Reopen the workbook after save and inspect representative text cells, comments, and sheet names.
