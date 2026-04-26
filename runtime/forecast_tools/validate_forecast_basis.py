# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .build_cell_instructions import validate_forecast_basis


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate forecast_basis.json")
    parser.add_argument("--input", required=True, help="Path to forecast_basis.json")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    validate_forecast_basis(payload)
    print("forecast_basis ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
