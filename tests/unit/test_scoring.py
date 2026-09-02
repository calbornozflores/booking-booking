import pandas as pd
import pytest

from booking_booking.scoring import score_listings, split_by_currency


def _df(rows: list[dict]) -> pd.DataFrame:
    columns = ["name", "price", "currency", "rating_value", "review_count"]
    return pd.DataFrame(rows, columns=columns)


def test_missing_price_excluded_from_ranking():
    df = _df(
        [
            {"name": "A", "price": None, "currency": "€", "rating_value": 8.0, "review_count": 100},
            {"name": "B", "price": 100.0, "currency": "€", "rating_value": 8.0, "review_count": 100},
        ]
    )

    scored, excluded = score_listings(df)

    assert list(scored["name"]) == ["B"]
    assert list(excluded["name"]) == ["A"]
    assert "price" in excluded.iloc[0]["excluded_reason"]


def test_missing_rating_excluded_from_ranking():
    df = _df(
        [
            {"name": "A", "price": 100.0, "currency": "€", "rating_value": None, "review_count": 100},
            {"name": "B", "price": 100.0, "currency": "€", "rating_value": 8.0, "review_count": 100},
        ]
    )

    scored, excluded = score_listings(df)

    assert list(scored["name"]) == ["B"]
    assert "rating" in excluded.iloc[0]["excluded_reason"]


def test_higher_rating_and_lower_price_ranks_higher():
    df = _df(
        [
            {"name": "Best", "price": 50.0, "currency": "€", "rating_value": 9.5, "review_count": 200},
            {"name": "Worst", "price": 300.0, "currency": "€", "rating_value": 6.0, "review_count": 200},
        ]
    )

    scored, _ = score_listings(df)

    assert list(scored["name"]) == ["Best", "Worst"]
    assert scored.iloc[0]["rank"] == 1


def test_low_review_count_gets_lower_confidence_at_equal_rating_and_price():
    df = _df(
        [
            {
                "name": "Many reviews",
                "price": 100.0,
                "currency": "€",
                "rating_value": 8.0,
                "review_count": 500,
            },
            {"name": "Few reviews", "price": 100.0, "currency": "€", "rating_value": 8.0, "review_count": 1},
        ]
    )

    scored, _ = score_listings(df)

    many = scored.set_index("name").loc["Many reviews", "value_score"]
    few = scored.set_index("name").loc["Few reviews", "value_score"]
    assert many > few


def test_missing_review_count_gets_floor_confidence_not_excluded():
    df = _df(
        [
            {
                "name": "No review count",
                "price": 100.0,
                "currency": "€",
                "rating_value": 8.0,
                "review_count": None,
            }
        ]
    )

    scored, excluded = score_listings(df)

    assert len(scored) == 1
    assert excluded.empty


def test_mixed_currency_groups_scored_independently():
    # Same rating/review_count, wildly different price scales (100 vs 1000).
    # Each is the sole listing in its currency group, so price should
    # normalize to 1.0 *within its own group* regardless of absolute price -
    # proving price scale is never compared across currencies.
    df = _df(
        [
            {"name": "Euro hotel", "price": 100.0, "currency": "€", "rating_value": 8.0, "review_count": 100},
            {
                "name": "Dollar hotel",
                "price": 1000.0,
                "currency": "$",
                "rating_value": 8.0,
                "review_count": 100,
            },
        ]
    )

    groups = split_by_currency(df)
    assert set(groups.keys()) == {"€", "$"}

    scores = {}
    for currency, group in groups.items():
        scored, _ = score_listings(group)
        scores[currency] = scored.iloc[0]["value_score"]

    assert scores["€"] == pytest.approx(scores["$"])


def test_split_by_currency_groups_missing_currency_as_unknown():
    df = _df(
        [
            {
                "name": "No currency",
                "price": 100.0,
                "currency": None,
                "rating_value": 8.0,
                "review_count": 100,
            },
        ]
    )

    groups = split_by_currency(df)

    assert "Unknown" in groups
    assert list(groups["Unknown"]["name"]) == ["No currency"]


def test_best_value_badge_flags_top_k():
    df = _df(
        [
            {
                "name": f"Hotel {i}",
                "price": 100.0 + i * 10,
                "currency": "€",
                "rating_value": 8.0,
                "review_count": 200,
            }
            for i in range(5)
        ]
    )

    scored, _ = score_listings(df, top_k=2)

    assert scored["is_best_value"].sum() == 2
    assert list(scored[scored["is_best_value"]]["rank"]) == [1, 2]


def test_price_outlier_flagging():
    df = _df(
        [
            {"name": "Normal 1", "price": 100.0, "currency": "€", "rating_value": 8.0, "review_count": 100},
            {"name": "Normal 2", "price": 110.0, "currency": "€", "rating_value": 8.0, "review_count": 100},
            {"name": "Normal 3", "price": 105.0, "currency": "€", "rating_value": 8.0, "review_count": 100},
            {"name": "Normal 4", "price": 95.0, "currency": "€", "rating_value": 8.0, "review_count": 100},
            {
                "name": "Suspiciously cheap",
                "price": 1.0,
                "currency": "€",
                "rating_value": 8.0,
                "review_count": 100,
            },
        ]
    )

    scored, _ = score_listings(df)

    outlier_row = scored.set_index("name").loc["Suspiciously cheap"]
    assert bool(outlier_row["is_price_outlier"]) is True


def test_all_equal_prices_normalize_without_error():
    df = _df(
        [
            {"name": "A", "price": 100.0, "currency": "€", "rating_value": 8.0, "review_count": 100},
            {"name": "B", "price": 100.0, "currency": "€", "rating_value": 7.0, "review_count": 100},
        ]
    )

    scored, _ = score_listings(df)

    assert list(scored["name"]) == ["A", "B"]
