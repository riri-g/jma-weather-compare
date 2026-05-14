/**
 * フロントエンドユーティリティ関数の単体テスト。
 *
 * テスト ID 対応:
 *   T-09: describe avg / sum
 *   T-10: describe daysInMonth
 *   + calcSummary, calcAnomaly, dailyNormRef
 */

import { describe, it, expect } from 'vitest';
import {
  avg,
  sum,
  daysInMonth,
  calcSummary,
  calcAnomaly,
  dailyNormRef,
} from '../app-utils.js';

// ────────────────────────────────────────────────────────────────
// T-09: avg / sum
// ────────────────────────────────────────────────────────────────

describe('avg', () => {
  it('単純な平均を返す', () => {
    expect(avg([1, 2, 3])).toBe(2);
  });

  it('浮動小数を含む場合', () => {
    expect(avg([1.5, 2.5])).toBe(2.0);
  });

  it('要素が 1 つの場合はその値を返す', () => {
    expect(avg([5])).toBe(5);
  });

  it('空配列は 0 を返す', () => {
    expect(avg([])).toBe(0);
  });

  it('負の値を含む場合', () => {
    expect(avg([-3, 3])).toBe(0);
  });
});

describe('sum', () => {
  it('合計を返す', () => {
    expect(sum([1, 2, 3])).toBe(6);
  });

  it('浮動小数の合計', () => {
    expect(sum([0.1, 0.2, 0.3])).toBeCloseTo(0.6);
  });

  it('空配列は 0 を返す', () => {
    expect(sum([])).toBe(0);
  });

  it('大きな値でも正確', () => {
    expect(sum([1000, 2000, 3000])).toBe(6000);
  });
});

// ────────────────────────────────────────────────────────────────
// T-10: daysInMonth
// ────────────────────────────────────────────────────────────────

describe('daysInMonth', () => {
  it('4月は30日', () => {
    expect(daysInMonth(2026, 4)).toBe(30);
  });

  it('3月は31日', () => {
    expect(daysInMonth(2026, 3)).toBe(31);
  });

  it('2月（平年）は28日', () => {
    expect(daysInMonth(2025, 2)).toBe(28);
  });

  it('2月（うるう年）は29日', () => {
    expect(daysInMonth(2024, 2)).toBe(29);
  });

  it('12月は31日', () => {
    expect(daysInMonth(2026, 12)).toBe(31);
  });

  it('1月は31日', () => {
    expect(daysInMonth(2026, 1)).toBe(31);
  });
});

// ────────────────────────────────────────────────────────────────
// calcSummary
// ────────────────────────────────────────────────────────────────

describe('calcSummary', () => {
  const current = {
    temp:   [5.4, 6.1, 10.8, 15.2, 19.7, null, null, null, null, null, null, null],
    precip: [80.5, 45.5, 118.0, 95.5, 163.5, null, null, null, null, null, null, null],
    solar:  [282.5, 230.5, 330.0, 390.5, 410.0, null, null, null, null, null, null, null],
  };
  const normals = {
    temp:   [5.4, 6.1, 9.4, 14.3, 18.9, 22.4, 25.7, 26.9, 23.3, 17.8, 12.5, 7.7],
    precip: [59.7, 56.5, 116.0, 133.5, 139.5, 167.8, 153.5, 167.8, 224.9, 197.8, 92.5, 57.6],
    solar:  [255.0, 230.5, 340.5, 390.0, 420.5, 380.0, 390.5, 410.0, 300.5, 280.5, 230.5, 220.0],
  };

  it('気温の平均差を計算する', () => {
    const result = calcSummary(current, normals);
    // current の実績 5 ヶ月平均
    const expectedCur = avg([5.4, 6.1, 10.8, 15.2, 19.7]);
    expect(result.temp.cur).toBeCloseTo(expectedCur);
  });

  it('降水量の合計差を計算する', () => {
    const result = calcSummary(current, normals);
    const expectedCur = sum([80.5, 45.5, 118.0, 95.5, 163.5]);
    expect(result.precip.cur).toBeCloseTo(expectedCur);
  });

  it('差分 (diff) が cur - nor に等しい', () => {
    const result = calcSummary(current, normals);
    expect(result.temp.diff).toBeCloseTo(result.temp.cur - result.temp.nor);
  });

  it('パーセンテージ (pct) が (diff/nor)*100 に等しい', () => {
    const result = calcSummary(current, normals);
    const expected = (result.temp.diff / result.temp.nor) * 100;
    expect(result.temp.pct).toBeCloseTo(expected);
  });
});

// ────────────────────────────────────────────────────────────────
// calcAnomaly
// ────────────────────────────────────────────────────────────────

describe('calcAnomaly', () => {
  it('各月の平年差を計算する', () => {
    const cur = [5.4, 6.1, null, null, null, null, null, null, null, null, null, null];
    const nor = [5.0, 6.0, 9.4,  14.3, 18.9, 22.4, 25.7, 26.9, 23.3, 17.8, 12.5, 7.7];
    const anom = calcAnomaly(cur, nor);
    expect(anom[0]).toBeCloseTo(0.4);
    expect(anom[1]).toBeCloseTo(0.1);
  });

  it('どちらかが null なら null を返す', () => {
    const cur = [null, 6.1];
    const nor = [5.0,  null];
    const anom = calcAnomaly(cur, nor);
    expect(anom[0]).toBeNull();
    expect(anom[1]).toBeNull();
  });

  it('12 要素を返す', () => {
    const vals = Array(12).fill(10.0);
    expect(calcAnomaly(vals, vals)).toHaveLength(12);
  });
});

// ────────────────────────────────────────────────────────────────
// dailyNormRef
// ────────────────────────────────────────────────────────────────

describe('dailyNormRef', () => {
  const normals = [59.7, 56.5, 116.0, 133.5, 139.5, 167.8, 153.5, 167.8, 224.9, 197.8, 92.5, 57.6];

  it('avg モードはそのまま月平年値を返す', () => {
    expect(dailyNormRef(normals, 1, 31, 'avg')).toBe(59.7);
  });

  it('perday モードは月平年値 ÷ 日数を返す', () => {
    const expected = +(133.5 / 30).toFixed(2); // 4月
    expect(dailyNormRef(normals, 4, 30, 'perday')).toBe(expected);
  });

  it('月平年値が null なら null を返す', () => {
    const nullNormals = Array(12).fill(null);
    expect(dailyNormRef(nullNormals, 1, 31, 'perday')).toBeNull();
  });
});
