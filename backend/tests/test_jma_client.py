"""
jma_client モジュールの単体テスト。

テスト ID 対応:
  T-01: test_safe_float_*
  T-02: test_expand_headers_*
  T-03: test_find_col_*
  T-04: test_parse_monthly_table_*
  T-05: test_parse_daily_table_*
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
import jma_client
from jma_client import (
    _safe_float,
    _expand_headers,
    _find_col,
    _parse_monthly_table,
    _parse_daily_table,
)
from bs4 import BeautifulSoup
from tests.fixtures import (
    MONTHLY_HTML,
    NORMALS_HTML,
    DAILY_HTML,
    EMPTY_HTML,
    MONTHLY_WITH_COMMA_HTML,
)


# ────────────────────────────────────────────────────────────────
# T-01: _safe_float
# ────────────────────────────────────────────────────────────────

class TestSafeFloat:
    def test_normal_integer(self):
        assert _safe_float("5") == 5.0

    def test_normal_float(self):
        assert _safe_float("12.5") == 12.5

    def test_negative(self):
        assert _safe_float("-3.2") == -3.2

    def test_fullwidth_minus(self):
        # 気象庁は全角ハイフン「−」(U+2212) を使う
        assert _safe_float("−") is None

    def test_halfwidth_minus_only(self):
        assert _safe_float("-") is None

    def test_empty_string(self):
        assert _safe_float("") is None

    def test_whitespace(self):
        assert _safe_float("  ") is None

    def test_comma_separated(self):
        assert _safe_float("1,234.5") == 1234.5

    def test_negative_float(self):
        assert _safe_float("-0.5") == -0.5

    def test_with_trailing_spaces(self):
        assert _safe_float("  7.8  ") == 7.8

    def test_unicode_dash(self):
        # ‐ (U+2010) も欠損扱い
        assert _safe_float("‐") is None


# ────────────────────────────────────────────────────────────────
# T-02: _expand_headers
# ────────────────────────────────────────────────────────────────

class TestExpandHeaders:
    def _make_table(self, html: str):
        soup = BeautifulSoup(f"<table>{html}</table>", "html.parser")
        return soup.find("table")

    def test_simple_single_row(self):
        tbl = self._make_table("<tr><th>月</th><th>気温</th><th>降水量</th></tr>")
        headers = _expand_headers(tbl)
        assert headers == ["月", "気温", "降水量"]

    def test_rowspan(self):
        tbl = self._make_table(
            "<tr><th rowspan='2'>月</th><th>気温(℃)</th></tr>"
            "<tr><th>平均</th></tr>"
        )
        headers = _expand_headers(tbl)
        assert headers[0] == "月"
        assert "気温(℃)" in headers[1]
        assert "平均" in headers[1]

    def test_colspan(self):
        tbl = self._make_table(
            "<tr><th>月</th><th colspan='2'>気温(℃)</th></tr>"
            "<tr><th></th><th>平均</th><th>最高</th></tr>"
        )
        headers = _expand_headers(tbl)
        assert len(headers) == 3
        assert "平均" in headers[1]
        assert "最高" in headers[2]

    def test_no_header_rows_returns_empty(self):
        # データ行しかないテーブル
        tbl = self._make_table("<tr><td>1</td><td>5.4</td></tr>")
        assert _expand_headers(tbl) == []

    def test_monthly_html_columns(self):
        soup = BeautifulSoup(MONTHLY_HTML, "html.parser")
        tbl = soup.find("table")
        headers = _expand_headers(tbl)
        # 少なくとも「気温」「降水量」「日射量」を含む列が存在する
        joined = " ".join(headers)
        assert "気温" in joined
        assert "降水量" in joined
        assert "日射量" in joined


# ────────────────────────────────────────────────────────────────
# T-03: _find_col
# ────────────────────────────────────────────────────────────────

class TestFindCol:
    def test_finds_matching_column(self):
        headers = ["月", "気温(℃)_平均", "気温(℃)_最高", "降水量(mm)_合計"]
        assert _find_col(headers, ["気温", "平均"]) == 1

    def test_exclude_works(self):
        headers = ["月", "気温(℃)_平均", "気温(℃)_最高"]
        result = _find_col(headers, ["気温"], exclude=["最高"])
        assert result == 1

    def test_returns_none_when_not_found(self):
        headers = ["月", "気温(℃)_平均"]
        assert _find_col(headers, ["日射量"]) is None

    def test_multiple_must_keywords(self):
        headers = ["降水量(mm)_最大", "降水量(mm)_合計"]
        assert _find_col(headers, ["降水量", "合計"]) == 1

    def test_empty_headers(self):
        assert _find_col([], ["気温"]) is None


# ────────────────────────────────────────────────────────────────
# T-04: _parse_monthly_table
# ────────────────────────────────────────────────────────────────

class TestParseMonthlyTable:
    def test_returns_12_elements(self):
        result = _parse_monthly_table(MONTHLY_HTML)
        assert len(result["temp"]) == 12
        assert len(result["precip"]) == 12
        assert len(result["solar"]) == 12

    def test_parses_known_values(self):
        result = _parse_monthly_table(MONTHLY_HTML)
        assert result["temp"][0] == 5.4    # 1月
        assert result["temp"][1] == 6.1    # 2月
        assert result["precip"][0] == 80.5
        assert result["solar"][0] == 282.5

    def test_missing_months_are_none(self):
        result = _parse_monthly_table(MONTHLY_HTML)
        # 6〜12月は欠損
        for i in range(5, 12):
            assert result["temp"][i] is None
            assert result["precip"][i] is None

    def test_normals_html_all_months_present(self):
        result = _parse_monthly_table(NORMALS_HTML)
        assert all(v is not None for v in result["temp"])
        assert all(v is not None for v in result["precip"])

    def test_empty_html_returns_empty_dict(self):
        result = _parse_monthly_table(EMPTY_HTML)
        assert result == {}

    def test_comma_in_precip(self):
        result = _parse_monthly_table(MONTHLY_WITH_COMMA_HTML)
        # 1,234.5 が正しく 1234.5 にパースされること
        assert result["precip"][0] == 1234.5


# ────────────────────────────────────────────────────────────────
# T-05: _parse_daily_table
# ────────────────────────────────────────────────────────────────

class TestParseDailyTable:
    def test_returns_31_elements(self):
        result = _parse_daily_table(DAILY_HTML)
        assert len(result["temp"]) == 31
        assert len(result["precip"]) == 31
        assert len(result["solar"]) == 31

    def test_parses_known_values(self):
        result = _parse_daily_table(DAILY_HTML)
        assert result["temp"][0] == 12.5   # 1日
        assert result["temp"][1] == 13.2   # 2日
        assert result["precip"][1] == 5.5
        assert result["solar"][0] == 18.5

    def test_missing_days_are_none(self):
        result = _parse_daily_table(DAILY_HTML)
        # 4日以降は欠損
        for i in range(3, 31):
            assert result["temp"][i] is None

    def test_empty_html_returns_empty_dict(self):
        result = _parse_daily_table(EMPTY_HTML)
        assert result == {}


# ────────────────────────────────────────────────────────────────
# fetch_* の統合テスト（HTTP をモック）
# ────────────────────────────────────────────────────────────────

class TestFetchMonthly:
    def test_uses_s1_url_for_kisho(self):
        with patch("jma_client._fetch", return_value=MONTHLY_HTML) as mock_fetch:
            jma_client._CACHE.clear()
            result = jma_client.fetch_monthly("44", "47662", 2026)
            url = mock_fetch.call_args[0][0]
            assert "monthly_s1.php" in url
            assert result["temp"][0] == 5.4

    def test_uses_a1_url_for_amedas(self):
        with patch("jma_client._fetch", return_value=MONTHLY_HTML) as mock_fetch:
            jma_client._CACHE.clear()
            result = jma_client.fetch_monthly("43", "0363", 2026)
            url = mock_fetch.call_args[0][0]
            assert "monthly_a1.php" in url

    def test_result_is_cached(self):
        with patch("jma_client._fetch", return_value=MONTHLY_HTML) as mock_fetch:
            jma_client._CACHE.clear()
            jma_client.fetch_monthly("44", "47662", 2025)
            jma_client.fetch_monthly("44", "47662", 2025)
            assert mock_fetch.call_count == 1


class TestFetchDaily:
    def test_uses_s1_url_for_kisho(self):
        with patch("jma_client._fetch", return_value=DAILY_HTML) as mock_fetch:
            jma_client._CACHE.clear()
            jma_client.fetch_daily("44", "47662", 2026, 4)
            url = mock_fetch.call_args[0][0]
            assert "daily_s1.php" in url
            assert "month=04" in url

    def test_uses_a1_url_for_amedas(self):
        with patch("jma_client._fetch", return_value=DAILY_HTML) as mock_fetch:
            jma_client._CACHE.clear()
            jma_client.fetch_daily("43", "0363", 2026, 4)
            url = mock_fetch.call_args[0][0]
            assert "daily_a1.php" in url


class TestFetchNormals:
    def test_uses_sfc_url_for_kisho(self):
        with patch("jma_client._fetch", return_value=NORMALS_HTML) as mock_fetch:
            jma_client._CACHE.clear()
            jma_client.fetch_normals("44", "47662")
            url = mock_fetch.call_args[0][0]
            assert "nml_sfc_ym.php" in url

    def test_uses_amd_url_for_amedas(self):
        with patch("jma_client._fetch", return_value=NORMALS_HTML) as mock_fetch:
            jma_client._CACHE.clear()
            jma_client.fetch_normals("43", "0363")
            url = mock_fetch.call_args[0][0]
            assert "nml_amd_ym.php" in url
