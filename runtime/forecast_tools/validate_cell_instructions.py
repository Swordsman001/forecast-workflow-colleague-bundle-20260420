# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contract_validators import validate_cell_instructions_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate cell_instructions.json")
    parser.add_argument("--input", required=True, help="Path to cell_instructions.json")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    validate_cell_instructions_payload(payload)
    print("cell_instructions ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
