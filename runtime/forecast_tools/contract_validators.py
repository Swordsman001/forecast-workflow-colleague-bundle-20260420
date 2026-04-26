# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from .build_cell_instructions import ContractValidationError


def _require_keys(data: dict[str, Any], keys: list[str], context: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ContractValidationError(f"{context} missing required keys: {', '.join(missing)}")


def validate_cell_instructions_payload(payload: dict[str, Any]) -> None:
    _require_keys(
        payload,
        [
            "workbook",
            "main_modeling_sheet",
            "generated_by",
            "source_workbook_hash",
            "workbook_map_hash",
            "forecast_basis_hash",
            "evidence_store_hash",
            "instructions",
        ],
        "cell_instructions",
    )
    instructions = payload["instructions"]
    if not isinstance(instructions, list) or not instructions:
        raise ContractValidationError("cell_instructions.instructions must be a non-empty list")

    allowed_write_types = {"value", "formula", "verification_target"}
    seen_ids: set[str] = set()
    for idx, instruction in enumerate(instructions):
        _require_keys(
            instruction,
            [
                "instruction_id",
                "sheet",
                "cell",
                "row_id",
                "year",
                "write_type",
                "source_basis_ref",
                "role",
                "allowed",
            ],
            f"instructions[{idx}]",
        )
        instruction_id = instruction["instruction_id"]
        if instruction_id in seen_ids:
            raise ContractValidationError(f"duplicate instruction_id: {instruction_id}")
        seen_ids.add(instruction_id)

        write_type = instruction["write_type"]
        if write_type not in allowed_write_types:
            raise ContractValidationError(f"instructions[{idx}] has unsupported write_type: {write_type}")
        if instruction["allowed"] is not True:
            raise ContractValidationError(f"instructions[{idx}] must be explicitly allowed")

        if write_type == "value":
            if "value" not in instruction:
                raise ContractValidationError(f"instructions[{idx}] missing value for write_type=value")
            if not instruction.get("value_path"):
                raise ContractValidationError(f"instructions[{idx}] missing value_path for write_type=value")
        else:
            formula_template = instruction.get("formula_template")
            if not formula_template:
                raise ContractValidationError(
                    f"instructions[{idx}] missing formula_template for write_type={write_type}"
                )


def validate_patch_log_payload(payload: list[dict[str, Any]]) -> None:
    if not isinstance(payload, list) or not payload:
        raise ContractValidationError("patch_log must be a non-empty list")

    required_keys = [
        "sheet",
        "cell",
        "row_id",
        "year",
        "before",
        "after",
        "write_type",
        "instruction_id",
        "basis_ref",
        "review_flag",
        "formula_preserved",
        "parity_audit_status",
        "instruction_hash",
        "basis_hash",
        "map_hash",
        "evidence_hash",
        "output_hash",
    ]
    for idx, entry in enumerate(payload):
        _require_keys(entry, required_keys, f"patch_log[{idx}]")
        if not entry["output_hash"]:
            raise ContractValidationError(f"patch_log[{idx}] missing output_hash")
        if entry["parity_audit_status"] not in {"pending", "passed", "failed"}:
            raise ContractValidationError(
                f"patch_log[{idx}] has invalid parity_audit_status: {entry['parity_audit_status']}"
            )


def validate_evidence_store_payload(payload: list[dict[str, Any]]) -> None:
    if not isinstance(payload, list) or not payload:
        raise ContractValidationError("evidence_store must be a non-empty list")

    required_line_keys = ["fact_id", "company", "period", "metric", "source_type", "confidence"]
    for idx, line in enumerate(payload):
        _require_keys(line, required_line_keys, f"evidence_store[{idx}]")
