# Forecast Basis JSON

`forecast_basis.json` is the machine-readable version of the approved forecast basis.

Its job is to carry approved facts and assumptions into instruction compilation without reopening judgment.

## Minimal Schema

```json
{
  "company": "example_co",
  "cutoff_date": "2025-05-31",
  "reported_year": "2024A",
  "target_window": ["2025E", "2026E", "2027E"],
  "language": "zh-CN",
  "completeness_audit": {
    "passed": true,
    "missing_segments": [],
    "missing_years": [],
    "missing_margin_logic": []
  },
  "facts": [
    {
      "key": "reported_revenue_2024A",
      "value": 257.31,
      "source_ref": "annual report p.8",
      "confidence": "high"
    }
  ],
  "assumptions": [
    {
      "key": "segment_alpha_revenue_2025E",
      "value": 88.2,
      "basis_type": "management_guidance",
      "source_ref": "meeting notes 2025-04-29",
      "review_flag": "none"
    }
  ],
  "segment_assumption_cards": [
    {
      "segment": "分部A",
      "year": "2026E",
      "metric": "revenue",
      "value": 92.5,
      "unit": "RMB_100m",
      "driver_form": "volume x ASP",
      "volume_logic": {
        "direction": "up",
        "mechanism": "新项目导入带动有效出货量提升",
        "evidence_refs": ["meeting_segment_alpha_2025", "research_segment_alpha_mix"]
      },
      "asp_logic": {
        "direction": "up",
        "mechanism": "高规格产品占比提升"
      },
      "share_logic": {
        "direction": "stable_to_up",
        "mechanism": "核心客户绑定和产品迭代支撑份额"
      },
      "margin_logic": {
        "value": 0.36,
        "mechanism": "高附加值产品 mix 提升带动毛利率改善"
      },
      "weak_assumptions": ["高端需求恢复", "主要客户导入节奏正常"],
      "kill_conditions": ["ASP 下行超预期", "新产品导入延后"],
      "source_ref": "meeting notes 2025-04-29; research summary",
      "confidence": "medium",
      "review_flag": "none"
    }
  ],
  "consolidated_logic": {
    "selling_expense_logic": "费用额温和增长，费率随收入放大而下降",
    "admin_expense_logic": "管理费用绝对额基本稳定",
    "rnd_expense_logic": "研发维持平台投入，费率缓慢下降",
    "financial_expense_logic": "汇率和融资成本影响有限",
    "net_margin_bridge": "毛利率改善和费用率下行共同驱动净利率提升"
  }
}
```

## Rules

- Keep it judgment-focused.
- Do not mirror workbook structure here beyond what instruction compilation needs.
- Facts, assumptions, weak assumptions, kill conditions, and review flags should be explicit.
- Future forecast logic should not stop at a numeric target. Record how the segment gets there.
- The file should be complete enough that instruction compilation does not need to invent missing logic.
- This file works with `workbook_map.json`; it does not replace it.
- Every fact and every major segment card should include structured `evidence_items`.
- `evidence_items` should be the canonical source for markdown and workbook-sheet rendering.
- Do not store long raw report or transcript blobs as the basis explanation.
- Segment names should come from the current workbook and current case evidence, not a prior case template.
- Facts should normally point to annual-report evidence only; do not attach every reference file to every disclosed fact.
- Research-report lines that contain prior analyst forecast numbers or future-year targets should be tagged as stale support and excluded from direct forecast justification.
- Dedupe repeated evidence rows deterministically so one card does not repeat the same claim from the same source.
