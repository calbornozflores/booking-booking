import math

import pandas as pd

DEFAULT_RATING_WEIGHT = 0.6
DEFAULT_PRICE_WEIGHT = 0.4
REVIEW_COUNT_CAP = 500
MIN_CONFIDENCE = 0.3
DEFAULT_TOP_K = 3


def split_by_currency(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Group listings by currency ('Unknown' for missing). Prices are only
    ever comparable within the same currency - callers must score/rank each
    group independently, never together."""
    currencies = df["currency"].fillna("Unknown")
    return {currency: df[currencies == currency].copy() for currency in currencies.unique()}


def _confidence(review_count: float | None) -> float:
    """Log-scaled confidence weight from review count: raw counts range from
    single digits to many thousands, so a linear weight would let a handful
    of very-high-review listings dominate. Missing/zero review counts get a
    floor (discounted, not discarded) rather than zero, since a listing can
    have a genuinely good rating/price with just an unparsed review count."""
    if review_count is None or pd.isna(review_count) or review_count <= 0:
        return MIN_CONFIDENCE
    return min(1.0, math.log1p(review_count) / math.log1p(REVIEW_COUNT_CAP))


def score_listings(
    df: pd.DataFrame,
    rating_weight: float = DEFAULT_RATING_WEIGHT,
    price_weight: float | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rank listings by value-for-money within a single currency group.

    Returns (scored, excluded): scored has value_score/rank/is_best_value/
    is_price_outlier columns, sorted best-first. excluded holds listings
    missing price or rating - these aren't imputed, since a recommendation
    for an unrated or unpriced listing isn't verifiable against the site.
    """
    if price_weight is None:
        price_weight = 1 - rating_weight

    has_price = df["price"].notna() & (df["price"] > 0)
    has_rating = df["rating_value"].notna()
    eligible = has_price & has_rating

    scored = df[eligible].copy()
    excluded = df[~eligible].copy()
    if not excluded.empty:
        reasons = []
        for _, row in excluded.iterrows():
            missing = []
            if not (pd.notna(row["price"]) and row["price"] > 0):
                missing.append("price")
            if pd.isna(row["rating_value"]):
                missing.append("rating")
            reasons.append(f"missing {'/'.join(missing)}")
        excluded["excluded_reason"] = reasons

    if scored.empty:
        for col in ("value_score", "rank", "is_best_value", "is_price_outlier"):
            scored[col] = []
        return scored, excluded

    price_min, price_max = scored["price"].min(), scored["price"].max()
    if price_max > price_min:
        price_norm = 1 - (scored["price"] - price_min) / (price_max - price_min)
    else:
        price_norm = pd.Series(1.0, index=scored.index)

    rating_norm = scored["rating_value"] / 10.0
    confidence = scored["review_count"].apply(_confidence)

    scored["value_score"] = (rating_norm * rating_weight + price_norm * price_weight) * confidence
    scored = scored.sort_values("value_score", ascending=False).reset_index(drop=True)
    scored["rank"] = scored.index + 1
    scored["is_best_value"] = scored["rank"] <= top_k

    q1, q3 = scored["price"].quantile(0.25), scored["price"].quantile(0.75)
    iqr = q3 - q1
    scored["is_price_outlier"] = (scored["price"] < q1 - 1.5 * iqr) if iqr > 0 else False

    return scored, excluded
