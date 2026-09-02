import streamlit as st

from booking_booking import scoring, storage
from booking_booking.webapp import theme

DISPLAY_COLUMNS = [
    "rank",
    "name",
    "area",
    "distance_from_centre",
    "price",
    "currency",
    "rating_value",
    "rating_description",
    "review_count",
    "value_score",
    "is_best_value",
    "is_price_outlier",
]


def _run_label(row) -> str:
    dates = f"{row['arrival_date']} → {row['departure_date']}"
    return f"#{row['id']} · {row['city']} · {dates} · {row['executed_at']}"


def _highlight_best_value(row):
    color = f"background-color: {theme.tint(theme.GREEN)}" if row["is_best_value"] else ""
    return [color] * len(row)


def _download_bytes(df, fmt: str) -> bytes:
    if fmt == "json":
        return df.to_json(orient="records", indent=2, date_format="iso").encode("utf-8")
    return df.to_csv(index=False).encode("utf-8")


def render() -> None:
    st.title("📊 Analyzer")

    conn = storage.get_connection()
    storage.init_db(conn)

    searches_df = storage.list_searches(conn)
    if searches_df.empty:
        st.info("No saved searches yet - run a search on the Home page first.")
        st.stop()

    searches_df["label"] = searches_df.apply(_run_label, axis=1)
    labels = list(searches_df["label"])

    selected_labels = st.multiselect("Select search run(s) to analyze", options=labels, default=labels[:1])
    if not selected_labels:
        st.info("Select at least one search run to analyze.")
        st.stop()

    selected_ids = searches_df[searches_df["label"].isin(selected_labels)]["id"].tolist()
    listings_df = storage.get_listings_for_searches(conn, selected_ids)

    if listings_df.empty:
        st.info("No listings found for the selected run(s).")
        st.stop()

    with st.expander("Additional filters"):
        min_rating = st.slider("Minimum rating", 0.0, 10.0, 0.0, 0.5)
        max_price = st.number_input("Maximum price (0 = no limit)", min_value=0.0, value=0.0, step=10.0)
        city_filter = st.text_input("Area contains")

    if min_rating > 0:
        listings_df = listings_df[listings_df["rating_value"].fillna(0) >= min_rating]
    if max_price > 0:
        listings_df = listings_df[listings_df["price"].fillna(float("inf")) <= max_price]
    if city_filter.strip():
        listings_df = listings_df[
            listings_df["area"].fillna("").str.contains(city_filter.strip(), case=False)
        ]

    if listings_df.empty:
        st.info("No listings match the current filters.")
        st.stop()

    st.subheader("Listings")
    st.caption("Optionally select individual rows below to narrow the ranking to just those listings.")
    selection_event = st.dataframe(
        listings_df,
        width="stretch",
        on_select="rerun",
        selection_mode="multi-row",
        key="analyzer_listings_table",
    )
    selected_rows = selection_event.selection.rows if selection_event.selection else []
    working_df = listings_df.iloc[selected_rows] if selected_rows else listings_df

    st.subheader("Value-for-money recommendations")

    currency_groups = scoring.split_by_currency(working_df)
    if len(currency_groups) > 1:
        counts = ", ".join(f"{currency}: {len(group)}" for currency, group in currency_groups.items())
        st.warning(
            f"Multiple currencies present ({counts}). Rankings below are computed independently "
            "per currency and are **not** comparable across groups - prices in different "
            "currencies are never mixed into the same score."
        )

    currency_choice = st.selectbox("Currency group to rank", options=list(currency_groups.keys()))
    rating_weight = st.slider(
        "Rating weight (price weight is 1 minus this)", 0.0, 1.0, scoring.DEFAULT_RATING_WEIGHT, 0.05
    )

    scored, excluded = scoring.score_listings(currency_groups[currency_choice], rating_weight=rating_weight)

    if scored.empty:
        st.info("No listings in this currency group are eligible for ranking (all missing price or rating).")
    else:
        best_value_names = scored[scored["is_best_value"]]["name"].dropna().tolist()
        if best_value_names:
            badge_cols = st.columns(len(best_value_names))
            for col, name in zip(badge_cols, best_value_names, strict=False):
                col.badge(name, color="green", icon="🏆")

        outlier_count = int(scored["is_price_outlier"].sum())
        if outlier_count:
            st.badge(f"{outlier_count} unusually cheap - verify before trusting", color="yellow", icon="⚠️")

        display_cols = [c for c in DISPLAY_COLUMNS if c in scored.columns]
        styled = scored[display_cols].style.apply(_highlight_best_value, axis=1)
        st.dataframe(styled, width="stretch")

        col1, col2 = st.columns(2)
        file_stub = f"analysis_{'_'.join(map(str, selected_ids))}"
        col1.download_button(
            "Download ranked CSV",
            data=_download_bytes(scored, "csv"),
            file_name=f"{file_stub}.csv",
            mime="text/csv",
        )
        col2.download_button(
            "Download ranked JSON",
            data=_download_bytes(scored, "json"),
            file_name=f"{file_stub}.json",
            mime="application/json",
        )

    if not excluded.empty:
        with st.expander(f"{len(excluded)} listing(s) excluded from ranking (missing price or rating)"):
            st.dataframe(excluded, width="stretch")
