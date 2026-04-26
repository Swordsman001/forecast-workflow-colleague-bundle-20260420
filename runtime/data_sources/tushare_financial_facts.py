# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .tushare_client import TushareClient


EXCHANGE_CODE_RE = re.compile(r"(?P<full>\d{6}\.(?:SH|SZ|BJ))", re.IGNORECASE)
SYMBOL_RE = re.compile(r"(?<!\d)(?P<symbol>\d{6})(?!\d)")
REGION_HINTS = (
    "境内",
    "境外",
    "国内",
    "国外",
    "海外",
    "华东",
    "华南",
    "华北",
    "华中",
    "西南",
    "西北",
    "东北",
    "北美",
    "欧洲",
    "亚太",
    "地区",
    "区域",
)
SALES_MODE_HINTS = (
    "直销",
    "经销",
    "代销",
    "线上",
    "线下",
    "出口",
    "内销",
    "零售",
    "批发",
    "模式",
)
BUSINESS_SUFFIXES = ("业务", "产品", "解决方案", "方案", "器件", "模组", "材料", "服务")


def _rows(records: Any) -> list[dict[str, Any]]:
    if records is None:
        return []
    if isinstance(records, list):
        return [dict(item) for item in records]
    to_dict = getattr(records, "to_dict", None)
    if callable(to_dict):
        try:
            return [dict(item) for item in to_dict(orient="records")]
        except TypeError:
            pass
    return []


def _first_row(records: Any) -> dict[str, Any]:
    rows = _rows(records)
    return rows[0] if rows else {}


def _to_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def _pct_to_ratio(value: Any) -> float | None:
    numeric = _to_float(value)
    if numeric is None:
        return None
    if abs(numeric) > 1:
        return numeric / 100
    return numeric


def _first_numeric(row: dict[str, Any], *keys: str, ratio: bool = False) -> float | None:
    for key in keys:
        if key not in row:
            continue
        parsed = _pct_to_ratio(row.get(key)) if ratio else _to_float(row.get(key))
        if parsed is not None:
            return parsed
    return None


def _fact_item(*, metric: str, value: float | None, unit: str, source_ref: str, source_label: str, note: str) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "metric": metric,
        "value": value,
        "unit": unit,
        "page_reference": source_label,
        "file_reference": source_ref,
        "source_ref": source_ref,
        "source_label": source_label,
        "note": note,
    }


def _classify_segment_dimension(segment: str) -> str:
    text = str(segment or "").strip()
    if not text:
        return "unknown"
    if any(token in text for token in REGION_HINTS):
        return "region"
    if any(token in text for token in SALES_MODE_HINTS):
        return "sales_mode"
    if any(text.endswith(token) or token in text for token in BUSINESS_SUFFIXES):
        return "business"
    return "business"


def _normalize_segment_label(segment: str) -> str:
    text = str(segment or "").strip()
    text = re.sub(r"^\s*\d+\s*[)）.、]\s*", "", text)
    text = re.sub(r"[（(].*?[)）]", "", text)
    text = text.replace("其中：", "").replace("其中:", "").strip()
    return text


def _normalize_segment_disclosure_rows(
    rows: list[dict[str, Any]],
    *,
    source_ref: str,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        raw_segment = str(row.get("bz_item") or row.get("segment") or "").strip()
        if not raw_segment:
            continue
        dimension = _classify_segment_dimension(raw_segment)
        mapping_ready = dimension == "business"
        if not mapping_ready:
            continue
        segment = _normalize_segment_label(raw_segment)
        if not segment:
            continue
        segment_revenue = _first_numeric(row, "bz_sales", "sales", "revenue")
        segment_cost = _first_numeric(row, "bz_cost", "cost")
        segment_margin = None
        if segment_revenue not in {None, 0, 0.0} and segment_cost is not None:
            segment_margin = (segment_revenue - segment_cost) / segment_revenue
        signature = (dimension, segment)
        if signature in seen:
            continue
        seen.add(signature)
        normalized.append(
            {
                "segment": segment,
                "raw_segment": raw_segment,
                "revenue": segment_revenue,
                "gross_margin": segment_margin,
                "unit": "元",
                "category": "main_business",
                "segment_dimension": dimension,
                "mapping_ready": mapping_ready,
                "source_ref": source_ref,
                "source_label": "fina_mainbz",
            }
        )
    return normalized


class TushareFinancialFactsAdapter:
    def __init__(self, client: TushareClient | None = None) -> None:
        self.client = client or TushareClient()

    def resolve_ts_code(
        self,
        *,
        company: str,
        ts_code: str | None = None,
        report_path: Path | None = None,
        model_path: Path | None = None,
    ) -> str:
        if ts_code:
            return ts_code.upper()
        for path in (report_path, model_path):
            if path is None:
                continue
            full_match = EXCHANGE_CODE_RE.search(path.name)
            if full_match:
                return full_match.group("full").upper()
        symbol_hint = None
        for path in (report_path, model_path):
            if path is None:
                continue
            symbol_match = SYMBOL_RE.search(path.name)
            if symbol_match:
                symbol_hint = symbol_match.group("symbol")
                break
        basic_rows = _rows(
            self.client.stock_basic(exchange="", list_status="L", fields="ts_code,symbol,name")
        )
        if symbol_hint:
            for row in basic_rows:
                if str(row.get("symbol") or "").strip() == symbol_hint:
                    return str(row.get("ts_code") or "").strip().upper()
        company_clean = str(company or "").strip()
        for row in basic_rows:
            if str(row.get("name") or "").strip() == company_clean:
                return str(row.get("ts_code") or "").strip().upper()
        raise ValueError(f"unable to resolve ts_code for company={company_clean}")

    def extract(
        self,
        *,
        company: str,
        report_year: int,
        ts_code: str | None = None,
        report_path: Path | None = None,
        model_path: Path | None = None,
    ) -> dict[str, Any]:
        resolved_ts_code = self.resolve_ts_code(
            company=company,
            ts_code=ts_code,
            report_path=report_path,
            model_path=model_path,
        )
        period = f"{int(report_year)}1231"
        income_row = _first_row(self.client.income(ts_code=resolved_ts_code, period=period))
        indicator_row = _first_row(self.client.fina_indicator(ts_code=resolved_ts_code, period=period))
        mainbz_rows = _rows(self.client.fina_mainbz(ts_code=resolved_ts_code, period=period))

        revenue = _first_numeric(income_row, "total_revenue", "revenue", "oper_rev")
        oper_cost = _first_numeric(income_row, "oper_cost")
        gross_profit = None
        if revenue is not None and oper_cost is not None:
            gross_profit = revenue - oper_cost
        gross_margin = _first_numeric(indicator_row, "grossprofit_margin", "gross_margin", ratio=True)
        if gross_margin is None and gross_profit is not None and revenue not in {None, 0, 0.0}:
            gross_margin = gross_profit / revenue

        reported_facts = {
            "营业收入": revenue,
            "毛利": gross_profit,
            "毛利率": gross_margin,
            "归母净利润": _first_numeric(income_row, "n_income_attr_p", "netprofit_attr"),
            "扣非归母净利润": _first_numeric(indicator_row, "dt_netprofit"),
            "销售费用": _first_numeric(income_row, "sell_exp"),
            "管理费用": _first_numeric(income_row, "admin_exp"),
            "研发费用": _first_numeric(income_row, "rd_exp", "research_exp"),
            "财务费用": _first_numeric(income_row, "fin_exp"),
            "销售费用率（%）": _first_numeric(indicator_row, "saleexp_to_gr", ratio=True),
            "管理费用率（%）": _first_numeric(indicator_row, "adminexp_of_gr", ratio=True),
            "研发费用率（%）": _first_numeric(indicator_row, "rdexp_to_gr", "research_exp_to_gr", ratio=True),
            "财务费用率（%）": _first_numeric(indicator_row, "finaexp_to_gr", ratio=True),
            "所得税税率（%）": _first_numeric(indicator_row, "tax_to_ebt", "effective_tax_rate", ratio=True),
        }

        fact_items: list[dict[str, Any]] = []
        source_pairs = {
            "营业收入": ("亿元" if revenue is not None and abs(revenue) < 100000 else "元", f"tushare:income:{resolved_ts_code}:{period}", "income"),
            "毛利": ("亿元" if gross_profit is not None and abs(gross_profit) < 100000 else "元", f"tushare:income:{resolved_ts_code}:{period}", "income"),
            "毛利率": ("ratio", f"tushare:fina_indicator:{resolved_ts_code}:{period}", "fina_indicator"),
            "归母净利润": ("元", f"tushare:income:{resolved_ts_code}:{period}", "income"),
            "扣非归母净利润": ("元", f"tushare:fina_indicator:{resolved_ts_code}:{period}", "fina_indicator"),
            "销售费用": ("元", f"tushare:income:{resolved_ts_code}:{period}", "income"),
            "管理费用": ("元", f"tushare:income:{resolved_ts_code}:{period}", "income"),
            "研发费用": ("元", f"tushare:income:{resolved_ts_code}:{period}", "income"),
            "财务费用": ("元", f"tushare:income:{resolved_ts_code}:{period}", "income"),
            "销售费用率（%）": ("ratio", f"tushare:fina_indicator:{resolved_ts_code}:{period}", "fina_indicator"),
            "管理费用率（%）": ("ratio", f"tushare:fina_indicator:{resolved_ts_code}:{period}", "fina_indicator"),
            "研发费用率（%）": ("ratio", f"tushare:fina_indicator:{resolved_ts_code}:{period}", "fina_indicator"),
            "财务费用率（%）": ("ratio", f"tushare:fina_indicator:{resolved_ts_code}:{period}", "fina_indicator"),
            "所得税税率（%）": ("ratio", f"tushare:fina_indicator:{resolved_ts_code}:{period}", "fina_indicator"),
        }
        for metric, value in reported_facts.items():
            unit, source_ref, source_label = source_pairs[metric]
            item = _fact_item(
                metric=metric,
                value=value,
                unit=unit,
                source_ref=source_ref,
                source_label=source_label,
                note="tushare_structured_fact",
            )
            if item is not None:
                fact_items.append(item)

        mainbz_source_ref = f"tushare:fina_mainbz:{resolved_ts_code}:{period}"
        raw_segment_disclosure = [
            {
                "segment": str(row.get("bz_item") or "").strip(),
                "revenue": _first_numeric(row, "bz_sales", "sales", "revenue"),
                "gross_margin": None,
                "unit": "元",
                "category": "main_business",
                "source_ref": mainbz_source_ref,
                "source_label": "fina_mainbz",
            }
            for row in mainbz_rows
            if str(row.get("bz_item") or "").strip()
        ]
        segment_disclosure = _normalize_segment_disclosure_rows(
            mainbz_rows,
            source_ref=mainbz_source_ref,
        )

        return {
            "source_type": "tushare",
            "source_ref": f"tushare:{resolved_ts_code}:{period}",
            "company": company,
            "ts_code": resolved_ts_code,
            "report_period": period,
            "reported_facts": reported_facts,
            "fact_items": fact_items,
            "raw_segment_disclosure": raw_segment_disclosure,
            "segment_disclosure": segment_disclosure,
        }
