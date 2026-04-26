# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(payload: Any) -> str:
    return sha256_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def sha256_jsonl(lines: list[dict[str, Any]]) -> str:
    encoded = "\n".join(
        json.dumps(line, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for line in lines
    ).encode("utf-8")
    return sha256_bytes(encoded)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows
