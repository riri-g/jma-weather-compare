"""
気象庁データ比較アプリ - FastAPI バックエンド
起動: uvicorn main:app --reload --port 8000
"""

from pathlib import Path
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

# ─── 観測地点リスト（地上気象観測所・日射量あり） ────────────────────
STATIONS = [
    # 北海道
    {"pref": "北海道", "name": "稚内",   "prec_no": "11", "block_no": "47401"},
    {"pref": "北海道", "name": "旭川",   "prec_no": "12", "block_no": "47407"},
    {"pref": "北海道", "name": "網走",   "prec_no": "13", "block_no": "47409"},
    {"pref": "北海道", "name": "札幌",   "prec_no": "14", "block_no": "47412"},
    {"pref": "北海道", "name": "帯広",   "prec_no": "16", "block_no": "47417"},
    {"pref": "北海道", "name": "釧路",   "prec_no": "17", "block_no": "47418"},
    {"pref": "北海道", "name": "室蘭",   "prec_no": "18", "block_no": "47423"},
    {"pref": "北海道", "name": "函館",   "prec_no": "15", "block_no": "47430"},
    # 東北
    {"pref": "青森県", "name": "青森",   "prec_no": "31", "block_no": "47575"},
    {"pref": "秋田県", "name": "秋田",   "prec_no": "32", "block_no": "47582"},
    {"pref": "岩手県", "name": "盛岡",   "prec_no": "33", "block_no": "47584"},
    {"pref": "宮城県", "name": "仙台",   "prec_no": "34", "block_no": "47590"},
    {"pref": "山形県", "name": "山形",   "prec_no": "35", "block_no": "47588"},
    {"pref": "福島県", "name": "福島",   "prec_no": "36", "block_no": "47595"},
    # 関東
    {"pref": "茨城県", "name": "水戸",   "prec_no": "40", "block_no": "47629"},
    {"pref": "栃木県", "name": "宇都宮", "prec_no": "41", "block_no": "47615"},
    {"pref": "群馬県", "name": "前橋",   "prec_no": "42", "block_no": "47624"},
    {"pref": "埼玉県", "name": "熊谷",   "prec_no": "43", "block_no": "47626"},
    {"pref": "東京都", "name": "東京",   "prec_no": "44", "block_no": "47662"},
    {"pref": "神奈川県","name": "横浜",  "prec_no": "46", "block_no": "47670"},
    {"pref": "千葉県", "name": "千葉",   "prec_no": "45", "block_no": "47682"},
    # 甲信越・北陸
    {"pref": "山梨県", "name": "甲府",   "prec_no": "49", "block_no": "47638"},
    {"pref": "長野県", "name": "長野",   "prec_no": "48", "block_no": "47610"},
    {"pref": "新潟県", "name": "新潟",   "prec_no": "54", "block_no": "47604"},
    {"pref": "富山県", "name": "富山",   "prec_no": "55", "block_no": "47607"},
    {"pref": "石川県", "name": "金沢",   "prec_no": "56", "block_no": "47605"},
    {"pref": "福井県", "name": "福井",   "prec_no": "57", "block_no": "47616"},
    # 東海
    {"pref": "静岡県", "name": "静岡",   "prec_no": "50", "block_no": "47656"},
    {"pref": "愛知県", "name": "名古屋", "prec_no": "51", "block_no": "47636"},
    {"pref": "岐阜県", "name": "岐阜",   "prec_no": "52", "block_no": "47632"},
    {"pref": "三重県", "name": "津",     "prec_no": "53", "block_no": "47651"},
    # 近畿
    {"pref": "滋賀県", "name": "彦根",   "prec_no": "60", "block_no": "47761"},
    {"pref": "京都府", "name": "京都",   "prec_no": "61", "block_no": "47759"},
    {"pref": "大阪府", "name": "大阪",   "prec_no": "62", "block_no": "47772"},
    {"pref": "兵庫県", "name": "神戸",   "prec_no": "63", "block_no": "47770"},
    {"pref": "奈良県", "name": "奈良",   "prec_no": "64", "block_no": "47780"},
    {"pref": "和歌山県","name": "和歌山","prec_no": "65", "block_no": "47777"},
    # 中国
    {"pref": "岡山県", "name": "岡山",   "prec_no": "66", "block_no": "47768"},
    {"pref": "広島県", "name": "広島",   "prec_no": "67", "block_no": "47765"},
    {"pref": "島根県", "name": "松江",   "prec_no": "68", "block_no": "47741"},
    {"pref": "鳥取県", "name": "鳥取",   "prec_no": "69", "block_no": "47747"},
    {"pref": "山口県", "name": "下関",   "prec_no": "81", "block_no": "47762"},
    # 四国
    {"pref": "徳島県", "name": "徳島",   "prec_no": "71", "block_no": "47895"},
    {"pref": "香川県", "name": "高松",   "prec_no": "72", "block_no": "47891"},
    {"pref": "愛媛県", "name": "松山",   "prec_no": "73", "block_no": "47887"},
    {"pref": "高知県", "name": "高知",   "prec_no": "74", "block_no": "47893"},
    # 九州
    {"pref": "福岡県", "name": "福岡",   "prec_no": "82", "block_no": "47807"},
    {"pref": "佐賀県", "name": "佐賀",   "prec_no": "83", "block_no": "47813"},
    {"pref": "長崎県", "name": "長崎",   "prec_no": "84", "block_no": "47817"},
    {"pref": "熊本県", "name": "熊本",   "prec_no": "85", "block_no": "47819"},
    {"pref": "大分県", "name": "大分",   "prec_no": "86", "block_no": "47815"},
    {"pref": "宮崎県", "name": "宮崎",   "prec_no": "87", "block_no": "47830"},
    {"pref": "鹿児島県","name": "鹿児島","prec_no": "88", "block_no": "47827"},
    # 沖縄
    {"pref": "沖縄県", "name": "那覇",   "prec_no": "91", "block_no": "47936"},
    {"pref": "沖縄県", "name": "石垣島", "prec_no": "94", "block_no": "47918"},
]


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


# フロントエンドを静的配信
_FRONTEND = Path(__file__).parent.parent / "frontend"

@app.get("/")
def index():
    return FileResponse(_FRONTEND / "index.html")

app.mount("/", StaticFiles(directory=str(_FRONTEND)), name="static")
