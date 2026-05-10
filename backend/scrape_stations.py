"""
気象庁 ETRN から全国の観測地点一覧を取得するスクリプト。
実行: python backend/scrape_stations.py
出力: backend/stations_all.py (STATIONS リスト)
"""

import re
import sys
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

PREC_NOS = [
    11, 12, 13, 14, 15, 16, 17, 18,        # 北海道
    31, 32, 33, 34, 35, 36,                 # 東北
    40, 41, 42, 43, 44, 45, 46, 48, 49,    # 関東・甲信越
    50, 51, 52, 53, 54, 55, 56, 57,        # 東海・北陸
    60, 61, 62, 63, 64, 65,                # 近畿
    66, 67, 68, 69,                        # 中国
    71, 72, 73, 74,                        # 四国
    81, 82, 83, 84, 85, 86, 87, 88,        # 九州
    91, 92, 93, 94,                        # 沖縄
]

PREC_TO_PREF = {
    11: "北海道", 12: "北海道", 13: "北海道", 14: "北海道",
    15: "北海道", 16: "北海道", 17: "北海道", 18: "北海道",
    31: "青森県", 32: "秋田県", 33: "岩手県", 34: "宮城県",
    35: "山形県", 36: "福島県",
    40: "茨城県", 41: "栃木県", 42: "群馬県", 43: "埼玉県",
    44: "東京都", 45: "千葉県", 46: "神奈川県",
    48: "長野県", 49: "山梨県",
    50: "静岡県", 51: "愛知県", 52: "岐阜県", 53: "三重県",
    54: "新潟県", 55: "富山県", 56: "石川県", 57: "福井県",
    60: "滋賀県", 61: "京都府", 62: "大阪府", 63: "兵庫県",
    64: "奈良県", 65: "和歌山県",
    66: "岡山県", 67: "広島県", 68: "島根県", 69: "鳥取県",
    71: "徳島県", 72: "香川県", 73: "愛媛県", 74: "高知県",
    81: "山口県", 82: "福岡県", 83: "佐賀県", 84: "長崎県",
    85: "熊本県", 86: "大分県", 87: "宮崎県", 88: "鹿児島県",
    91: "沖縄県", 92: "沖縄県", 93: "沖縄県", 94: "沖縄県",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
}


def scrape_prec(prec_no: int) -> list[dict]:
    url = (
        f"https://www.data.jma.go.jp/obd/stats/etrn/select/prefecture.php"
        f"?prec_no={prec_no}"
    )
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        r = client.get(url, headers=HEADERS)
        r.raise_for_status()
        r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, "html.parser")
    stations = []
    seen = set()

    for area in soup.find_all("area"):
        href = area.get("href", "")
        alt  = area.get("alt", "").strip()
        if not alt:
            continue

        m_block = re.search(r"block_no=(\w+)", href)
        if not m_block:
            continue
        block_no = m_block.group(1)

        m_prec = re.search(r"prec_no=(\d+)", href)
        if not m_prec:
            continue
        href_prec = int(m_prec.group(1))

        # 別のprec_noへのリンク（隣接局）はスキップ
        if href_prec != prec_no:
            continue

        key = (prec_no, block_no)
        if key in seen:
            continue
        seen.add(key)

        pref = PREC_TO_PREF.get(prec_no, f"prec{prec_no}")
        stations.append({
            "pref":     pref,
            "name":     alt,
            "prec_no":  str(prec_no),
            "block_no": block_no,
        })

    return stations


def main():
    all_stations = []
    for prec_no in PREC_NOS:
        print(f"prec_no={prec_no:2d} ({PREC_TO_PREF.get(prec_no, '?')}) ... ", end="", flush=True)
        try:
            result = scrape_prec(prec_no)
            all_stations.extend(result)
            print(f"{len(result)} 局")
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
        time.sleep(1.5)

    # 出力ファイルに書き出す
    out = Path(__file__).parent / "stations_all.py"
    lines = ["STATIONS = [\n"]
    for s in all_stations:
        lines.append(
            f'    {{"pref": "{s["pref"]}", "name": "{s["name"]}", '
            f'"prec_no": "{s["prec_no"]}", "block_no": "{s["block_no"]}"}},\n'
        )
    lines.append("]\n")

    out.write_text("".join(lines), encoding="utf-8")
    print(f"\n合計 {len(all_stations)} 局 → {out}")


if __name__ == "__main__":
    main()
