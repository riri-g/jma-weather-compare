@echo off
chcp 65001 > nul
echo =========================================
echo  気象庁データ比較アプリ 起動中...
echo =========================================
echo.
echo バックエンドサーバーを起動しています（ポート 8000）
echo 起動後、ブラウザで http://localhost:8000 を開いてください。
echo 終了するには Ctrl+C を押してください。
echo.
cd /d "%~dp0backend"
python -m uvicorn main:app --port 8000 --reload
pause
