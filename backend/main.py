"""
気象庁データ比較アプリ - FastAPI バックエンド
起動: uvicorn main:app --reload --port 8000
"""

import json
import sys
from pathlib import Path

# backend/ ディレクトリを import パスに追加（どこから起動しても jma_client を見つけられるようにする）
sys.path.insert(0, str(Path(__file__).parent))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import jma_client

# 都道府県中心座標（stations_geo.json がない場合のフォールバック）
_PREF_CENTROIDS: dict[str, tuple[float, float]] = {
    "北海道": (43.06, 141.35), "青森県": (40.82, 140.74), "岩手県": (39.70, 141.15),
    "宮城県": (38.27, 140.87), "秋田県": (39.72, 140.10), "山形県": (38.24, 140.36),
    "福島県": (37.75, 140.47), "茨城県": (36.34, 140.45), "栃木県": (36.56, 139.88),
    "群馬県": (36.39, 139.06), "埼玉県": (35.86, 139.65), "千葉県": (35.61, 140.12),
    "東京都": (35.69, 139.69), "神奈川県": (35.45, 139.64), "新潟県": (37.90, 139.02),
    "富山県": (36.70, 137.21), "石川県": (36.59, 136.63), "福井県": (36.07, 136.22),
    "山梨県": (35.66, 138.57), "長野県": (36.65, 138.18), "静岡県": (34.98, 138.38),
    "愛知県": (35.18, 136.91), "三重県": (34.73, 136.51), "滋賀県": (35.00, 135.87),
    "京都府": (35.02, 135.76), "大阪府": (34.69, 135.50), "兵庫県": (34.69, 135.18),
    "奈良県": (34.68, 135.83), "和歌山県": (34.23, 135.17), "鳥取県": (35.50, 134.24),
    "島根県": (35.47, 133.05), "岡山県": (34.66, 133.93), "広島県": (34.40, 132.46),
    "山口県": (34.19, 131.47), "徳島県": (34.07, 134.55), "香川県": (34.34, 134.04),
    "愛媛県": (33.84, 132.77), "高知県": (33.56, 133.53), "福岡県": (33.61, 130.42),
    "佐賀県": (33.25, 130.30), "長崎県": (32.74, 129.87), "熊本県": (32.79, 130.74),
    "大分県": (33.24, 131.61), "宮崎県": (31.91, 131.42), "鹿児島県": (31.56, 130.56),
    "沖縄県": (26.21, 127.68),
}

app = FastAPI(title="JMA Weather Compare")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ─── 観測地点リスト（scrape_stations.py で生成した stations_all.py から読み込み） ─
from stations_all import STATIONS as _ALL_STATIONS
STATIONS = [s for s in _ALL_STATIONS if s["block_no"] != "00"]



@app.get("/api/stations")
def get_stations():
    return STATIONS


@app.get("/api/stations-geo")
def get_stations_geo():
    """緯度経度付きの観測地点一覧を返す。
    stations_geo.json が存在すればそこから正確な座標を、
    なければ都道府県中心座標をフォールバックとして使用する。"""
    geo_file = Path(__file__).parent / "stations_geo.json"
    geo: dict = {}
    if geo_file.exists():
        try:
            geo = json.loads(geo_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    result = []
    for s in STATIONS:
        key = f"{s['prec_no']}|{s['block_no']}"
        coords = geo.get(key)
        if coords:
            result.append({**s, "lat": coords["lat"], "lon": coords["lon"], "exact": True})
        elif s["pref"] in _PREF_CENTROIDS:
            lat, lon = _PREF_CENTROIDS[s["pref"]]
            result.append({**s, "lat": lat, "lon": lon, "exact": False})
    return result


@app.get("/api/climate")
def get_climate(prec_no: str, block_no: str, year: int = 2026):
    # 対象局の名前を解決
    station = next(
        (s for s in STATIONS if s["prec_no"] == prec_no and s["block_no"] == block_no),
        None,
    )
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")

    try:
        current = jma_client.fetch_monthly(prec_no, block_no, year)
        normals = jma_client.fetch_normals(prec_no, block_no)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"気象庁からのデータ取得に失敗しました: {e}")

    if not current and not normals:
        raise HTTPException(status_code=404, detail="データが取得できませんでした")

    return {
        "station": station["name"],
        "pref": station["pref"],
        "prec_no": prec_no,
        "block_no": block_no,
        "year": year,
        "months": list(range(1, 13)),
        "current": current,
        "normals": normals,
    }


@app.get("/api/daily")
def get_daily(prec_no: str, block_no: str, year: int, month: int):
    station = next(
        (s for s in STATIONS if s["prec_no"] == prec_no and s["block_no"] == block_no),
        None,
    )
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="month must be 1-12")

    try:
        daily   = jma_client.fetch_daily(prec_no, block_no, year, month)
        normals = jma_client.fetch_normals(prec_no, block_no)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"気象庁からのデータ取得に失敗しました: {e}")

    if not daily and not normals:
        raise HTTPException(status_code=404, detail="データが取得できませんでした")

    return {
        "station": station["name"],
        "pref":    station["pref"],
        "prec_no": prec_no,
        "block_no": block_no,
        "year":    year,
        "month":   month,
        "current": daily,
        "normals": normals,
    }


@app.get("/api/range")
def get_range(prec_no: str, block_no: str, start: str, end: str):
    """期間指定の日別データを返す。start/end は YYYY-MM-DD 形式。"""
    from datetime import date as _date

    station = next(
        (s for s in STATIONS if s["prec_no"] == prec_no and s["block_no"] == block_no),
        None,
    )
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")

    try:
        sy, sm, sd = map(int, start.split("-"))
        ey, em, ed = map(int, end.split("-"))
    except Exception:
        raise HTTPException(status_code=400, detail="start/end は YYYY-MM-DD 形式で指定してください")

    try:
        if _date(sy, sm, sd) > _date(ey, em, ed):
            raise HTTPException(status_code=400, detail="start は end より前の日付を指定してください")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日付が無効です: {e}")

    try:
        data    = jma_client.fetch_range(prec_no, block_no, sy, sm, sd, ey, em, ed)
        normals = jma_client.fetch_normals(prec_no, block_no)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"気象庁からのデータ取得に失敗しました: {e}")

    return {
        "station": station["name"],
        "pref":    station["pref"],
        "prec_no": prec_no,
        "block_no": block_no,
        "start":   start,
        "end":     end,
        "current": data,
        "normals": normals,
    }


# フロントエンドを静的配信
_FRONTEND = Path(__file__).parent.parent / "frontend"

@app.get("/")
def index():
    return FileResponse(_FRONTEND / "index.html")

app.mount("/", StaticFiles(directory=str(_FRONTEND)), name="static")
