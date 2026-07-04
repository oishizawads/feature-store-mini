"""Feature Store Mini — Streamlit エントリポイント。

UI は薄く保ち、集計ロジックは src/ に委譲する。
実行: streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.brand import (
    apply_brand,
    footer_backlink,
    hero,
    section,
    sidebar_header,
    themed_altair,
    show_table,
)
from src.catalog import (
    FEATURE_DEFS,
    build_catalog,
    freshness_flag,
    generate_sample_frame,
)

st.set_page_config(page_title="Feature Store Mini", page_icon="🗂️", layout="wide")
apply_brand(st)
themed_altair(alt)


@st.cache_data(show_spinner=False)
def _catalog(seed: int, n: int) -> pd.DataFrame:
    return build_catalog(seed=seed, n=n)


@st.cache_data(show_spinner=False)
def _frame(seed: int, n: int) -> pd.DataFrame:
    return generate_sample_frame(n=n, seed=seed)


def main() -> None:
    sidebar_header(st, "Feature Store Mini")
    seed = st.sidebar.number_input("シード", min_value=0, max_value=9999, value=42, step=1)
    n = st.sidebar.slider("サンプル行数", 50, 2000, 500, 50)
    categories = sorted({f.category for f in FEATURE_DEFS})
    owners = sorted({f.owner for f in FEATURE_DEFS})
    cat_sel = st.sidebar.multiselect("カテゴリで絞り込み", categories, default=categories)
    owner_sel = st.sidebar.multiselect("owner で絞り込み", owners, default=owners)

    hero(
        st,
        "FEATURE STORE",
        "Feature Store Mini",
        "特徴量の定義・更新頻度・欠損率・鮮度を一覧し、特徴量管理と再現性の考え方を示します。",
        chips=["Python", "Pandas", "Altair", "Feature Management"],
    )

    catalog = _catalog(int(seed), int(n)).copy()
    catalog = catalog[
        catalog["category"].isin(cat_sel) & catalog["owner"].isin(owner_sel)
    ]

    if catalog.empty:
        st.info("フィルタに該当する特徴量がありません。カテゴリ / owner の選択を見直してください。")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("特徴量数", len(catalog))
    c2.metric("平均欠損率", f"{catalog['missing_rate'].mean():.1%}")
    c3.metric("stale 特徴量数", int((catalog["freshness_days"] > 7).sum()))
    c4.metric("owner 数", catalog["owner"].nunique())

    st.divider()
    section(st, "FEATURE CATALOG", "特徴量カタログ")
    view = catalog.copy()
    view["鮮度"] = view["freshness_days"].map(lambda d: freshness_flag(int(d)))
    view["欠損率"] = view["missing_rate"].map(lambda r: f"{r:.1%}")
    view = view.rename(
        columns={
            "feature": "特徴量", "dtype": "型", "category": "カテゴリ",
            "owner": "owner", "update_freq": "更新頻度", "freshness_days": "経過日数",
        }
    )[["特徴量", "型", "カテゴリ", "owner", "更新頻度", "経過日数", "鮮度", "欠損率"]]
    show_table(st, view)

    section(st, "FEATURE STATS", "欠損率（特徴量別）")
    bar_data = catalog[["feature", "missing_rate"]].copy()
    chart = (
        alt.Chart(bar_data)
        .mark_bar()
        .encode(
            x=alt.X(
                "missing_rate:Q",
                axis=alt.Axis(format="%", title="欠損率"),
                scale=alt.Scale(domainMin=0),
            ),
            y=alt.Y("feature:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("feature:N", title="特徴量"),
                alt.Tooltip("missing_rate:Q", format=".1%", title="欠損率"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(chart, width="stretch")

    section(st, "FEATURE DETAIL", "特徴量の詳細")
    names = list(catalog["feature"])
    pick = st.selectbox("特徴量を選択", names)
    fdef = next((f for f in FEATURE_DEFS if f.name == pick), None)
    if fdef is not None:
        st.markdown(
            f"**{fdef.name}** — {fdef.definition}\n\n"
            f"- 型: `{fdef.dtype}` / カテゴリ: `{fdef.category}` / owner: `{fdef.owner}`\n"
            f"- 更新頻度: `{fdef.update_freq}` / 鮮度: {freshness_flag(fdef.freshness_days)}"
        )

    footer_backlink(st, repo="feature-store-mini")


if __name__ == "__main__":
    main()
