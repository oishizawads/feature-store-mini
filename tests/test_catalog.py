"""feature-store-mini のロジックテスト。"""

import numpy as np
import pandas as pd
import pytest

from src.catalog import (
    FEATURE_DEFS,
    build_catalog,
    freshness_flag,
    generate_sample_frame,
    missing_rates,
)


def test_missing_rates_known_frame():
    df = pd.DataFrame({"a": [1.0, np.nan, 3.0, np.nan], "b": [1.0, 2.0, 3.0, 4.0]})
    mr = missing_rates(df).set_index("feature")["missing_rate"].to_dict()
    assert mr["a"] == pytest.approx(0.5)
    assert mr["b"] == pytest.approx(0.0)


def test_missing_rates_all_nan_column():
    df = pd.DataFrame({"a": [np.nan, np.nan, np.nan]})
    mr = missing_rates(df).set_index("feature")["missing_rate"].to_dict()
    assert mr["a"] == pytest.approx(1.0)


def test_missing_rates_empty_frame_safe():
    out = missing_rates(pd.DataFrame())
    assert list(out.columns) == ["feature", "missing_rate"]
    assert len(out) == 0


def test_generate_sample_frame_reproducible():
    a = generate_sample_frame(n=200, seed=7)
    b = generate_sample_frame(n=200, seed=7)
    pd.testing.assert_frame_equal(a, b)


def test_generate_sample_frame_zero_rows():
    out = generate_sample_frame(n=0)
    assert out.empty
    assert len(out.columns) == len(FEATURE_DEFS)


def test_build_catalog_one_row_per_feature():
    cat = build_catalog(seed=1, n=300)
    assert len(cat) == len(FEATURE_DEFS)
    assert set(cat["feature"]) == {f.name for f in FEATURE_DEFS}
    assert cat["missing_rate"].between(0.0, 1.0).all()


def test_build_catalog_reflects_configured_missing():
    # ltv_estimate は欠損率が高めに設定されている → 0 より大きい
    cat = build_catalog(seed=42, n=1000).set_index("feature")
    assert cat.loc["ltv_estimate", "missing_rate"] > 0.0
    assert cat.loc["days_since_signup", "missing_rate"] == pytest.approx(0.0)


def test_freshness_flag_levels():
    assert "fresh" in freshness_flag(0)
    assert "ok" in freshness_flag(5)
    assert "stale" in freshness_flag(30)
