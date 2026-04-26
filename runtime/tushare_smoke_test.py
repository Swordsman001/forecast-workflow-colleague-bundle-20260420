# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.data_sources.tushare_client import TushareClient


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def build_smoke_result(
    *,
    client: TushareClient,
    api_name: str,
    ts_code: str | None,
    start_date: str | None,
    end_date: str | None,
    limit: int,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if ts_code:
        kwargs["ts_code"] = ts_code
    if start_date:
        kwargs["start_date"] = start_date
    if end_date:
        kwargs["end_date"] = end_date
    data = getattr(client, api_name)(**kwargs)
    return {
        "api_name": api_name,
        "row_count": len(data),
        "columns": data.columns.tolist(),
        "preview": data.head(limit).to_dict(orient="records"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tushare 接入 smoke test")
    parser.add_argument("--api", default="trade_cal", help="要测试的接口名")
    parser.add_argument("--ts-code", default=None, help="证券代码，例如 600519.SH")
    parser.add_argument("--start-date", default=None, help="开始日期 YYYYMMDD")
    parser.add_argument("--end-date", default=None, help="结束日期 YYYYMMDD")
    parser.add_argument("--limit", type=int, default=5, help="预览行数")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = TushareClient()
    result = build_smoke_result(
        client=client,
        api_name=args.api,
        ts_code=args.ts_code,
        start_date=args.start_date,
        end_date=args.end_date,
        limit=args.limit,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
