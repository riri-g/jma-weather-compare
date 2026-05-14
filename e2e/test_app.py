"""
E2E テスト — 気象庁データ比較アプリ。

テスト ID 対応:
  T-11: TestStationSelection
  T-12: TestMonthlyDisplay
  T-13: TestDailyDisplay
  T-14: TestModeToggle
"""

import pytest
from unittest.mock import patch
from playwright.sync_api import Page, expect


# ────────────────────────────────────────────────────────────────
# T-11: 地点選択フロー
# ────────────────────────────────────────────────────────────────

class TestStationSelection:
    def test_page_loads(self, page: Page):
        expect(page).to_have_title("気象庁データ比較")

    def test_pref_select_has_options(self, page: Page):
        pref_sel = page.locator("#pref-select")
        options = pref_sel.locator("option")
        count = options.count()
        assert count > 10, f"都道府県の選択肢が少なすぎます: {count}"

    def test_station_select_disabled_initially(self, page: Page):
        station_sel = page.locator("#station-select")
        expect(station_sel).to_be_disabled()

    def test_fetch_btn_disabled_initially(self, page: Page):
        btn = page.locator("#fetch-btn")
        expect(btn).to_be_disabled()

    def test_station_select_enabled_after_pref_selection(self, page: Page):
        page.select_option("#pref-select", label="東京都")
        station_sel = page.locator("#station-select")
        expect(station_sel).to_be_enabled()

    def test_station_list_updates_on_pref_change(self, page: Page):
        page.select_option("#pref-select", label="東京都")
        options = page.locator("#station-select option")
        count = options.count()
        assert count > 1, f"東京都の観測局が少なすぎます: {count}"

    def test_fetch_btn_enabled_after_station_selection(self, page: Page):
        page.select_option("#pref-select", label="東京都")
        page.select_option("#station-select", index=1)  # 最初の実局を選択
        btn = page.locator("#fetch-btn")
        expect(btn).to_be_enabled()

    def test_placeholder_visible_initially(self, page: Page):
        placeholder = page.locator("#placeholder")
        expect(placeholder).to_be_visible()


# ────────────────────────────────────────────────────────────────
# T-14: モード切替
# ────────────────────────────────────────────────────────────────

class TestModeToggle:
    def test_monthly_btn_active_by_default(self, page: Page):
        classes = page.locator("#mode-monthly").get_attribute("class")
        assert "active" in classes

    def test_daily_btn_not_active_by_default(self, page: Page):
        classes = page.locator("#mode-daily").get_attribute("class")
        assert "active" not in classes

    def test_month_group_hidden_in_monthly_mode(self, page: Page):
        month_group = page.locator("#month-group")
        expect(month_group).to_be_hidden()

    def test_click_daily_activates_daily_btn(self, page: Page):
        page.click("#mode-daily")
        classes = page.locator("#mode-daily").get_attribute("class")
        assert "active" in classes

    def test_click_daily_shows_month_group(self, page: Page):
        page.click("#mode-daily")
        expect(page.locator("#month-group")).to_be_visible()

    def test_click_monthly_hides_month_group(self, page: Page):
        page.click("#mode-daily")
        page.click("#mode-monthly")
        expect(page.locator("#month-group")).to_be_hidden()

    def test_click_monthly_deactivates_daily_btn(self, page: Page):
        page.click("#mode-daily")
        page.click("#mode-monthly")
        classes = page.locator("#mode-daily").get_attribute("class")
        assert "active" not in classes


# ────────────────────────────────────────────────────────────────
# T-12: 月ごとデータ表示
# (実際の JMA へのアクセスは発生する — ネットワーク不要な場合はスキップ)
# ────────────────────────────────────────────────────────────────

class TestMonthlyDisplay:
    @pytest.fixture(autouse=True)
    def _goto_monthly(self, page: Page):
        """東京を選択して月ごとデータを取得する。"""
        page.select_option("#pref-select", label="東京都")
        page.select_option("#station-select", value="44|47662")
        page.fill("#year-input", "2024")
        page.click("#fetch-btn")
        # 最大 40 秒待機（初回スクレイピング）
        page.wait_for_selector("#content", state="visible", timeout=40000)

    def test_content_visible_after_fetch(self, page: Page):
        expect(page.locator("#content")).to_be_visible()

    def test_placeholder_hidden_after_fetch(self, page: Page):
        expect(page.locator("#placeholder")).to_be_hidden()

    def test_summary_temp_not_empty(self, page: Page):
        val = page.locator("#s-temp").inner_text()
        assert val != "--"

    def test_summary_precip_not_empty(self, page: Page):
        val = page.locator("#s-precip").inner_text()
        assert val != "--"

    def test_temp_chart_canvas_exists(self, page: Page):
        canvas = page.locator("#chart-temp")
        expect(canvas).to_be_visible()

    def test_precip_chart_canvas_exists(self, page: Page):
        canvas = page.locator("#chart-precip")
        expect(canvas).to_be_visible()

    def test_solar_chart_canvas_exists(self, page: Page):
        canvas = page.locator("#chart-solar")
        expect(canvas).to_be_visible()

    def test_anomaly_charts_visible(self, page: Page):
        for chart_id in ["chart-temp-anom", "chart-precip-anom", "chart-solar-anom"]:
            expect(page.locator(f"#{chart_id}")).to_be_visible()

    def test_status_message_shown(self, page: Page):
        status = page.locator("#status")
        expect(status).to_be_visible()
        assert "東京都" in status.inner_text() or "東京" in status.inner_text()


# ────────────────────────────────────────────────────────────────
# T-13: 日ごとデータ表示
# ────────────────────────────────────────────────────────────────

class TestDailyDisplay:
    @pytest.fixture(autouse=True)
    def _goto_daily(self, page: Page):
        """東京・日ごとモードでデータを取得する。"""
        page.click("#mode-daily")
        page.select_option("#pref-select", label="東京都")
        page.select_option("#station-select", value="44|47662")
        page.fill("#year-input", "2024")
        page.select_option("#month-input", "4")
        page.click("#fetch-btn")
        page.wait_for_selector("#daily-content", state="visible", timeout=40000)

    def test_daily_content_visible(self, page: Page):
        expect(page.locator("#daily-content")).to_be_visible()

    def test_monthly_content_hidden(self, page: Page):
        expect(page.locator("#content")).to_be_hidden()

    def test_daily_temp_chart_exists(self, page: Page):
        expect(page.locator("#chart-daily-temp")).to_be_visible()

    def test_daily_precip_chart_exists(self, page: Page):
        expect(page.locator("#chart-daily-precip")).to_be_visible()

    def test_daily_solar_chart_exists(self, page: Page):
        expect(page.locator("#chart-daily-solar")).to_be_visible()

    def test_status_shows_month(self, page: Page):
        status = page.locator("#status").inner_text()
        assert "4月" in status
