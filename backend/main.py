"""
気象庁データ比較アプリ - FastAPI バックエンド
起動: uvicorn main:app --reload --port 8000
"""

import sys
from pathlib import Path

# backend/ ディレクトリを import パスに追加（どこから起動しても jma_client を見つけられるようにする）
sys.path.insert(0, str(Path(__file__).parent))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import jma_client

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
