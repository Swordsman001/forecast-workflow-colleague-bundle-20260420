import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.forecast_tools.build_cell_instructions import (  # type: ignore
    ContractValidationError,
    build_cell_instructions,
)


def sample_workbook_map() -> dict:
    return {
        "workbook": "model.xlsx",
        "main_modeling_sheet": "Model",
        "main_modeling_sheet_index": 0,
        "header_row": 2,
        "label_column": "B",
        "historical_columns": {"2025A": "K"},
        "forecast_columns": {"2026E": "L", "2027E": "M"},
        "rollforward_pattern": {
            "reported_col": "K",
            "forecast_start_col": "L",
            "new_far_year_col": "N",
        },
        "current_headers": {"K": "2025A", "L": "2026E", "M": "2027E"},
        "current_forecast_window": ["2026E", "2027E"],
        "summary_extension_status": {"adjacent_forecast_populated_new_far_year_blank": 0},
        "row_registry": [
            {
                "row_id": "phone_asp",
                "sheet": "Model",
                "row": 33,
                "label": "手机 ASP",
                "role": "driver_input",
                "writable": True,
                "required_years": ["2026E", "2027E"],
                "must_extend_to_far_year": True,
                "year_cells": {"2026E": "L33", "2027E": "M33"},
                "basis_paths": {
                    "2026E": "assumptions.phone_asp_2026E.value",
                    "2027E": "assumptions.phone_asp_2027E.value",
                },
                "validation": {},
            },
            {
                "row_id": "phone_revenue",
                "sheet": "Model",
                "row": 29,
                "label": "手机收入",
                "role": "formula_derived",
                "writable": False,
                "required_years": ["2026E", "2027E"],
                "must_extend_to_far_year": True,
                "year_cells": {"2026E": "L29", "2027E": "M29"},
                "formula_template": "={col}34*{col}33/100",
                "source_row_id": "phone_volume",
                "validation": {},
            },
            {
                "row_id": "summary_phone_revenue",
                "sheet": "Model",
                "row": 118,
                "label": "摘要手机收入",
                "role": "summary_display",
                "writable": False,
                "required_years": ["2026E", "2027E"],
                "must_extend_to_far_year": True,
                "year_cells": {"2026E": "L118", "2027E": "M118"},
                "formula_template": "={col}29",
                "source_row_id": "phone_revenue",
                "validation": {},
            },
        ],
        "writable_driver_targets": ["phone_asp"],
        "formula_rows": ["phone_revenue"],
        "display_rows": ["summary_phone_revenue"],
        "map_validation_hints": {"must_match_headers": True},
    }


def sample_forecast_basis() -> dict:
    return {
        "company": "603501.SH",
        "cutoff_date": "2025-05-31",
        "reported_year": "2025A",
        "target_window": ["2026E", "2027E"],
        "language": "zh-CN",
        "completeness_audit": {"passed": True, "missing_segments": [], "missing_years": [], "missing_margin_logic": []},
        "facts": [],
        "assumptions": [
            {"key": "phone_asp_2026E", "value": 112.5},
            {"key": "phone_asp_2027E", "value": 118.0},
        ],
        "segment_assumption_cards": [
            {
                "segment": "手机CIS",
                "year": "2026E",
                "metric": "revenue",
                "value": 92.5,
                "driver_form": "volume x ASP",
                "volume_logic": {"mechanism": "高规格导入", "evidence_items": []},
                "asp_logic": {"mechanism": "像素升级", "evidence_items": []},
                "share_logic": {"mechanism": "高端份额稳定", "evidence_items": []},
                "margin_logic": {"mechanism": "高端 mix 改善", "evidence_items": []},
                "kill_conditions": ["ASP 下行超预期"],
                "evidence_items": [
                    {
                        "claim": "高规格机型导入，带动收入增长。",
                        "source_ref": "meeting-note-1",
                        "source_tier": "reference_files",
                        "source_label": "meeting-notes.docx | meeting_note",
                    }
                ],
            }
        ],
    }


class BuildCellInstructionsTests(unittest.TestCase):
    def test_builds_value_formula_and_verification_target_instructions(self) -> None:
        result = build_cell_instructions(sample_workbook_map(), sample_forecast_basis())

        self.assertEqual(result["main_modeling_sheet"], "Model")
        self.assertEqual(len(result["instructions"]), 6)

        phone_asp = next(item for item in result["instructions"] if item["instruction_id"] == "phone_asp.2026E")
        phone_revenue = next(item for item in result["instructions"] if item["instruction_id"] == "phone_revenue.2026E")
        summary_phone = next(item for item in result["instructions"] if item["instruction_id"] == "summary_phone_revenue.2026E")

        self.assertEqual(phone_asp["write_type"], "value")
        self.assertEqual(phone_asp["value"], 112.5)
        self.assertEqual(phone_revenue["write_type"], "formula")
        self.assertEqual(phone_revenue["formula_template"], "=L34*L33/100")
        self.assertEqual(summary_phone["write_type"], "verification_target")
        self.assertEqual(summary_phone["formula_template"], "=L29")

    def test_display_rows_can_be_promoted_from_verification_to_formula_writes(self) -> None:
        workbook_map = sample_workbook_map()
        workbook_map["row_registry"][2]["display_write_mode"] = "rewrite"

        result = build_cell_instructions(workbook_map, sample_forecast_basis())
        summary_phone = next(item for item in result["instructions"] if item["instruction_id"] == "summary_phone_revenue.2026E")

        self.assertEqual(summary_phone["write_type"], "formula")
        self.assertEqual(summary_phone["formula_template"], "=L29")
        self.assertTrue(summary_phone["formula_preserved"])

    def test_fails_when_writable_row_lacks_basis_path(self) -> None:
        workbook_map = sample_workbook_map()
        del workbook_map["row_registry"][0]["basis_paths"]["2027E"]

        with self.assertRaises(ContractValidationError):
            build_cell_instructions(workbook_map, sample_forecast_basis())

    def test_output_is_json_serializable(self) -> None:
        result = build_cell_instructions(sample_workbook_map(), sample_forecast_basis())
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cell_instructions.json"
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["generated_by"], "build_cell_instructions.py")


if __name__ == "__main__":
    unittest.main()
