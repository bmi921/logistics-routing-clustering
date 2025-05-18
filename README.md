# 🏢 営業所建設計画プロジェクト
5000世帯の東京の顧客にラストワンマイルで製品を届ける必要のある事業で、あなたは営業所の立地計画を担当することになった。
合理性のある理由で営業所の位置を計画する。
- 世帯をRでクラスター分析
- 巡回セールスマン問題としてORtoolsで局所最適化(最適解ではない)


<div align="center">

[![Notion Badge](https://img.shields.io/badge/Notion-詳細ドキュメント-000000?style=for-the-badge&logo=notion)](https://silent-felidae-1f6.notion.site/4-6-1e3d103bdc84809d948feaa3cd5e4bbd)
[![GitHub Pages Badge](https://img.shields.io/badge/GitHub_Pages-結果ビューア-222222?style=for-the-badge&logo=github)](https://bmi921.github.io/cvrp.html)

</div>


## 🛠️ 技術

<div align="center">

| 分析フェーズ | 使用技術 | バッジ |
|-------------|---------|-------|
| **クラスタリング** | R, cluster | ![R](https://img.shields.io/badge/R-276DC3?style=for-the-badge&logo=r&logoColor=white) |
| **座標計算** | Python | ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) |
| **ルート最適化** | OR-Tools | ![Google OR-Tools](https://img.shields.io/badge/Google_OR--Tools-4285F4?style=for-the-badge&logo=google&logoColor=white) |
| **可視化** | kepler.gl | ![kepler.gl](https://img.shields.io/badge/kepler.gl-000000?style=for-the-badge) |

</div>

## 🚀使い方
```
git clone https://github.com/bmi921/logistics-cluster-cvrp
cd ./logistics-cluster-cvrp
Rscript clsuter.r
python CVRP/calc_xy.py
python CVRP/cvrp.py
```
cluster.r → calc_xy.py → cvrp.py　の順で実行してください。中間生成ファイルのためです。

## 📂 ディレクトリ構成
```
logistics-cluster-cvrp/
├── 📂 data/          # 入力データセット
├── 📂 geojson   # keplerの表示のため 
├── 📂 CVRP/
│   ├── calc_xy.py    # 座標変換
│   └── cvrp.py       # ルート最適化
├── 📂 output       # 生成結果
├── cluster.r     # クラスター分析
├── 📜 .gitignore
├── 📜 LICENSE
└── 📜 README.md      # このファイル
```


<div align="center">

![GitHub last commit](https://img.shields.io/github/last-commit/bmi921/logistics-cluster-cvrp?style=flat-square)
![GitHub repo size](https://img.shields.io/github/repo-size/bmi921/logistics-cluster-cvrp?style=flat-square)
![GitHub issues](https://img.shields.io/github/issues/bmi921/logistics-cluster-cvrp?style=flat-square)

</div>
