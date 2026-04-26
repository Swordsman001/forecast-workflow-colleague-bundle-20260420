# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


CELL_RE = re.compile(r"^(?P<col>[A-Z]+)(?P<row>\d+)$")


class ContractValidationError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_keys(data: dict[str, Any], keys: list[str], context: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ContractValidationError(f"{context} missing required keys: {', '.join(missing)}")


def validate_workbook_map(workbook_map: dict[str, Any]) -> None:
    _require_keys(
        workbook_map,
        [
            "workbook",
            "main_modeling_sheet",
            "main_modeling_sheet_index",
            "header_row",
            "label_column",
            "historical_columns",
            "forecast_columns",
            "rollforward_pattern",
            "current_headers",
            "current_forecast_window",
            "summary_extension_status",
            "row_registry",
            "writable_driver_targets",
            "formula_rows",
            "display_rows",
            "map_validation_hints",
        ],
        "workbook_map",
    )
    row_registry = workbook_map["row_registry"]
    if not isinstance(row_registry, list) or not row_registry:
        raise ContractValidationError("workbook_map.row_registry must be a non-empty list")
    for idx, row in enumerate(row_registry):
        _require_keys(
            row,
            [
                "row_id",
                "sheet",
                "row",
                "label",
                "role",
                "writable",
                "required_years",
                "must_extend_to_far_year",
            ],
            f"row_registry[{idx}]",
        )
        if row["writable"]:
            _require_keys(row, ["year_cells", "basis_paths"], f"row_registry[{idx}]")
        display_write_mode = row.get("display_write_mode")
        if display_write_mode not in {None, "verify", "rewrite"}:
            raise ContractValidationError(
                f"row_registry[{idx}] has invalid display_write_mode: {display_write_mode}"
            )


def validate_forecast_basis(forecast_basis: dict[str, Any]) -> None:
    _require_keys(
        forecast_basis,
        [
            "company",
            "cutoff_date",
            "reported_year",
            "target_window",
            "language",
            "completeness_audit",
            "facts",
            "assumptions",
            "segment_assumption_cards",
        ],
        "forecast_basis",
    )
    audit = forecast_basis["completeness_audit"]
    if not isinstance(audit, dict) or not audit.get("passed", False):
        raise ContractValidationError("forecast_basis completeness_audit must exist and pass")
    cards = forecast_basis["segment_assumption_cards"]
    if not isinstance(cards, list):
        raise ContractValidationError("forecast_basis.segment_assumption_cards must be a list")
    facts = forecast_basis["facts"]
    if not isinstance(facts, list):
        raise ContractValidationError("forecast_basis.facts must be a list")
    for idx, fact in enumerate(facts):
        evidence_items = fact.get("evidence_items")
        if not isinstance(evidence_items, list) or not evidence_items:
            raise ContractValidationError(
                f"facts[{idx}] must include non-empty structured evidence_items"
            )
    for idx, card in enumerate(cards):
        _require_keys(
            card,
            [
                "segment",
                "year",
                "metric",
                "value",
                "driver_form",
                "volume_logic",
                "asp_logic",
                "share_logic",
                "margin_logic",
                "kill_conditions",
            ],
            f"segment_assumption_cards[{idx}]",
        )
        if not card["kill_conditions"]:
            raise ContractValidationError(f"segment_assumption_cards[{idx}] must have kill_conditions")
        evidence_items = card.get("evidence_items")
        if not isinstance(evidence_items, list) or not evidence_items:
            raise ContractValidationError(
                f"segment_assumption_cards[{idx}] must include non-empty structured evidence_items"
            )
        for logic_key in ("volume_logic", "asp_logic", "share_logic", "margin_logic"):
            logic_payload = card.get(logic_key)
            if not isinstance(logic_payload, dict):
                raise ContractValidationError(f"segment_assumption_cards[{idx}].{logic_key} must be an object")
            logic_evidence = logic_payload.get("evidence_items")
            if not isinstance(logic_evidence, list):
                raise ContractValidationError(
                    f"segment_assumption_cards[{idx}].{logic_key} must include evidence_items list"
                )


def resolve_path(data: Any, path: str) -> Any:
    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                raise ContractValidationError(f"basis path not found: {path}")
            current = current[part]
            continue
        if isinstance(current, list):
            matched = None
            for item in current:
                if not isinstance(item, dict):
                    continue
                key = item.get("key")
                row_id = item.get("row_id")
                card_key = item.get("card_key")
                composite = ".".join(
                    str(piece)
                    for piece in (item.get("segment"), item.get("year"), item.get("metric"))
                    if piece is not None
                )
                if part in {key, row_id, card_key, composite}:
                    matched = item
                    break
            if matched is None:
                raise ContractValidationError(f"list path segment not found: {path}")
            current = matched
            continue
        raise ContractValidationError(f"cannot resolve path {path} beyond scalar value")
    return current


def _column_from_cell(cell: str) -> str:
    match = CELL_RE.match(cell)
    if not match:
        raise ContractValidationError(f"invalid cell reference: {cell}")
    return match.group("col")


def _build_value_instruction(
    row: dict[str, Any],
    year: str,
    basis: dict[str, Any],
) -> dict[str, Any]:
    cell = row["year_cells"].get(year)
    if not cell:
        raise ContractValidationError(f"missing year cell for row {row['row_id']} year {year}")
    value_path = row["basis_paths"].get(year) or row.get("basis_path")
    if not value_path:
        raise ContractValidationError(f"missing basis path for row {row['row_id']} year {year}")
    value = resolve_path(basis, value_path)
    return {
        "instruction_id": f"{row['row_id']}.{year}",
        "sheet": row["sheet"],
        "cell": cell,
        "row_id": row["row_id"],
        "year": year,
        "write_type": "value",
        "value_path": value_path,
        "value": value,
        "formula_template": None,
        "source_basis_ref": value_path,
        "role": row["role"],
        "review_flag": row.get("validation", {}).get("review_flag"),
        "allowed": True,
        "formula_preserved": None,
    }


def _build_formula_instruction(row: dict[str, Any], year: str) -> dict[str, Any]:
    cell = row.get("year_cells", {}).get(year)
    if not cell:
        raise ContractValidationError(f"missing year cell for formula row {row['row_id']} year {year}")
    template = row.get("formula_template")
    if not template:
        raise ContractValidationError(f"missing formula_template for row {row['row_id']}")
    formula = template.replace("{col}", _column_from_cell(cell))
    return {
        "instruction_id": f"{row['row_id']}.{year}",
        "sheet": row["sheet"],
        "cell": cell,
        "row_id": row["row_id"],
        "year": year,
        "write_type": "formula",
        "value_path": None,
        "value": None,
        "formula_template": formula,
        "source_basis_ref": row.get("source_row_id"),
        "role": row["role"],
        "review_flag": row.get("validation", {}).get("review_flag"),
        "allowed": True,
        "formula_preserved": True,
    }


def _build_verification_target(row: dict[str, Any], year: str) -> dict[str, Any]:
    cell = row.get("year_cells", {}).get(year)
    if not cell:
        raise ContractValidationError(f"missing year cell for display row {row['row_id']} year {year}")
    template = row.get("formula_template")
    formula = template.replace("{col}", _column_from_cell(cell)) if template else None
    return {
        "instruction_id": f"{row['row_id']}.{year}",
        "sheet": row["sheet"],
        "cell": cell,
        "row_id": row["row_id"],
        "year": year,
        "write_type": "verification_target",
        "value_path": None,
        "value": None,
        "formula_template": formula,
        "source_basis_ref": row.get("source_row_id"),
        "role": row["role"],
        "review_flag": row.get("validation", {}).get("review_flag"),
        "allowed": True,
        "formula_preserved": row.get("formula_template") is not None,
    }


def _build_display_instruction(row: dict[str, Any], year: str) -> dict[str, Any]:
    if row.get("display_write_mode") == "rewrite":
        return _build_formula_instruction(row, year)
    return _build_verification_target(row, year)


def build_cell_instructions(
    workbook_map: dict[str, Any],
    forecast_basis: dict[str, Any],
    *,
    source_workbook_hash: str | None = None,
    workbook_map_hash: str | None = None,
    forecast_basis_hash: str | None = None,
    evidence_store_hash: str | None = None,
) -> dict[str, Any]:
    validate_workbook_map(workbook_map)
    validate_forecast_basis(forecast_basis)

    instructions: list[dict[str, Any]] = []
    for row in workbook_map["row_registry"]:
        for year in row["required_years"]:
            if row["writable"]:
                instructions.append(_build_value_instruction(row, year, forecast_basis))
            elif row["role"] in {"formula_derived", "tie_out_check"}:
                instructions.append(_build_formula_instruction(row, year))
            elif row["role"] in {"display_formula", "summary_display"}:
                instructions.append(_build_display_instruction(row, year))

    return {
        "workbook": workbook_map["workbook"],
        "main_modeling_sheet": workbook_map["main_modeling_sheet"],
        "generated_by": "build_cell_instructions.py",
        "source_workbook_hash": source_workbook_hash,
        "workbook_map_hash": workbook_map_hash,
        "forecast_basis_hash": forecast_basis_hash,
        "evidence_store_hash": evidence_store_hash,
        "instructions": instructions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic cell instructions from workbook map and forecast basis")
    parser.add_argument("--workbook-map", required=True, help="Path to workbook_map.json")
    parser.add_argument("--forecast-basis", required=True, help="Path to forecast_basis.json")
    parser.add_argument("--output", required=True, help="Path to output cell_instructions.json")
    args = parser.parse_args()

    workbook_map = load_json(Path(args.workbook_map))
    forecast_basis = load_json(Path(args.forecast_basis))
    output = build_cell_instructions(workbook_map, forecast_basis)
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
