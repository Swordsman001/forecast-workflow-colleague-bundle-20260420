# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
import os

from .build_cell_instructions import ContractValidationError
from .contract_validators import validate_cell_instructions_payload, validate_patch_log_payload
from .artifact_utils import sha256_file


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp") as handle:
        handle.write(text)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def verify_contract_patch(
    *,
    cell_instructions: dict[str, Any],
    patch_log: list[dict[str, Any]],
    candidate_workbook_path: Path,
    report_path: Path | None = None,
) -> dict[str, Any]:
    validate_cell_instructions_payload(cell_instructions)
    validate_patch_log_payload(patch_log)

    expected_ids = [item["instruction_id"] for item in cell_instructions["instructions"]]
    actual_ids = [item["instruction_id"] for item in patch_log]
    missing_ids = [instruction_id for instruction_id in expected_ids if instruction_id not in actual_ids]
    extra_ids = [instruction_id for instruction_id in actual_ids if instruction_id not in expected_ids]

    candidate_hash = sha256_file(candidate_workbook_path)
    output_hashes = {entry["output_hash"] for entry in patch_log}
    hash_match = output_hashes == {candidate_hash}
    if not hash_match:
        raise ContractValidationError("patch_log output_hash does not match candidate workbook hash")

    instruction_hashes = {entry["instruction_hash"] for entry in patch_log}
    basis_hashes = {entry["basis_hash"] for entry in patch_log}
    map_hashes = {entry["map_hash"] for entry in patch_log}
    evidence_hashes = {entry["evidence_hash"] for entry in patch_log}
    expected_instruction_hash = cell_instructions.get("cell_instructions_hash")
    expected_basis_hash = cell_instructions.get("forecast_basis_hash")
    expected_map_hash = cell_instructions.get("workbook_map_hash")
    expected_evidence_hash = cell_instructions.get("evidence_store_hash")
    instruction_hash_match = instruction_hashes == {expected_instruction_hash}
    basis_hash_match = basis_hashes == {expected_basis_hash}
    map_hash_match = map_hashes == {expected_map_hash}
    evidence_hash_match = evidence_hashes == {expected_evidence_hash}
    if not instruction_hash_match:
        raise ContractValidationError("patch_log instruction_hash does not match cell_instructions hash")
    if not basis_hash_match:
        raise ContractValidationError("patch_log basis_hash does not match forecast_basis hash")
    if not map_hash_match:
        raise ContractValidationError("patch_log map_hash does not match workbook_map hash")
    if not evidence_hash_match:
        raise ContractValidationError("patch_log evidence_hash does not match evidence_store hash")

    report = {
        "passed": not missing_ids and not extra_ids and hash_match and instruction_hash_match and basis_hash_match and map_hash_match and evidence_hash_match,
        "instruction_count": len(expected_ids),
        "patch_log_count": len(actual_ids),
        "missing_instruction_ids": missing_ids,
        "extra_instruction_ids": extra_ids,
        "candidate_hash": candidate_hash,
        "hash_match": hash_match,
        "instruction_hash_match": instruction_hash_match,
        "basis_hash_match": basis_hash_match,
        "map_hash_match": map_hash_match,
        "evidence_hash_match": evidence_hash_match,
    }
    if report_path is not None:
        _atomic_write_text(report_path, json.dumps(report, ensure_ascii=False, indent=2))
    return report
