"""
観測地点の緯度経度を Nominatim (OpenStreetMap) で取得し stations_geo.json を生成する。

実行方法:
    python backend/build_geo.py

所要時間: 約 30〜40 分（レートリミット 1 req/s のため）
出力:    backend/stations_geo.json
"""

import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from stations_all import STATIONS

OUT = Path(__file__).parent / "stations_geo.json"
HEADERS = {"User-Agent": "jma-weather-compare/1.0 (educational project)"}
INTERVAL = 1.1  # Nominatim: max 1 req/sec


def geocode(name: str, pref: str) -> tuple[float | None, float | None]:
    """Nominatim で観測地点名＋都道府県を検索して (lat, lon) を返す。"""
    # 観測所名で検索（「気象台」「測候所」「観測所」を除いた地名部分）
    q = f"{name} {pref} 日本"
    try:
        r = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 1, "countrycodes": "jp"},
            headers=HEADERS,
            timeout=10,
        )
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"    ERROR: {e}")
    return None, None


def main():
    # 既存ファイルがあれば読み込んで追記モードで動かす（中断・再開対応）
    existing: dict = {}
    if OUT.exists():
        existing = json.loads(OUT.read_text(encoding="utf-8"))
        print(f"既存データ: {len(existing)} 件")

    result = dict(existing)
    skipped = 0

    for i, s in enumerate(STATIONS):
        key = f"{s['prec_no']}|{s['block_no']}"
        if key in result:
            skipped += 1
            continue

        pref = s["pref"]
        name = s["name"]
        print(f"[{i + 1}/{len(STATIONS)}] {pref} {name} ... ", end="", flush=True)

        lat, lon = geocode(name, pref)
        if lat is not None:
            result[key] = {"lat": round(lat, 5), "lon": round(lon, 5)}
            print(f"{lat:.4f}, {lon:.4f}")
        else:
            print("見つからず")

        # 途中保存（100 件ごと）
        if (i + 1) % 100 == 0:
            OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  → 中間保存: {len(result)} 件")

        time.sleep(INTERVAL)

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n完了: {len(result)} 件 (スキップ {skipped} 件) → {OUT}")


if __name__ == "__main__":
    main()
