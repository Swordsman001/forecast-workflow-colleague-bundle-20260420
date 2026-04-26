# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import dotenv_values


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.env"


def load_tushare_token(env_path: Path | str | None = None) -> str:
    config_path = Path(env_path) if env_path is not None else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    config = dotenv_values(config_path)
    token = str(config.get("TUSHARE_TOKEN") or "").strip()
    if not token:
        raise ValueError("config.env 中缺少 TUSHARE_TOKEN")
    return token


class TushareClient:
    def __init__(
        self,
        token: str | None = None,
        env_path: Path | str | None = None,
        ts_module: Any | None = None,
    ) -> None:
        self._token = (token or "").strip() or load_tushare_token(env_path)
        self._ts_module = ts_module
        self._pro_client = None

    def _get_ts_module(self) -> Any:
        if self._ts_module is None:
            import tushare as ts

            self._ts_module = ts
        return self._ts_module

    @property
    def pro_client(self) -> Any:
        if self._pro_client is None:
            ts = self._get_ts_module()
            ts.set_token(self._token)
            self._pro_client = ts.pro_api()
        return self._pro_client

    def _call_pro(self, method_name: str, **kwargs: Any) -> Any:
        method = getattr(self.pro_client, method_name)
        return method(**kwargs)

    def query(self, api_name: str, **kwargs: Any) -> Any:
        return self.pro_client.query(api_name, **kwargs)

    def stock_basic(self, **kwargs: Any) -> Any:
        return self._call_pro("stock_basic", **kwargs)

    def stock_company(self, **kwargs: Any) -> Any:
        return self._call_pro("stock_company", **kwargs)

    def income(self, **kwargs: Any) -> Any:
        return self._call_pro("income", **kwargs)

    def balancesheet(self, **kwargs: Any) -> Any:
        return self._call_pro("balancesheet", **kwargs)

    def cashflow(self, **kwargs: Any) -> Any:
        return self._call_pro("cashflow", **kwargs)

    def fina_indicator(self, **kwargs: Any) -> Any:
        return self._call_pro("fina_indicator", **kwargs)

    def forecast(self, **kwargs: Any) -> Any:
        return self._call_pro("forecast", **kwargs)

    def express(self, **kwargs: Any) -> Any:
        return self._call_pro("express", **kwargs)

    def fina_mainbz(self, **kwargs: Any) -> Any:
        return self._call_pro("fina_mainbz", **kwargs)

    def dividend(self, **kwargs: Any) -> Any:
        return self._call_pro("dividend", **kwargs)

    def trade_cal(self, **kwargs: Any) -> Any:
        return self._call_pro("trade_cal", **kwargs)

    def daily(self, **kwargs: Any) -> Any:
        return self._call_pro("daily", **kwargs)

    def weekly(self, **kwargs: Any) -> Any:
        return self._call_pro("weekly", **kwargs)

    def monthly(self, **kwargs: Any) -> Any:
        return self._call_pro("monthly", **kwargs)

    def daily_basic(self, **kwargs: Any) -> Any:
        return self._call_pro("daily_basic", **kwargs)

    def adj_factor(self, **kwargs: Any) -> Any:
        return self._call_pro("adj_factor", **kwargs)

    def moneyflow(self, **kwargs: Any) -> Any:
        return self._call_pro("moneyflow", **kwargs)

    def pro_bar(self, **kwargs: Any) -> Any:
        ts = self._get_ts_module()
        return ts.pro_bar(**kwargs)
