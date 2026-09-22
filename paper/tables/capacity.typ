// 本檔由 paper/make_table_typst.py 自動產生，請勿手動編輯。
// 資料來源：ml/out/s16_capacity_final_5seed.json
// 產生時間：2026-09-20 23:48 ｜ 跑滿 5 個種子的格數：64/64 ｜ partial=False

#figure(
  table(
    columns: 4,
    table.header([*qubit 數* $n$], [*$L$ = 4*], [*$L$ = 6*], [*$L$ = 8*]),
    [$3$], [0.4953 #text(size: 6.8pt, fill: gray)[+/- 0.0763]], [0.5813 #text(size: 6.8pt, fill: gray)[+/- 0.0148]], [0.5733 #text(size: 6.8pt, fill: gray)[+/- 0.0097]],
    [$4$], [0.5593 #text(size: 6.8pt, fill: gray)[+/- 0.0607]], [0.6146 #text(size: 6.8pt, fill: gray)[+/- 0.0307]], [0.6253 #text(size: 6.8pt, fill: gray)[+/- 0.0192]],
    [$5$], [0.5213 #text(size: 6.8pt, fill: gray)[+/- 0.0666]], [0.6080 #text(size: 6.8pt, fill: gray)[+/- 0.0393]], [0.6133 #text(size: 6.8pt, fill: gray)[+/- 0.0440]],
    [$6$], [0.4133 #text(size: 6.8pt, fill: gray)[+/- 0.0989]], [0.5453 #text(size: 6.8pt, fill: gray)[+/- 0.0529]], [0.5927 #text(size: 6.8pt, fill: gray)[+/- 0.0134]],
    [$7$], [0.4527 #text(size: 6.8pt, fill: gray)[+/- 0.0549]], [0.5720 #text(size: 6.8pt, fill: gray)[+/- 0.0276]], [0.5760 #text(size: 6.8pt, fill: gray)[+/- 0.0747]],
    [$8$], [0.3260 #text(size: 6.8pt, fill: gray)[+/- 0.0613]], [0.5460 #text(size: 6.8pt, fill: gray)[+/- 0.0352]], [0.5647 #text(size: 6.8pt, fill: gray)[+/- 0.0229]],
    [$9$], [0.4160 #text(size: 6.8pt, fill: gray)[+/- 0.0996]], [0.4760 #text(size: 6.8pt, fill: gray)[+/- 0.0922]], [0.5240 #text(size: 6.8pt, fill: gray)[+/- 0.1110]],
    [$10$], [0.3707 #text(size: 6.8pt, fill: gray)[+/- 0.1300]], [0.4347 #text(size: 6.8pt, fill: gray)[+/- 0.0922]], [0.5207 #text(size: 6.8pt, fill: gray)[+/- 0.0522]],
  ),
  caption: [固定深度下，測試準確率隨 qubit 數的變化（五個種子的平均值；
    灰色小字為標準差）。$n = 3$ 偏低是結構性的——$8$ 個類別最少需要
    $3$ 個 qubit 的投影讀出，該點剛好打滿——因此主張寫成「自 $n = 4$ 起」。
],
) <tab:slices>

#figure(
  text(size: 7pt)[
    #table(
      columns: 9,
      table.header([$n$ / $L$], [1], [2], [3], [4], [5], [6], [7], [8]),
      [$3$], [0.131 #text(size: 5.8pt, fill: gray)[(0.054)]], [0.205 #text(size: 5.8pt, fill: gray)[(0.018)]], [0.431 #text(size: 5.8pt, fill: gray)[(0.049)]], [0.495 #text(size: 5.8pt, fill: gray)[(0.076)]], [0.554 #text(size: 5.8pt, fill: gray)[(0.045)]], [0.581 #text(size: 5.8pt, fill: gray)[(0.015)]], [0.570 #text(size: 5.8pt, fill: gray)[(0.006)]], [0.573 #text(size: 5.8pt, fill: gray)[(0.010)]],
      [$4$], [0.137 #text(size: 5.8pt, fill: gray)[(0.013)]], [0.323 #text(size: 5.8pt, fill: gray)[(0.078)]], [0.440 #text(size: 5.8pt, fill: gray)[(0.090)]], [0.559 #text(size: 5.8pt, fill: gray)[(0.061)]], [0.599 #text(size: 5.8pt, fill: gray)[(0.017)]], [0.615 #text(size: 5.8pt, fill: gray)[(0.031)]], [0.619 #text(size: 5.8pt, fill: gray)[(0.035)]], [0.625 #text(size: 5.8pt, fill: gray)[(0.019)]],
      [$5$], [0.204 #text(size: 5.8pt, fill: gray)[(0.031)]], [0.331 #text(size: 5.8pt, fill: gray)[(0.044)]], [0.459 #text(size: 5.8pt, fill: gray)[(0.087)]], [0.521 #text(size: 5.8pt, fill: gray)[(0.067)]], [0.612 #text(size: 5.8pt, fill: gray)[(0.067)]], [0.608 #text(size: 5.8pt, fill: gray)[(0.039)]], [0.622 #text(size: 5.8pt, fill: gray)[(0.047)]], [0.613 #text(size: 5.8pt, fill: gray)[(0.044)]],
      [$6$], [0.227 #text(size: 5.8pt, fill: gray)[(0.005)]], [0.147 #text(size: 5.8pt, fill: gray)[(0.022)]], [0.421 #text(size: 5.8pt, fill: gray)[(0.062)]], [0.413 #text(size: 5.8pt, fill: gray)[(0.099)]], [0.516 #text(size: 5.8pt, fill: gray)[(0.029)]], [0.545 #text(size: 5.8pt, fill: gray)[(0.053)]], [0.598 #text(size: 5.8pt, fill: gray)[(0.020)]], [0.593 #text(size: 5.8pt, fill: gray)[(0.013)]],
      [$7$], [0.197 #text(size: 5.8pt, fill: gray)[(0.018)]], [0.392 #text(size: 5.8pt, fill: gray)[(0.081)]], [0.351 #text(size: 5.8pt, fill: gray)[(0.034)]], [0.453 #text(size: 5.8pt, fill: gray)[(0.055)]], [0.399 #text(size: 5.8pt, fill: gray)[(0.065)]], [0.572 #text(size: 5.8pt, fill: gray)[(0.028)]], [0.545 #text(size: 5.8pt, fill: gray)[(0.072)]], [0.576 #text(size: 5.8pt, fill: gray)[(0.075)]],
      [$8$], [0.196 #text(size: 5.8pt, fill: gray)[(0.022)]], [0.279 #text(size: 5.8pt, fill: gray)[(0.022)]], [0.352 #text(size: 5.8pt, fill: gray)[(0.125)]], [0.326 #text(size: 5.8pt, fill: gray)[(0.061)]], [0.501 #text(size: 5.8pt, fill: gray)[(0.069)]], [0.546 #text(size: 5.8pt, fill: gray)[(0.035)]], [0.503 #text(size: 5.8pt, fill: gray)[(0.111)]], [0.565 #text(size: 5.8pt, fill: gray)[(0.023)]],
      [$9$], [0.163 #text(size: 5.8pt, fill: gray)[(0.031)]], [0.322 #text(size: 5.8pt, fill: gray)[(0.010)]], [0.316 #text(size: 5.8pt, fill: gray)[(0.055)]], [0.416 #text(size: 5.8pt, fill: gray)[(0.100)]], [0.411 #text(size: 5.8pt, fill: gray)[(0.100)]], [0.476 #text(size: 5.8pt, fill: gray)[(0.092)]], [0.444 #text(size: 5.8pt, fill: gray)[(0.029)]], [0.524 #text(size: 5.8pt, fill: gray)[(0.111)]],
      [$10$], [0.182 #text(size: 5.8pt, fill: gray)[(0.016)]], [0.219 #text(size: 5.8pt, fill: gray)[(0.077)]], [0.340 #text(size: 5.8pt, fill: gray)[(0.075)]], [0.371 #text(size: 5.8pt, fill: gray)[(0.130)]], [0.434 #text(size: 5.8pt, fill: gray)[(0.085)]], [0.435 #text(size: 5.8pt, fill: gray)[(0.092)]], [0.478 #text(size: 5.8pt, fill: gray)[(0.092)]], [0.521 #text(size: 5.8pt, fill: gray)[(0.052)]],
    )
  ],
  caption: [完整的 $(n, L)$ 網格：五個種子的測試準確率平均值，
    括號內為標準差。「—」表示該格未跑滿五個種子；未跑滿的格子不並入統計，
    以免單一種子的「標準差 $0$」與五個種子的標準差混為一談。
],
) <tab:grid>
