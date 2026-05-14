"""
FastAPI エンドポイントの統合テスト。

テスト ID 対応:
  T-06: TestGetStations
  T-07: TestGetClimate
  T-08: TestGetDaily
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.fixtures import MONTHLY_HTML, NORMALS_HTML, DAILY_HTML


@pytest.fixture(scope="module")
def client():
    from main import app
    return TestClient(app)


# ────────────────────────────────────────────────────────────────
# T-06: GET /api/stations
# ────────────────────────────────────────────────────────────────

class TestGetStations:
    def test_returns_200(self, client):
        res = client.get("/api/stations")
        assert res.status_code == 200

    def test_returns_list(self, client):
        res = client.get("/api/stations")
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_station_has_required_keys(self, client):
        res = client.get("/api/stations")
        station = res.json()[0]
        for key in ("pref", "name", "prec_no", "block_no"):
            assert key in station

    def test_no_zero_block_no(self, client):
        res = client.get("/api/stations")
        for s in res.json():
            assert s["block_no"] != "00", f"block_no='00' が含まれています: {s}"

    def test_contains_tokyo(self, client):
        res = client.get("/api/stations")
        names = [s["name"] for s in res.json()]
        assert "東京" in names

    def test_contains_amedas_station(self, client):
        res = client.get("/api/stations")
        amedas = [s for s in res.json() if not s["block_no"].startswith("47")]
        assert len(amedas) > 0, "AMeDAS 局が一件もありません"


# ────────────────────────────────────────────────────────────────
# T-07: GET /api/climate
# ────────────────────────────────────────────────────────────────

class TestGetClimate:
    def test_normal_response(self, client):
        with patch("jma_client._fetch", side_effect=[MONTHLY_HTML, NORMALS_HTML]):
            import jma_client
            jma_client._CACHE.clear()
            res = client.get("/api/climate?prec_no=44&block_no=47662&year=2026")
        assert res.status_code == 200

    def test_response_structure(self, client):
        with patch("jma_client._fetch", side_effect=[MONTHLY_HTML, NORMALS_HTML]):
            import jma_client
            jma_client._CACHE.clear()
            res = client.get("/api/climate?prec_no=44&block_no=47662&year=2026")
        data = res.json()
        for key in ("station", "pref", "year", "current", "normals"):
            assert key in data

    def test_current_has_12_months(self, client):
        with patch("jma_client._fetch", side_effect=[MONTHLY_HTML, NORMALS_HTML]):
            import jma_client
            jma_client._CACHE.clear()
            res = client.get("/api/climate?prec_no=44&block_no=47662&year=2026")
        data = res.json()
        assert len(data["current"]["temp"]) == 12
        assert len(data["normals"]["temp"]) == 12

    def test_unknown_station_returns_404(self, client):
        res = client.get("/api/climate?prec_no=99&block_no=99999&year=2026")
        assert res.status_code == 404

    def test_jma_fetch_error_returns_502(self, client):
        import jma_client
        jma_client._CACHE.clear()
        with patch("jma_client._fetch", side_effect=Exception("Connection error")):
            res = client.get("/api/climate?prec_no=44&block_no=47662&year=2026")
        assert res.status_code == 502

    def test_year_is_reflected_in_response(self, client):
        with patch("jma_client._fetch", side_effect=[MONTHLY_HTML, NORMALS_HTML]):
            import jma_client
            jma_client._CACHE.clear()
            res = client.get("/api/climate?prec_no=44&block_no=47662&year=2020")
        assert res.json()["year"] == 2020


# ────────────────────────────────────────────────────────────────
# T-08: GET /api/daily
# ────────────────────────────────────────────────────────────────

class TestGetDaily:
    def test_normal_response(self, client):
        with patch("jma_client._fetch", side_effect=[DAILY_HTML, NORMALS_HTML]):
            import jma_client
            jma_client._CACHE.clear()
            res = client.get("/api/daily?prec_no=44&block_no=47662&year=2026&month=4")
        assert res.status_code == 200

    def test_response_structure(self, client):
        with patch("jma_client._fetch", side_effect=[DAILY_HTML, NORMALS_HTML]):
            import jma_client
            jma_client._CACHE.clear()
            res = client.get("/api/daily?prec_no=44&block_no=47662&year=2026&month=4")
        data = res.json()
        for key in ("station", "pref", "year", "month", "current", "normals"):
            assert key in data

    def test_current_has_31_elements(self, client):
        with patch("jma_client._fetch", side_effect=[DAILY_HTML, NORMALS_HTML]):
            import jma_client
            jma_client._CACHE.clear()
            res = client.get("/api/daily?prec_no=44&block_no=47662&year=2026&month=4")
        data = res.json()
        assert len(data["current"]["temp"]) == 31

    def test_unknown_station_returns_404(self, client):
        res = client.get("/api/daily?prec_no=99&block_no=99999&year=2026&month=4")
        assert res.status_code == 404

    def test_invalid_month_returns_400(self, client):
        res = client.get("/api/daily?prec_no=44&block_no=47662&year=2026&month=13")
        assert res.status_code == 400

    def test_month_zero_returns_400(self, client):
        res = client.get("/api/daily?prec_no=44&block_no=47662&year=2026&month=0")
        assert res.status_code == 400

    def test_jma_fetch_error_returns_502(self, client):
        import jma_client
        jma_client._CACHE.clear()
        with patch("jma_client._fetch", side_effect=Exception("timeout")):
            res = client.get("/api/daily?prec_no=44&block_no=47662&year=2026&month=4")
        assert res.status_code == 502

    def test_month_is_reflected_in_response(self, client):
        with patch("jma_client._fetch", side_effect=[DAILY_HTML, NORMALS_HTML]):
            import jma_client
            jma_client._CACHE.clear()
            res = client.get("/api/daily?prec_no=44&block_no=47662&year=2026&month=7")
        assert res.json()["month"] == 7
