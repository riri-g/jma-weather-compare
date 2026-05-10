"""
気象庁 ETRN からデータを取得・解析するモジュール。
- monthly_s1.php  : 年別・月別の観測値（気温・降水量・日射量など）
- nml_sfc_ym.php  : 平年値（1991-2020年平均）
"""

import re
import time
from typing import Optional
import httpx
from bs4 import BeautifulSoup, Tag

_CACHE: dict[str, tuple[float, object]] = {}
_CACHE_TTL_SHORT = 3600   # 観測値: 1時間
_CACHE_TTL_LONG  = 86400  # 平年値: 24時間

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
}


def _cached(key: str, ttl: float, fn):
    if key in _CACHE:
        ts, val = _CACHE[key]
        if time.time() - ts < ttl:
            return val
    val = fn()
    _CACHE[key] = (time.time(), val)
    return val


def _fetch(url: str) -> str:
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        r = client.get(url, headers=_HEADERS)
        r.raise_for_status()
        r.encoding = "utf-8"
        return r.text


def _safe_float(text: str) -> Optional[float]:
    """セルのテキストを float に変換。欠損は None。"""
    v = text.strip().replace(",", "").replace("−", "-").replace("‐", "-")
    v = re.sub(r"[^0-9.\-]", "", v)
    try:
        return float(v) if v not in ("", "-") else None
    except ValueError:
        return None


def _expand_headers(table: Tag) -> list[str]:
    """
    複数行ヘッダー（rowspan/colspan あり）を1次元の列名リストに展開する。
    例: 「降水量(mm) / 合計」→ "降水量(mm)_合計"
    データ行（th+td 混在）は含めず、純粋なヘッダー行（全セルが th）のみ対象。
    """
    rows = [r for r in table.find_all("tr")
            if r.find_all(["th", "td"]) and not r.find("td")]
    if not rows:
        return []

    # 最大列数を把握
    max_cols = 0
    for row in rows:
        cols = sum(int(c.get("colspan", 1)) for c in row.find_all(["th", "td"]))
        max_cols = max(max_cols, cols)

    # グリッドに配置
    grid: list[list[str]] = [[""] * max_cols for _ in rows]
    occupied: set[tuple[int, int]] = set()

    for ri, row in enumerate(rows):
        ci = 0
        for cell in row.find_all(["th", "td"]):
            while (ri, ci) in occupied:
                ci += 1
            text = cell.get_text(strip=True)
            rs = int(cell.get("rowspan", 1))
            cs = int(cell.get("colspan", 1))
            for dr in range(rs):
                for dc in range(cs):
                    r_, c_ = ri + dr, ci + dc
                    if r_ < len(rows):
                        grid[r_][c_] = text
                    occupied.add((r_, c_))
            ci += cs

    # 各列の名前 = 上のセルを "_" で連結（重複部分は省く）
    result = []
    for ci in range(max_cols):
        parts = []
        for ri in range(len(rows)):
            v = grid[ri][ci]
            if v and v not in parts:
                parts.append(v)
        result.append("_".join(parts))
    return result


def _find_col(headers: list[str], must: list[str], exclude: list[str] = []) -> Optional[int]:
    """must キーワードをすべて含み、exclude キーワードを含まない列インデックスを返す。"""
    for i, h in enumerate(headers):
        if all(k in h for k in must) and not any(k in h for k in exclude):
            return i
    return None


def _parse_monthly_table(html: str) -> dict:
    """
    HTML から月別観測値を解析する。
    戻り値: {"temp": [...], "precip": [...], "solar": [...]}  各 12 要素（月順、欠損 None）
    """
    soup = BeautifulSoup(html, "html.parser")

    # データテーブルを探す（気温・降水量・日射量を含む最大のテーブル）
    target = None
    for tbl in soup.find_all("table"):
        text = tbl.get_text()
        if "降水量" in text and "気温" in text:
            target = tbl
            break

    if target is None:
        return {}

    headers = _expand_headers(target)

    temp_col   = _find_col(headers, ["気温", "平均"],  exclude=["最高", "最低", "露点", "湿球"])
    precip_col = _find_col(headers, ["降水量", "合計"], exclude=["最大", "最長"])
    solar_col  = _find_col(headers, ["日射量"])

    temp   = [None] * 12
    precip = [None] * 12
    solar  = [None] * 12

    for row in target.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 3:
            continue
        # 純粋なヘッダー行（全て th）はスキップ
        if all(c.name == "th" for c in cells):
            continue
        # 先頭セルが月番号か確認（「1」または「1月」形式に対応）
        m = re.match(r"^\s*(\d{1,2})\s*月?\s*$", cells[0].get_text())
        if not m:
            continue
        month = int(m.group(1))
        if not (1 <= month <= 12):
            continue
        idx = month - 1

        def val(col):
            if col is None or col >= len(cells):
                return None
            return _safe_float(cells[col].get_text())

        temp[idx]   = val(temp_col)
        precip[idx] = val(precip_col)
        solar[idx]  = val(solar_col)

    return {"temp": temp, "precip": precip, "solar": solar}


def _parse_normal_table(html: str) -> dict:
    """
    平年値ページ（nml_sfc_ym.php）を解析する。
    戻り値は _parse_monthly_table と同形式。
    """
    return _parse_monthly_table(html)


def _parse_daily_table(html: str) -> dict:
    """
    日別観測値ページ（daily_s1.php / daily_a1.php）を解析する。
    戻り値: {"temp": [...], "precip": [...], "solar": [...]}  各 31 要素（欠損 None）
    """
    soup = BeautifulSoup(html, "html.parser")

    target = None
    for tbl in soup.find_all("table"):
        text = tbl.get_text()
        if "降水量" in text and "気温" in text:
            target = tbl
            break

    if target is None:
        return {}

    headers = _expand_headers(target)

    temp_col   = _find_col(headers, ["気温", "平均"],  exclude=["最高", "最低", "露点", "湿球"])
    precip_col = _find_col(headers, ["降水量", "合計"], exclude=["最大", "最長", "10分", "1時間"])
    solar_col  = _find_col(headers, ["日射量"])

    temp   = [None] * 31
    precip = [None] * 31
    solar  = [None] * 31

    for row in target.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 3:
            continue
        if all(c.name == "th" for c in cells):
            continue
        m = re.match(r"^\s*(\d{1,2})\s*日?\s*$", cells[0].get_text())
        if not m:
            continue
        day = int(m.group(1))
        if not (1 <= day <= 31):
            continue
        idx = day - 1

        def val(col):
            if col is None or col >= len(cells):
                return None
            return _safe_float(cells[col].get_text())

        temp[idx]   = val(temp_col)
        precip[idx] = val(precip_col)
        solar[idx]  = val(solar_col)

    return {"temp": temp, "precip": precip, "solar": solar}


# ─── 公開 API ────────────────────────────────────────────────

def fetch_monthly(prec_no: str, block_no: str, year: int) -> dict:
    is_amedas = not block_no.startswith("47")
    if is_amedas:
        url = (
            f"https://www.data.jma.go.jp/obd/stats/etrn/view/monthly_a1.php"
            f"?prec_no={prec_no}&block_no={block_no}&year={year}&month=&day=&view="
        )
    else:
        url = (
            f"https://www.data.jma.go.jp/obd/stats/etrn/view/monthly_s1.php"
            f"?prec_no={prec_no}&block_no={block_no}&year={year}&month=&day=&view="
        )
    key = f"monthly:{prec_no}:{block_no}:{year}"
    return _cached(key, _CACHE_TTL_SHORT, lambda: _parse_monthly_table(_fetch(url)))


def fetch_daily(prec_no: str, block_no: str, year: int, month: int) -> dict:
    is_amedas = not block_no.startswith("47")
    if is_amedas:
        url = (
            f"https://www.data.jma.go.jp/obd/stats/etrn/view/daily_a1.php"
            f"?prec_no={prec_no}&block_no={block_no}&year={year}&month={month:02d}&day=&view="
        )
    else:
        url = (
            f"https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php"
            f"?prec_no={prec_no}&block_no={block_no}&year={year}&month={month:02d}&day=&view="
        )
    key = f"daily:{prec_no}:{block_no}:{year}:{month}"
    return _cached(key, _CACHE_TTL_SHORT, lambda: _parse_daily_table(_fetch(url)))


def fetch_normals(prec_no: str, block_no: str) -> dict:
    is_amedas = not block_no.startswith("47")
    if is_amedas:
        url = (
            f"https://www.data.jma.go.jp/obd/stats/etrn/view/nml_amd_ym.php"
            f"?prec_no={prec_no}&block_no={block_no}&view="
        )
    else:
        url = (
            f"https://www.data.jma.go.jp/obd/stats/etrn/view/nml_sfc_ym.php"
            f"?prec_no={prec_no}&block_no={block_no}&view="
        )
    key = f"normal:{prec_no}:{block_no}"
    return _cached(key, _CACHE_TTL_LONG, lambda: _parse_normal_table(_fetch(url)))
