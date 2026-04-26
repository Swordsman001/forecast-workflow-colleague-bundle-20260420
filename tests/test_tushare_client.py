import sys
import tempfile
import types
import unittest
from pathlib import Path
import subprocess
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.data_sources.tushare_client import TushareClient, load_tushare_token  # type: ignore
from scripts.tushare_smoke_test import build_smoke_result  # type: ignore


class TushareClientTests(unittest.TestCase):
    def test_load_tushare_token_reads_token_from_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / "config.env"
            env_path.write_text("TUSHARE_TOKEN=test-token\n", encoding="utf-8")

            token = load_tushare_token(env_path)

            self.assertEqual(token, "test-token")

    def test_load_tushare_token_rejects_missing_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / "config.env"
            env_path.write_text("FEISHU_WEBHOOK=\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_tushare_token(env_path)

    def test_client_initializes_sdk_with_token(self) -> None:
        fake_pro = mock.Mock()
        fake_ts = types.SimpleNamespace(
            set_token=mock.Mock(),
            pro_api=mock.Mock(return_value=fake_pro),
            pro_bar=mock.Mock(),
        )

        client = TushareClient(token="abc123", ts_module=fake_ts)

        self.assertIs(client.pro_client, fake_pro)
        fake_ts.set_token.assert_called_once_with("abc123")
        fake_ts.pro_api.assert_called_once_with()

    def test_income_delegates_to_pro_client(self) -> None:
        fake_pro = mock.Mock()
        fake_pro.income.return_value = "income-data"
        fake_ts = types.SimpleNamespace(
            set_token=mock.Mock(),
            pro_api=mock.Mock(return_value=fake_pro),
            pro_bar=mock.Mock(),
        )
        client = TushareClient(token="abc123", ts_module=fake_ts)

        result = client.income(ts_code="600519.SH", period="20241231")

        self.assertEqual(result, "income-data")
        fake_pro.income.assert_called_once_with(ts_code="600519.SH", period="20241231")

    def test_pro_bar_uses_module_level_helper(self) -> None:
        fake_ts = types.SimpleNamespace(
            set_token=mock.Mock(),
            pro_api=mock.Mock(return_value=mock.Mock()),
            pro_bar=mock.Mock(return_value="bar-data"),
        )
        client = TushareClient(token="abc123", ts_module=fake_ts)

        result = client.pro_bar(ts_code="600519.SH", start_date="20260101", end_date="20260131", freq="D")

        self.assertEqual(result, "bar-data")
        fake_ts.pro_bar.assert_called_once_with(
            ts_code="600519.SH",
            start_date="20260101",
            end_date="20260131",
            freq="D",
        )

    def test_build_smoke_result_uses_requested_api(self) -> None:
        fake_df = mock.Mock()
        fake_df.columns.tolist.return_value = ["trade_date", "is_open"]
        fake_df.head.return_value.to_dict.return_value = [{"trade_date": "20260401", "is_open": 1}]
        fake_df.__len__ = mock.Mock(return_value=1)
        fake_client = mock.Mock()
        fake_client.trade_cal.return_value = fake_df

        result = build_smoke_result(
            client=fake_client,
            api_name="trade_cal",
            ts_code=None,
            start_date="20260401",
            end_date="20260410",
            limit=3,
        )

        fake_client.trade_cal.assert_called_once_with(start_date="20260401", end_date="20260410")
        self.assertEqual(result["api_name"], "trade_cal")
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["columns"], ["trade_date", "is_open"])

    def test_smoke_script_help_runs_as_direct_script(self) -> None:
        script_path = ROOT / "scripts" / "tushare_smoke_test.py"

        completed = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--api", completed.stdout)


if __name__ == "__main__":
    unittest.main()
