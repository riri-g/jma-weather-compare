'use strict';

const API = location.hostname === 'localhost' ? 'http://localhost:8000/api' : '/api';
const MONTHS = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'];

const charts = {};
let currentMode = 'monthly';
let currentData = null;

// ─── 地図関連 ─────────────────────────────────────────────────────────────
let leafletMap = null;
let selectedMarker = null;
let mapLoaded = false;

// ─── 初期化 ────────────────────────────────────────────────────────────────

async function init() {
  const res = await fetch(`${API}/stations`);
  const stations = await res.json();

  const prefMap = {};
  for (const s of stations) {
    if (!prefMap[s.pref]) prefMap[s.pref] = [];
    prefMap[s.pref].push(s);
  }

  const prefSel    = document.getElementById('pref-select');
  const stationSel = document.getElementById('station-select');

  for (const pref of Object.keys(prefMap)) {
    prefSel.add(new Option(pref, pref));
  }

  prefSel.addEventListener('change', () => {
    stationSel.innerHTML = '<option value="">-- 選択 --</option>';
    stationSel.disabled = true;
    document.getElementById('fetch-btn').disabled = true;

    const pref = prefSel.value;
    if (!pref) return;
    for (const s of prefMap[pref]) {
      stationSel.add(new Option(s.name, `${s.prec_no}|${s.block_no}`));
    }
    stationSel.disabled = false;
  });

  stationSel.addEventListener('change', () => {
    document.getElementById('fetch-btn').disabled = !stationSel.value;
  });

  document.getElementById('fetch-btn').addEventListener('click', () => {
    if (currentMode === 'monthly') fetchData();
    else if (currentMode === 'daily') fetchDaily();
    else fetchRange();
  });

  // 月セレクタの初期値を当月に
  document.getElementById('month-input').value = new Date().getMonth() + 1;

  // 期間指定の初期値を今月1日〜今日に
  const today = new Date();
  const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  document.getElementById('range-start').value = firstOfMonth.toISOString().slice(0, 10);
  document.getElementById('range-end').value   = today.toISOString().slice(0, 10);
}

// ─── モード切替（HTML の onclick から直接呼ばれる） ──────────────────────

function setMode(mode) {
  if (currentMode === mode) return;
  currentMode = mode;
  document.getElementById('mode-monthly').classList.toggle('active', mode === 'monthly');
  document.getElementById('mode-daily').classList.toggle('active', mode === 'daily');
  document.getElementById('mode-range').classList.toggle('active', mode === 'range');
  document.getElementById('month-group').style.display      = mode === 'daily'  ? '' : 'none';
  document.getElementById('range-group').style.display      = mode === 'range'  ? '' : 'none';
  document.getElementById('range-group-end').style.display  = mode === 'range'  ? '' : 'none';
  document.getElementById('year-input').closest('.ctrl-group').style.display =
    mode === 'range' ? 'none' : '';
  document.getElementById('content').style.display       = 'none';
  document.getElementById('daily-content').style.display = 'none';
  document.getElementById('range-content').style.display = 'none';
  document.getElementById('status').style.display        = 'none';
  document.getElementById('csv-btn').style.display       = 'none';
  currentData = null;
}

// ─── 月ごとデータ取得 ─────────────────────────────────────────────────────

async function fetchData() {
  const [prec_no, block_no] = document.getElementById('station-select').value.split('|');
  const year = document.getElementById('year-input').value;

  setStatus('loading', '気象庁からデータを取得中…（初回は10〜20秒かかる場合があります）');
  document.getElementById('fetch-btn').disabled = true;
  document.getElementById('content').style.display = 'none';
  document.getElementById('placeholder').style.display = 'none';

  try {
    const res = await fetch(`${API}/climate?prec_no=${prec_no}&block_no=${block_no}&year=${year}`);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    renderAll(data);
    setStatus('info', `${data.pref} ${data.station}（${year}年）のデータを表示しています。`);
  } catch (e) {
    setStatus('error', `エラー: ${e.message}`);
    document.getElementById('placeholder').style.display = 'block';
  } finally {
    document.getElementById('fetch-btn').disabled = false;
  }
}

// ─── 日ごとデータ取得 ─────────────────────────────────────────────────────

async function fetchDaily() {
  const [prec_no, block_no] = document.getElementById('station-select').value.split('|');
  const year  = document.getElementById('year-input').value;
  const month = document.getElementById('month-input').value;

  setStatus('loading', '気象庁からデータを取得中…（初回は10〜20秒かかる場合があります）');
  document.getElementById('fetch-btn').disabled = true;
  document.getElementById('daily-content').style.display = 'none';
  document.getElementById('placeholder').style.display = 'none';

  try {
    const res = await fetch(`${API}/daily?prec_no=${prec_no}&block_no=${block_no}&year=${year}&month=${month}`);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    renderDaily(data);
    setStatus('info', `${data.pref} ${data.station}（${year}年${month}月）の日別データを表示しています。`);
  } catch (e) {
    setStatus('error', `エラー: ${e.message}`);
    document.getElementById('placeholder').style.display = 'block';
  } finally {
    document.getElementById('fetch-btn').disabled = false;
  }
}

// ─── 期間指定データ取得 ───────────────────────────────────────────────────

async function fetchRange() {
  const [prec_no, block_no] = document.getElementById('station-select').value.split('|');
  const start = document.getElementById('range-start').value;
  const end   = document.getElementById('range-end').value;

  if (!start || !end) {
    setStatus('error', '開始日と終了日を入力してください。');
    return;
  }
  if (start > end) {
    setStatus('error', '開始日は終了日より前の日付を指定してください。');
    return;
  }

  setStatus('loading', '気象庁からデータを取得中…（月をまたぐ場合は時間がかかります）');
  document.getElementById('fetch-btn').disabled = true;
  document.getElementById('range-content').style.display = 'none';
  document.getElementById('placeholder').style.display = 'none';

  try {
    const res = await fetch(`${API}/range?prec_no=${prec_no}&block_no=${block_no}&start=${start}&end=${end}`);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    renderRange(data);
    setStatus('info', `${data.pref} ${data.station}（${start} ～ ${end}）の日別データを表示しています。`);
  } catch (e) {
    setStatus('error', `エラー: ${e.message}`);
    document.getElementById('placeholder').style.display = 'block';
  } finally {
    document.getElementById('fetch-btn').disabled = false;
  }
}

// ─── 月ごと描画 ───────────────────────────────────────────────────────────

function renderAll(data) {
  currentData = data;
  const { current, normals, year } = data;
  updateSummary(current, normals);
  renderChart('temp',   current.temp,   normals.temp,   year, getVar('--temp-color'),   '℃',     'line');
  renderChart('precip', current.precip, normals.precip, year, getVar('--precip-color'), 'mm',     'bar');
  renderChart('solar',  current.solar,  normals.solar,  year, getVar('--solar-color'),  'MJ/m²', 'line');
  document.getElementById('content').style.display = 'block';
  document.getElementById('csv-btn').style.display = '';
}

// ─── 日ごと描画 ───────────────────────────────────────────────────────────

function renderDaily(data) {
  const { current, normals, year, month } = data;
  const days   = daysInMonth(year, month);
  const labels = Array.from({length: days}, (_, i) => `${i + 1}日`);

  const curTemp   = current.temp.slice(0, days);
  const curPrecip = current.precip.slice(0, days);
  const curSolar  = current.solar.slice(0, days);

  const normTemp   = normals.temp[month - 1];
  const normPrecip = normals.precip[month - 1] != null
    ? +(normals.precip[month - 1] / days).toFixed(2) : null;
  const normSolar  = normals.solar[month - 1] != null
    ? +(normals.solar[month - 1] / days).toFixed(2) : null;

  renderDailyChart('daily-temp',   labels, curTemp,   normTemp,   year, month, getVar('--temp-color'),   '℃',     'line');
  renderDailyChart('daily-precip', labels, curPrecip, normPrecip, year, month, getVar('--precip-color'), 'mm',     'bar');
  renderDailyChart('daily-solar',  labels, curSolar,  normSolar,  year, month, getVar('--solar-color'),  'MJ/m²', 'line');

  currentData = data;
  document.getElementById('daily-content').style.display = 'block';
  document.getElementById('csv-btn').style.display = '';
}

// ─── 期間指定描画 ─────────────────────────────────────────────────────────

function renderRange(data) {
  const { current, normals, start, end } = data;
  const labels    = current.labels;

  // 各ラベルから月を取り出し、その月の平年値を参照する
  const normTempArr   = labels.map(lbl => {
    const m = parseInt(lbl.split('/')[0], 10);
    return normals.temp[m - 1] ?? null;
  });
  const normPrecipArr = labels.map(lbl => {
    const m = parseInt(lbl.split('/')[0], 10);
    const days = new Date(new Date(start).getFullYear(), m, 0).getDate();
    const v = normals.precip[m - 1];
    return v != null ? +(v / days).toFixed(2) : null;
  });
  const normSolarArr  = labels.map(lbl => {
    const m = parseInt(lbl.split('/')[0], 10);
    const days = new Date(new Date(start).getFullYear(), m, 0).getDate();
    const v = normals.solar[m - 1];
    return v != null ? +(v / days).toFixed(2) : null;
  });

  renderRangeChart('range-temp',   labels, current.temp,   normTempArr,   getVar('--temp-color'),   '℃',     'line');
  renderRangeChart('range-precip', labels, current.precip, normPrecipArr, getVar('--precip-color'), 'mm',     'bar');
  renderRangeChart('range-solar',  labels, current.solar,  normSolarArr,  getVar('--solar-color'),  'MJ/m²', 'line');

  currentData = data;
  document.getElementById('range-content').style.display = 'block';
  document.getElementById('csv-btn').style.display = '';
}

function renderRangeChart(key, labels, curVals, normVals, color, unit, type) {
  const id = `chart-${key}`;
  if (charts[id]) charts[id].destroy();

  const normalColor = getVar('--normal-dash');
  const datasets = [
    {
      label: '実績',
      data: curVals,
      ...(type === 'bar'
        ? { backgroundColor: color + 'aa', borderColor: color, borderWidth: 1.5 }
        : { borderColor: color, backgroundColor: color + '22', borderWidth: 2,
            pointRadius: labels.length > 60 ? 0 : 2, pointHoverRadius: 5, tension: 0.2, fill: true }),
      order: 1,
    },
    {
      label: '平年値（参考）',
      data: normVals,
      type: 'line',
      borderColor: normalColor,
      borderWidth: 1.5,
      borderDash: [6, 4],
      pointRadius: 0,
      fill: false,
      order: 0,
    },
  ];

  const ctx = document.getElementById(id).getContext('2d');
  charts[id] = new Chart(ctx, {
    type: type === 'bar' ? 'bar' : 'line',
    data: { labels, datasets },
    options: {
      ...chartOptions(unit),
      scales: {
        ...chartOptions(unit).scales,
        x: {
          ...chartOptions(unit).scales.x,
          ticks: {
            font: { size: 10 },
            maxTicksLimit: 20,
            maxRotation: 45,
          },
        },
      },
    },
  });
}

function daysInMonth(year, month) {
  return new Date(year, month, 0).getDate();
}

function renderDailyChart(key, labels, curVals, normVal, year, month, color, unit, type) {
  const id = `chart-${key}`;
  if (charts[id]) charts[id].destroy();

  const normalColor = getVar('--normal-dash');
  const datasets = [
    {
      label: `${year}年${month}月`,
      data: curVals,
      ...(type === 'bar'
        ? { backgroundColor: color + 'aa', borderColor: color, borderWidth: 1.5 }
        : { borderColor: color, backgroundColor: color + '22', borderWidth: 2,
            pointRadius: 2, pointHoverRadius: 5, tension: 0.2, fill: true }),
      order: 1,
    },
  ];

  if (normVal != null) {
    datasets.push({
      label: '平年値（参考）',
      data: labels.map(() => normVal),
      type: 'line',
      borderColor: normalColor,
      borderWidth: 1.5,
      borderDash: [6, 4],
      pointRadius: 0,
      fill: false,
      order: 0,
    });
  }

  const ctx = document.getElementById(id).getContext('2d');
  charts[id] = new Chart(ctx, {
    type: type === 'bar' ? 'bar' : 'line',
    data: { labels, datasets },
    options: chartOptions(unit),
  });
}

// ─── サマリーカード ───────────────────────────────────────────────────────

function updateSummary(current, normals) {
  const cfg = [
    { key: 'temp',   id: 's-temp',   unit: '℃',    fn: avg, fmt: v => v.toFixed(1) },
    { key: 'precip', id: 's-precip', unit: 'mm',    fn: sum, fmt: v => v.toFixed(0) },
    { key: 'solar',  id: 's-solar',  unit: 'MJ/m²', fn: sum, fmt: v => v.toFixed(1) },
  ];

  for (const c of cfg) {
    const cur     = c.fn(current[c.key].filter(v => v !== null));
    const nor     = c.fn(normals[c.key].filter(v => v !== null));
    const hasData = current[c.key].some(v => v !== null);

    document.getElementById(c.id).textContent =
      hasData ? `${c.fmt(cur)} ${c.unit}` : '--';

    if (hasData && nor) {
      const diff = cur - nor;
      const pct  = nor !== 0 ? ((diff / nor) * 100).toFixed(1) : '—';
      const sign = diff >= 0 ? '+' : '';
      const el   = document.getElementById(`${c.id}-diff`);
      el.textContent = `平年比: ${sign}${c.fmt(diff)} ${c.unit} (${sign}${pct}%)`;
      el.className   = `diff ${diff > 0 ? 'pos' : diff < 0 ? 'neg' : 'zero'}`;
    }
  }
}

// ─── Chart.js グラフ描画（月ごと） ───────────────────────────────────────

function renderChart(key, curVals, norVals, year, color, unit, type) {
  const mainId = `chart-${key}`;
  const anomId = `chart-${key}-anom`;

  if (charts[mainId]) charts[mainId].destroy();
  if (charts[anomId]) charts[anomId].destroy();

  const normalColor = getVar('--normal-dash');

  const mainCtx = document.getElementById(mainId).getContext('2d');
  charts[mainId] = new Chart(mainCtx, {
    type: type === 'bar' ? 'bar' : 'line',
    data: {
      labels: MONTHS,
      datasets: [
        {
          label: `${year}年`,
          data: curVals,
          ...(type === 'bar'
            ? { backgroundColor: color + 'aa', borderColor: color, borderWidth: 1.5 }
            : { borderColor: color, backgroundColor: color + '22', borderWidth: 2.5,
                pointRadius: 4, pointHoverRadius: 6, tension: 0.3, fill: true }),
          order: 1,
        },
        {
          label: '平年値',
          data: norVals,
          type: 'line',
          borderColor: normalColor,
          borderWidth: 2,
          borderDash: [6, 4],
          pointRadius: 3,
          fill: false,
          tension: 0.3,
          order: 0,
        },
      ],
    },
    options: chartOptions(unit),
  });

  const anomData = MONTHS.map((_, i) => {
    const c = curVals[i], n = norVals[i];
    return c != null && n != null ? +(c - n).toFixed(2) : null;
  });

  const anomCtx = document.getElementById(anomId).getContext('2d');
  charts[anomId] = new Chart(anomCtx, {
    type: 'bar',
    data: {
      labels: MONTHS,
      datasets: [{
        label: `平年差 (${unit})`,
        data: anomData,
        backgroundColor: anomData.map(v =>
          v === null ? 'transparent' : v >= 0 ? getVar('--positive') + 'bb' : getVar('--negative') + 'bb'
        ),
        borderColor: anomData.map(v =>
          v === null ? 'transparent' : v >= 0 ? getVar('--positive') : getVar('--negative')
        ),
        borderWidth: 1,
      }],
    },
    options: {
      ...chartOptions(unit),
      plugins: { ...chartOptions(unit).plugins, legend: { display: false } },
    },
  });
}

// ─── Chart.js 共通オプション ──────────────────────────────────────────────

function chartOptions(unit) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: ctx => {
            const v = ctx.parsed.y;
            return v != null
              ? `${ctx.dataset.label}: ${v} ${unit}`
              : `${ctx.dataset.label}: データなし`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: '#e8edf2' },
        ticks: { font: { size: 11 } },
      },
      y: {
        grid: { color: '#e8edf2' },
        ticks: { font: { size: 12 }, callback: v => `${v}` },
      },
    },
  };
}

// ─── 地図 ────────────────────────────────────────────────────────────────

function toggleMap() {
  const panel = document.getElementById('map-panel');
  const btn   = document.getElementById('map-btn');
  const open  = panel.style.display === 'none';
  panel.style.display = open ? '' : 'none';
  btn.classList.toggle('open', open);

  if (!open) return;

  // display:none → 表示に切り替えた直後はコンテナサイズが確定していないため、
  // ブラウザの描画サイクルを1フレーム待ってから初期化・リサイズする
  requestAnimationFrame(() => {
    if (!mapLoaded) {
      initMap();
    } else if (leafletMap) {
      leafletMap.invalidateSize();
    }
  });
}

async function initMap() {
  mapLoaded = true;

  leafletMap = L.map('map-container', { zoomControl: true }).setView([36.5, 136.5], 5);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 18,
  }).addTo(leafletMap);

  // パネル表示後にサイズを再確定してタイルを正しく描画する
  leafletMap.invalidateSize();

  let geoStations = [];
  try {
    const res = await fetch(`${API}/stations-geo`);
    geoStations = await res.json();
  } catch (e) {
    document.getElementById('map-hint').textContent = '地図データの読み込みに失敗しました。';
    return;
  }

  const exactCount = geoStations.filter(s => s.exact).length;
  const total      = geoStations.length;
  const hintEl     = document.getElementById('map-exact-count');
  hintEl.textContent = exactCount === total
    ? `全 ${total} 局（正確な座標）`
    : `正確な座標: ${exactCount} 局 / 都道府県中心: ${total - exactCount} 局`;

  // 選択状態のマーカーを更新するための参照
  const markerMap = {};  // key → marker

  geoStations.forEach(s => {
    const key    = `${s.prec_no}|${s.block_no}`;
    const color  = s.exact ? '#1a6fc4' : '#94a3b8';
    const radius = s.exact ? 5 : 3;

    const marker = L.circleMarker([s.lat, s.lon], {
      radius,
      fillColor: color,
      color: '#fff',
      weight: 1,
      fillOpacity: 0.85,
    }).addTo(leafletMap);

    marker.bindTooltip(`${s.pref}　${s.name}`, { direction: 'top', offset: [0, -4] });

    marker.on('click', () => selectStationFromMap(s, marker, markerMap));
    markerMap[key] = marker;
  });

  // ドロップダウンで変更されたときにマーカーを同期
  document.getElementById('station-select').addEventListener('change', () => {
    const val = document.getElementById('station-select').value;
    highlightMarker(val, markerMap);
  });
}

function selectStationFromMap(s, marker, markerMap) {
  const key = `${s.prec_no}|${s.block_no}`;

  // 都道府県セレクタを更新
  const prefSel = document.getElementById('pref-select');
  prefSel.value = s.pref;
  prefSel.dispatchEvent(new Event('change'));

  // 観測地点セレクタを更新（change イベント後にオプションが生成される）
  setTimeout(() => {
    const stationSel = document.getElementById('station-select');
    stationSel.value = key;
    stationSel.dispatchEvent(new Event('change'));
    highlightMarker(key, markerMap);
  }, 0);
}

function highlightMarker(key, markerMap) {
  // 前の選択マーカーをリセット
  if (selectedMarker) {
    selectedMarker.setStyle({ fillColor: selectedMarker._origColor, radius: selectedMarker._origRadius });
  }
  const m = markerMap[key];
  if (!m) return;
  m._origColor  = m._origColor  || m.options.fillColor;
  m._origRadius = m._origRadius || m.options.radius;
  m.setStyle({ fillColor: '#e05252', radius: 8 });
  selectedMarker = m;

  // 地図をマーカー中心に移動
  if (leafletMap) leafletMap.panTo(m.getLatLng());
}

// ─── CSV ダウンロード ─────────────────────────────────────────────────────

function downloadCSV() {
  if (!currentData) return;
  const { rows, filename } = buildCSV(currentData, currentMode);
  const bom  = '﻿'; // Excel で文字化けしないよう BOM を付与
  const blob = new Blob([bom + rows.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function buildCSV(data, mode) {
  const esc = v => (v == null ? '' : String(v));

  if (mode === 'monthly') {
    const { current, normals, station, pref, year } = data;
    const header = ['月', '気温実績(℃)', '気温平年値(℃)', '気温平年差(℃)',
                    '降水量実績(mm)', '降水量平年値(mm)', '降水量平年差(mm)',
                    '日射量実績(MJ/m²)', '日射量平年値(MJ/m²)', '日射量平年差(MJ/m²)'];
    const rows = [header.join(',')];
    for (let i = 0; i < 12; i++) {
      const ct = current.temp[i],   nt = normals.temp[i];
      const cp = current.precip[i], np = normals.precip[i];
      const cs = current.solar[i],  ns = normals.solar[i];
      rows.push([
        i + 1,
        esc(ct), esc(nt), ct != null && nt != null ? +(ct - nt).toFixed(2) : '',
        esc(cp), esc(np), cp != null && np != null ? +(cp - np).toFixed(1) : '',
        esc(cs), esc(ns), cs != null && ns != null ? +(cs - ns).toFixed(1) : '',
      ].join(','));
    }
    return { rows, filename: `${pref}${station}_${year}年_月別.csv` };
  }

  if (mode === 'daily') {
    const { current, normals, station, pref, year, month } = data;
    const days = daysInMonth(year, month);
    const nt   = normals.temp[month - 1];
    const np   = normals.precip[month - 1] != null ? +(normals.precip[month - 1] / days).toFixed(2) : null;
    const ns   = normals.solar[month - 1]  != null ? +(normals.solar[month - 1]  / days).toFixed(2) : null;
    const header = ['日', '気温実績(℃)', '降水量実績(mm)', '日射量実績(MJ/m²)',
                    '気温平年参考(℃)', '降水量平年参考(mm)', '日射量平年参考(MJ/m²)'];
    const rows = [header.join(',')];
    for (let i = 0; i < days; i++) {
      rows.push([
        i + 1,
        esc(current.temp[i]), esc(current.precip[i]), esc(current.solar[i]),
        esc(nt), esc(np), esc(ns),
      ].join(','));
    }
    return { rows, filename: `${pref}${station}_${year}年${month}月_日別.csv` };
  }

  // range
  const { current, normals, station, pref, start, end } = data;
  const header = ['日付', '気温実績(℃)', '降水量実績(mm)', '日射量実績(MJ/m²)',
                  '気温平年参考(℃)', '降水量平年参考(mm)', '日射量平年参考(MJ/m²)'];
  const rows = [header.join(',')];
  current.labels.forEach((lbl, i) => {
    const m    = parseInt(lbl.split('/')[0], 10);
    const year = parseInt(start.split('-')[0], 10);
    const days = new Date(year, m, 0).getDate();
    const nt   = normals.temp[m - 1] ?? null;
    const np   = normals.precip[m - 1] != null ? +(normals.precip[m - 1] / days).toFixed(2) : null;
    const ns   = normals.solar[m - 1]  != null ? +(normals.solar[m - 1]  / days).toFixed(2) : null;
    rows.push([
      lbl,
      esc(current.temp[i]), esc(current.precip[i]), esc(current.solar[i]),
      esc(nt), esc(np), esc(ns),
    ].join(','));
  });
  return { rows, filename: `${pref}${station}_${start}_${end}_期間.csv` };
}

// ─── ユーティリティ ───────────────────────────────────────────────────────

function setStatus(type, msg) {
  const el = document.getElementById('status');
  el.className = type;
  el.textContent = msg;
  el.style.display = 'block';
}

function getVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function avg(arr) {
  if (!arr.length) return 0;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function sum(arr) {
  return arr.reduce((a, b) => a + b, 0);
}

// ─── 起動 ─────────────────────────────────────────────────────────────────

document.getElementById('month-input').value = new Date().getMonth() + 1;

// 地図ボタンのイベントを onclick 属性ではなく JS 側で登録
document.getElementById('map-btn').addEventListener('click', toggleMap);

init().catch(e => {
  setStatus('error', `初期化エラー: ${e.message}　バックエンドが起動しているか確認してください。`);
});
