"""
テスト用 HTML フィクスチャ。
実際の気象庁 ETRN ページを参考に最小限の構造を再現したサンプル HTML。
"""

# ── 月別観測値テーブル (monthly_s1.php 相当) ─────────────────────────────────
MONTHLY_HTML = """
<html><body>
<table>
  <tr>
    <th rowspan="2">月</th>
    <th colspan="2">気温(℃)</th>
    <th colspan="2">降水量(mm)</th>
    <th>日射量</th>
  </tr>
  <tr>
    <th>平均</th><th>最高</th>
    <th>合計</th><th>最大</th>
    <th>日射量(MJ/m²)</th>
  </tr>
  <tr><td>1</td><td>5.4</td><td>9.2</td><td>80.5</td><td>30.2</td><td>282.5</td></tr>
  <tr><td>2</td><td>6.1</td><td>10.5</td><td>45.5</td><td>28.0</td><td>230.5</td></tr>
  <tr><td>3</td><td>10.8</td><td>15.3</td><td>118.0</td><td>35.5</td><td>330.0</td></tr>
  <tr><td>4</td><td>15.2</td><td>20.1</td><td>95.5</td><td>40.0</td><td>390.5</td></tr>
  <tr><td>5</td><td>19.7</td><td>24.5</td><td>163.5</td><td>55.0</td><td>410.0</td></tr>
  <tr><td>6</td><td>−</td><td>−</td><td>−</td><td>−</td><td>−</td></tr>
  <tr><td>7</td><td>−</td><td>−</td><td>−</td><td>−</td><td>−</td></tr>
  <tr><td>8</td><td>−</td><td>−</td><td>−</td><td>−</td><td>−</td></tr>
  <tr><td>9</td><td>−</td><td>−</td><td>−</td><td>−</td><td>−</td></tr>
  <tr><td>10</td><td>−</td><td>−</td><td>−</td><td>−</td><td>−</td></tr>
  <tr><td>11</td><td>−</td><td>−</td><td>−</td><td>−</td><td>−</td></tr>
  <tr><td>12</td><td>−</td><td>−</td><td>−</td><td>−</td><td>−</td></tr>
</table>
</body></html>
"""

# ── 平年値テーブル (nml_sfc_ym.php 相当) ─────────────────────────────────────
NORMALS_HTML = """
<html><body>
<table>
  <tr>
    <th rowspan="2">月</th>
    <th colspan="2">気温(℃)</th>
    <th colspan="2">降水量(mm)</th>
    <th>日射量</th>
  </tr>
  <tr>
    <th>平均</th><th>最高</th>
    <th>合計</th><th>最大</th>
    <th>日射量(MJ/m²)</th>
  </tr>
  <tr><td>1</td><td>5.4</td><td>9.2</td><td>59.7</td><td>20.0</td><td>255.0</td></tr>
  <tr><td>2</td><td>6.1</td><td>10.5</td><td>56.5</td><td>22.0</td><td>230.5</td></tr>
  <tr><td>3</td><td>9.4</td><td>14.0</td><td>116.0</td><td>30.0</td><td>340.5</td></tr>
  <tr><td>4</td><td>14.3</td><td>19.0</td><td>133.5</td><td>35.0</td><td>390.0</td></tr>
  <tr><td>5</td><td>18.9</td><td>23.5</td><td>139.5</td><td>40.0</td><td>420.5</td></tr>
  <tr><td>6</td><td>22.4</td><td>27.0</td><td>167.8</td><td>50.0</td><td>380.0</td></tr>
  <tr><td>7</td><td>25.7</td><td>30.0</td><td>153.5</td><td>60.0</td><td>390.5</td></tr>
  <tr><td>8</td><td>26.9</td><td>31.5</td><td>167.8</td><td>65.0</td><td>410.0</td></tr>
  <tr><td>9</td><td>23.3</td><td>28.0</td><td>224.9</td><td>70.0</td><td>300.5</td></tr>
  <tr><td>10</td><td>17.8</td><td>22.5</td><td>197.8</td><td>55.0</td><td>280.5</td></tr>
  <tr><td>11</td><td>12.5</td><td>17.0</td><td>92.5</td><td>35.0</td><td>230.5</td></tr>
  <tr><td>12</td><td>7.7</td><td>12.0</td><td>57.6</td><td>25.0</td><td>220.0</td></tr>
</table>
</body></html>
"""

# ── 日別観測値テーブル (daily_s1.php 相当) ────────────────────────────────────
DAILY_HTML = """
<html><body>
<table>
  <tr>
    <th rowspan="2">日</th>
    <th colspan="2">気温(℃)</th>
    <th colspan="2">降水量(mm)</th>
    <th>日射量</th>
  </tr>
  <tr>
    <th>平均</th><th>最高</th>
    <th>合計</th><th>最大</th>
    <th>日射量(MJ/m²)</th>
  </tr>
  <tr><td>1</td><td>12.5</td><td>16.0</td><td>0.0</td><td>0.0</td><td>18.5</td></tr>
  <tr><td>2</td><td>13.2</td><td>17.5</td><td>5.5</td><td>3.0</td><td>12.0</td></tr>
  <tr><td>3</td><td>11.0</td><td>15.0</td><td>0.0</td><td>0.0</td><td>20.5</td></tr>
  <tr><td>4</td><td>−</td><td>−</td><td>−</td><td>−</td><td>−</td></tr>
</table>
</body></html>
"""

# ── テーブルなしページ ────────────────────────────────────────────────────────
EMPTY_HTML = "<html><body><p>データなし</p></body></html>"

# ── コンマ区切り値を含むテーブル ──────────────────────────────────────────────
MONTHLY_WITH_COMMA_HTML = """
<html><body>
<table>
  <tr>
    <th rowspan="2">月</th>
    <th>気温(℃)_平均</th>
    <th>降水量(mm)_合計</th>
    <th>日射量(MJ/m²)</th>
  </tr>
  <tr>
    <th></th><th></th><th></th>
  </tr>
  <tr><td>1</td><td>5.4</td><td>1,234.5</td><td>282.5</td></tr>
  <tr><td>2</td><td>6.1</td><td>56.5</td><td>230.5</td></tr>
</table>
</body></html>
"""
