'use strict';

const API = location.hostname === 'localhost' ? 'http://localhost:8000/api' : '/api';
const MONTHS = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'];

const charts = {};
let currentMode = 'monthly';

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
    else fetchDaily();
  });

  // 月セレクタの初期値を当月に
  document.getElementById('month-input').value = new Date().getMonth() + 1;

  setupModeToggle();
}

// ─── モード切替 ───────────────────────────────────────────────────────────

function setupModeToggle() {
  const monthlyBtn   = document.getElementById('mode-monthly');
  const dailyBtn     = document.getElementById('mode-daily');
  const monthGroup   = document.getElementById('month-group');
  const content      = document.getElementById('content');
  const dailyContent = document.getElementById('daily-content');

  monthlyBtn.addEventListener('click', () => {
    if (currentMode === 'monthly') return;
    currentMode = 'monthly';
    monthlyBtn.classList.add('active');
    dailyBtn.classList.remove('active');
    monthGroup.style.display = 'none';
    dailyContent.style.display = 'none';
    document.getElementById('status').style.display = 'none';
  });

  dailyBtn.addEventListener('click', () => {
    if (currentMode === 'daily') return;
    currentMode = 'daily';
    dailyBtn.classList.add('active');
    monthlyBtn.classList.remove('active');
    monthGroup.style.display = '';
    content.style.display = 'none';
    document.getElementById('status').style.display = 'none';
  });
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

// ─── 月ごと描画 ───────────────────────────────────────────────────────────

function renderAll(data) {
  const { current, normals, year } = data;
  updateSummary(current, normals);
  renderChart('temp',   current.temp,   normals.temp,   year, getVar('--temp-color'),   '℃',     'line');
  renderChart('precip', current.precip, normals.precip, year, getVar('--precip-color'), 'mm',     'bar');
  renderChart('solar',  current.solar,  normals.solar,  year, getVar('--solar-color'),  'MJ/m²', 'line');
  document.getElementById('content').style.display = 'block';
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

  document.getElementById('daily-content').style.display = 'block';
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

init().catch(e => {
  setStatus('error', `初期化エラー: ${e.message}　バックエンドが起動しているか確認してください。`);
});
