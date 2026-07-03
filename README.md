# Feature Store Mini

特徴量の **定義・更新頻度・欠損率・鮮度** を一覧し、特徴量管理と再現性の考え方を示す小型 Streamlit アプリです。

> **注意:** 本アプリのメタデータは **架空** であり、サンプルテーブルは **合成データ**（seed 固定で再現可能）です。実在の企業・データとは無関係です。

## 主要機能

- 特徴量カタログ（型・カテゴリ・owner・更新頻度）の一覧表示
- 特徴量ごとの **欠損率** の計算と可視化
- **鮮度**（最終更新からの経過日数）のフラグ表示
- カテゴリ / owner によるフィルタ
- 特徴量の詳細（定義・メタデータ）表示

## 使用技術

- Python 3.11+ / Streamlit / pandas / NumPy
- 集計ロジックは `src/catalog.py`、UI は `app/streamlit_app.py`（薄く保つ）

## データの出所

- 特徴量メタデータは架空の定義（`src/catalog.py` の `FEATURE_DEFS`）
- サンプルテーブルは seed 固定の合成データ（`generate_sample_frame`）

## ローカル実行手順

```bash
uv sync
uv run streamlit run app/streamlit_app.py
uv run pytest
```

`uv` を使わない場合は `pip install streamlit pandas numpy pytest` でも動きます。
`app/streamlit_app.py` は `sys.path` を補正しているため、editable install なしでも起動します。

## ディレクトリ構成

```
feature-store-mini/
├── app/streamlit_app.py   # Streamlit エントリ（UI）
├── src/catalog.py         # メタデータ・合成データ・欠損率・鮮度
├── src/brand.py           # 共通ブランドテーマ
├── tests/test_catalog.py  # 欠損率・再現性・境界のテスト
├── .streamlit/config.toml
└── pyproject.toml
```

## スクリーンショット

`assets/` に配置してください（現在は未配置）。

## 制限事項

- MVP であり、認証・DB・本番運用機能・課金は含みません
- 本格的な Feature Store（オンライン配信・バージョン管理・整合性保証）の代替ではなく、管理の考え方を示すデモです
- **架空メタデータ・合成データであり、実在の特徴量やデータ品質を示すものではありません**

## セキュリティ

- API キー等の秘密情報は使用しません（`.env` 不要で動作）
