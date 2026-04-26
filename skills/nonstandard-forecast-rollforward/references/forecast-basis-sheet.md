# Forecast Basis Sheet

Use a dedicated workbook sheet named `Forecast Basis`.

Purpose:

- explain why the important forecast numbers are what they are
- separate hard facts from bridge logic and judgment
- give a reviewer a fast path to challenge weak assumptions
- force the forecast writeup to spend enough space on `FY1-FY3` logic rather than only on actual-year bridging

Recommended layout:

| sheet | target_row | year | value | basis_type | model_role | driver | affected_by | evidence_summary | source_ref | confidence | review_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Examples:

| 营收拆分 | 分部A收入 | 2025E | 82.0 | management_guidance | driver_input | volume + mix | new program ramp, mix improvement | pre-cutoff meetings indicate shipments accelerate and mix improves into FY1 | meeting notes 2025-04-29 | medium | none |
| 营收拆分 | 分部B收入 | 2024A | 15.57 | retained_prior_logic | driver_input | residual bridge | anchored by disclosed major segments and remaining business lines | no explicit disclosed split for this line; residual retained after anchoring disclosed buckets | annual report + meeting notes | medium | check_split |
| 利润拆分 | 销售费用率 | 2026E | 2.12% | manual_judgment_conservative_extension | driver_input | operating leverage | revenue scale and mix improvement | expense ratio fades modestly with scale; no explicit guidance | model continuation from 2024A and 2025E | medium | check_driver |

Rules:

- Keep the sheet concise and review-oriented.
- Include the important lines, not every formula cell.
- Prefer row labels a human can recognize over raw coordinates.
- If the workbook contains a parameter block, include both the parameter and the affected top-line row when useful.
- User-facing content on this sheet should default to Chinese.
- Future-year rows must be more than slogan-level. For major segments, record the actual driver form such as `volume x ASP`, `market size x share x ASP`, or a clearly labeled conservative growth bridge.
- The sheet should show not only how `2024A` was bridged, but also how `2025E`, `2026E`, and `2027E` were built.
- For each major future segment, explain both revenue logic and margin logic.
- Include explicit rows or notes for selling, admin, R&D, and financial expense assumptions when they materially drive net margin.
- Render each row from structured evidence items rather than pasting raw long text.
- The `依据摘要` column should contain short claims only.
- The `来源` column should contain precise human-readable source labels only.
- If a row cannot be expressed as short `claim + source` pairs, it should fail validation upstream.
