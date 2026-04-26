# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contract_validators import validate_patch_log_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate patch_log.json")
    parser.add_argument("--input", required=True, help="Path to patch_log.json")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    validate_patch_log_payload(payload)
    print("patch_log ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
