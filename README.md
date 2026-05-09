# 気象庁データ比較アプリ

指定した観測地点の **今年の気温・降水量・日射量** を **平年値（1991-2020年平均）** と比較できる Web アプリです。

🌐 **公開URL**: https://jma-weather-compare.onrender.com

## 機能

- 全国 55 観測地点から地点を選択
- 年を指定して今年以外の年も表示可能
- 気温・降水量・日射量を平年値と並べてグラフ表示
- 月ごとの平年差（偏差）をバーグラフで表示
- 年合計・年平均と平年比をサマリーカードで確認

## データソース

[気象庁 統計情報（ETRN）](https://www.data.jma.go.jp/obd/stats/etrn/) より取得

- 観測値: `monthly_s1.php`（月別値）
- 平年値: `nml_sfc_ym.php`（1991-2020年平均）

## 技術構成

| 役割 | 技術 |
|------|------|
| バックエンド | Python / FastAPI |
| データ取得 | httpx + BeautifulSoup4 |
| フロントエンド | HTML / CSS / JavaScript |
| グラフ描画 | Chart.js |
| ホスティング | Render |

## ローカルで動かす

### 必要なもの
- Python 3.10 以上

### 手順

```bash
# リポジトリをクローン
git clone https://github.com/riri-g/jma-weather-compare.git
cd jma-weather-compare

# 依存パッケージをインストール
pip install -r requirements.txt

# サーバーを起動
uvicorn backend.main:app --port 8000 --reload
```

ブラウザで http://localhost:8000 を開く。

Windows の場合は `start.bat` をダブルクリックするだけで起動できます。

## ファイル構成

```
jma-weather-compare/
├── backend/
│   ├── main.py          # FastAPI サーバー・API エンドポイント
│   ├── jma_client.py    # 気象庁データ取得・HTML解析
│   └── requirements.txt
├── frontend/
│   ├── index.html       # 画面構造
│   ├── app.js           # グラフ描画・API呼び出し
│   └── style.css        # スタイル
├── requirements.txt
├── Procfile             # Render 用起動設定
└── start.bat            # Windows ローカル起動用
```
