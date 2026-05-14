'use strict';

// テスト可能なピュア関数群。app.js から export して使う。

export function avg(arr) {
  if (!arr.length) return 0;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

export function sum(arr) {
  return arr.reduce((a, b) => a + b, 0);
}

export function daysInMonth(year, month) {
  return new Date(year, month, 0).getDate();
}

/**
 * 月別サマリーを計算して返す（DOM 操作なし）。
 * @param {{temp:number[], precip:number[], solar:number[]}} current
 * @param {{temp:number[], precip:number[], solar:number[]}} normals
 * @returns {{temp, precip, solar}: {cur, nor, diff, pct}}
 */
export function calcSummary(current, normals) {
  const cfg = [
    { key: 'temp',   fn: avg },
    { key: 'precip', fn: sum },
    { key: 'solar',  fn: sum },
  ];
  const result = {};
  for (const { key, fn } of cfg) {
    const cur = fn(current[key].filter(v => v !== null));
    const nor = fn(normals[key].filter(v => v !== null));
    const diff = cur - nor;
    const pct = nor !== 0 ? (diff / nor) * 100 : null;
    result[key] = { cur, nor, diff, pct };
  }
  return result;
}

/**
 * 月別平年差を計算して返す。
 * @param {number[]} curVals  12要素
 * @param {number[]} norVals  12要素
 * @returns {number[]} 12要素（どちらか null なら null）
 */
export function calcAnomaly(curVals, norVals) {
  return curVals.map((c, i) => {
    const n = norVals[i];
    return c != null && n != null ? +(c - n).toFixed(2) : null;
  });
}

/**
 * 日ごとモードの平年参考値を計算する。
 * @param {number[]} normals  12要素の月別平年値
 * @param {number}   month    1-12
 * @param {number}   days     月の日数
 * @param {'avg'|'perday'} mode  avg: そのまま返す / perday: days で割る
 */
export function dailyNormRef(normals, month, days, mode) {
  const v = normals[month - 1];
  if (v == null) return null;
  return mode === 'perday' ? +(v / days).toFixed(2) : v;
}
