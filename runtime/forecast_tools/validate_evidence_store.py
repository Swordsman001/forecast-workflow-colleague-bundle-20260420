# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

from .artifact_utils import load_jsonl
from .contract_validators import validate_evidence_store_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate evidence_store.jsonl")
    parser.add_argument("--input", required=True, help="Path to evidence_store.jsonl")
    args = parser.parse_args()

    payload = load_jsonl(Path(args.input))
    validate_evidence_store_payload(payload)
    print("evidence_store ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
