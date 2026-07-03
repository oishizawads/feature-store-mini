"""特徴量カタログのメタデータと合成サンプルテーブルの生成・集計。

UI から切り離した純粋ロジック。すべて合成データ（seed 固定で再現可能）。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FeatureDef:
    name: str
    dtype: str
    category: str
    owner: str
    update_freq: str
    freshness_days: int  # 最終更新からの経過日数
    definition: str


# 架空の特徴量メタデータ（実在の企業・データとは無関係）
FEATURE_DEFS: list[FeatureDef] = [
    FeatureDef("user_age", "int", "user", "growth-team", "daily", 1,
               "利用者の年齢（登録情報から算出）"),
    FeatureDef("days_since_signup", "int", "user", "growth-team", "daily", 1,
               "登録からの経過日数"),
    FeatureDef("sessions_7d", "int", "activity", "product-team", "hourly", 0,
               "直近7日のセッション数"),
    FeatureDef("avg_session_minutes", "float", "activity", "product-team", "hourly", 0,
               "1セッションあたり平均滞在分数"),
    FeatureDef("purchases_30d", "int", "revenue", "revenue-team", "daily", 2,
               "直近30日の購入回数"),
    FeatureDef("ltv_estimate", "float", "revenue", "ds-team", "weekly", 6,
               "推定生涯価値（簡易モデル出力）"),
    FeatureDef("is_premium", "bool", "revenue", "revenue-team", "daily", 1,
               "有料プラン加入フラグ"),
    FeatureDef("region", "category", "user", "growth-team", "monthly", 20,
               "利用者の地域区分（一般化済み）"),
    FeatureDef("device_type", "category", "activity", "product-team", "daily", 1,
               "主要利用デバイス種別"),
    FeatureDef("churn_score", "float", "ml", "ds-team", "daily", 3,
               "解約予測スコア（0..1、モデル出力）"),
]

# 特徴量ごとの想定欠損率（合成データ生成用）
_MISSING_RATE = {
    "user_age": 0.02, "days_since_signup": 0.0, "sessions_7d": 0.01,
    "avg_session_minutes": 0.05, "purchases_30d": 0.03, "ltv_estimate": 0.12,
    "is_premium": 0.0, "region": 0.08, "device_type": 0.04, "churn_score": 0.15,
}


def generate_sample_frame(n: int = 500, seed: int = 42) -> pd.DataFrame:
    """カタログ定義に沿った合成サンプルテーブルを返す（seed 固定で再現可能）。"""
    if n <= 0:
        return pd.DataFrame(columns=[f.name for f in FEATURE_DEFS])
    rng = np.random.default_rng(seed)
    cols: dict[str, np.ndarray] = {}
    for f in FEATURE_DEFS:
        if f.name == "user_age":
            v = rng.integers(18, 70, n).astype(float)
        elif f.name == "days_since_signup":
            v = rng.integers(0, 900, n).astype(float)
        elif f.name == "sessions_7d":
            v = rng.poisson(5, n).astype(float)
        elif f.name == "avg_session_minutes":
            v = np.round(rng.gamma(2.0, 4.0, n), 2)
        elif f.name == "purchases_30d":
            v = rng.poisson(1.2, n).astype(float)
        elif f.name == "ltv_estimate":
            v = np.round(rng.gamma(3.0, 40.0, n), 2)
        elif f.name == "is_premium":
            v = rng.random(n) < 0.22
            v = v.astype(object)
        elif f.name == "region":
            v = rng.choice(["north", "south", "east", "west"], n).astype(object)
        elif f.name == "device_type":
            v = rng.choice(["ios", "android", "web"], n).astype(object)
        elif f.name == "churn_score":
            v = np.round(rng.beta(2.0, 5.0, n), 3)
        else:  # pragma: no cover - 定義漏れの保険
            v = rng.random(n)

        # 欠損の注入
        rate = _MISSING_RATE.get(f.name, 0.0)
        if rate > 0:
            mask = rng.random(n) < rate
            v = pd.Series(v)
            v[mask] = np.nan
            cols[f.name] = v.to_numpy()
        else:
            cols[f.name] = np.asarray(v)
    return pd.DataFrame(cols)


def missing_rates(df: pd.DataFrame) -> pd.DataFrame:
    """列ごとの欠損率を返す（feature, missing_rate）。空データでも落ちない。"""
    if df is None or df.empty or df.shape[1] == 0:
        return pd.DataFrame(columns=["feature", "missing_rate"])
    rates = df.isna().mean()
    return pd.DataFrame(
        {"feature": rates.index, "missing_rate": rates.to_numpy(dtype=float)}
    )


def build_catalog(seed: int = 42, n: int = 500) -> pd.DataFrame:
    """メタデータ + 実測欠損率 + 鮮度をまとめた特徴量カタログを返す。"""
    df = generate_sample_frame(n=n, seed=seed)
    mr = dict(zip(*[missing_rates(df)[c] for c in ("feature", "missing_rate")])) if not df.empty else {}
    rows = []
    for f in FEATURE_DEFS:
        rows.append(
            {
                "feature": f.name,
                "dtype": f.dtype,
                "category": f.category,
                "owner": f.owner,
                "update_freq": f.update_freq,
                "freshness_days": f.freshness_days,
                "missing_rate": float(mr.get(f.name, 0.0)),
            }
        )
    return pd.DataFrame(rows)


def freshness_flag(freshness_days: int, threshold: int = 7) -> str:
    """鮮度を人間可読なフラグに変換する。"""
    if freshness_days <= 1:
        return "🟢 fresh"
    if freshness_days <= threshold:
        return "🟡 ok"
    return "🔴 stale"
