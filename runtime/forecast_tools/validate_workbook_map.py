# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .build_cell_instructions import validate_workbook_map


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate workbook_map.json")
    parser.add_argument("--input", required=True, help="Path to workbook_map.json")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    validate_workbook_map(payload)
    print("workbook_map ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
