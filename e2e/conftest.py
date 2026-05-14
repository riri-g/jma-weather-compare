"""
E2E テスト用フィクスチャ。
バックエンドサーバーを起動してテストを実行する。
"""

import subprocess
import time
import sys
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright, Browser, Page


BACKEND_DIR = Path(__file__).parent.parent / "backend"
# app.js が `location.hostname === 'localhost'` のとき 8000 番を使うので合わせる
BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def backend_server():
    """テスト用バックエンドサーバーを起動・終了する。"""
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "main:app",
            "--port", "8000",
            "--host", "127.0.0.1",
        ],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # 起動を待つ
    import httpx
    for _ in range(30):
        try:
            httpx.get(f"{BASE_URL}/api/stations", timeout=2)
            break
        except Exception:
            time.sleep(0.5)
    else:
        proc.kill()
        pytest.fail("バックエンドサーバーが起動しませんでした")

    yield BASE_URL

    proc.kill()
    proc.wait()


@pytest.fixture(scope="session")
def browser_session(backend_server):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser_session, backend_server):
    ctx = browser_session.new_context()
    pg = ctx.new_page()
    pg.goto(backend_server)
    # init() が /api/stations を非同期取得するので、オプションが増えるまで待つ
    pg.wait_for_function("document.querySelectorAll('#pref-select option').length > 1", timeout=15000)
    yield pg
    ctx.close()
