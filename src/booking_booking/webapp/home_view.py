import datetime
import logging

import streamlit as st

from booking_booking import storage
from booking_booking.errors import (
    BookingBookingError,
    ChallengeBlockedError,
    ElementNotFoundError,
    NoResultsError,
)
from booking_booking.models import SearchRequest
from booking_booking.orchestration import SearchProgress, run_search
from booking_booking.parsing.report import listings_to_dataframe

logger = logging.getLogger(__name__)

STAGE_LABELS = {
    "connecting": "Connecting to Booking.com",
    "waf_wait": "Waiting for anti-bot challenge to clear",
    "selecting_destination": "Selecting destination",
    "selecting_dates": "Selecting dates",
    "waiting_for_results": "Waiting for search results",
    "counting_properties": "Counting properties found",
    "collecting": "Collecting properties",
    "parsing": "Parsing collected properties",
    "done": "Done",
}


def _run_search_with_progress(request: SearchRequest, max_results: int | None):
    with st.status("Starting search...", expanded=True) as status:
        progress_bar = st.progress(0.0)

        def on_progress(evt: SearchProgress) -> None:
            label = STAGE_LABELS.get(evt.stage, evt.stage)
            if evt.stage == "collecting" and evt.total:
                progress_bar.progress(min(1.0, (evt.current or 0) / evt.total))
                status.update(label=f"{label} ({evt.current}/{evt.total})")
            else:
                status.update(label=label)

        try:
            outcome = run_search(request, max_results=max_results, on_progress=on_progress)
        except ChallengeBlockedError as exc:
            status.update(label="Blocked by anti-bot challenge", state="error")
            st.error(
                f"{exc}\n\nThis is expected under repeated automated use - space out your runs "
                "rather than retrying immediately."
            )
            return None
        except NoResultsError as exc:
            status.update(label="No results", state="error")
            st.error(f"No results: {exc}")
            return None
        except ElementNotFoundError as exc:
            status.update(label="Page structure changed", state="error")
            st.error(
                f"{exc}\n\nBooking.com's page structure may have changed - check "
                "src/booking_booking/config.py's selectors."
            )
            return None
        except BookingBookingError as exc:
            status.update(label="Search failed", state="error")
            st.error(str(exc))
            return None
        except Exception:
            status.update(label="Unexpected error", state="error")
            logger.exception("Unexpected error during search")
            st.error("An unexpected error occurred. Check the terminal logs for details.")
            return None

        progress_bar.progress(1.0)
        status.update(label="Done", state="complete")
        return outcome


def _download_bytes(df, fmt: str) -> bytes:
    if fmt == "json":
        return df.to_json(orient="records", indent=2, date_format="iso").encode("utf-8")
    return df.to_csv(index=False).encode("utf-8")


def render() -> None:
    st.title("🏨 Booking Booking")
    st.caption(
        "Search Booking.com for hotels. Booking.com actively blocks automated traffic (AWS WAF) - "
        "repeated runs in a short window may start failing; that's expected, not a bug. See the README."
    )

    with st.form("search_form"):
        col1, col2 = st.columns(2)
        city = col1.text_input("City", placeholder='e.g. "Temuco, Chile"')
        option = col2.number_input("Destination suggestion #", min_value=1, value=1, step=1)

        col3, col4 = st.columns(2)
        default_arrival = datetime.date.today() + datetime.timedelta(days=30)
        arrival_date = col3.date_input("Arrival date", value=default_arrival)
        departure_date = col4.date_input("Departure date", value=default_arrival + datetime.timedelta(days=2))

        max_results = st.number_input("Max results (0 = no limit)", min_value=0, value=25, step=5)

        submitted = st.form_submit_button("Run search")

    if submitted:
        if not city.strip():
            st.error("Please enter a city.")
            st.stop()
        if departure_date <= arrival_date:
            st.error("Departure date must be after arrival date.")
            st.stop()

        request = SearchRequest(
            city=city.strip(),
            arrival_date=arrival_date,
            departure_date=departure_date,
            place_option=int(option),
        )
        effective_max_results = int(max_results) or None

        outcome = _run_search_with_progress(request, effective_max_results)

        if outcome is not None:
            df = listings_to_dataframe(outcome.listings)

            currency = None
            if not df.empty and df["currency"].nunique(dropna=True) == 1:
                currency = df["currency"].dropna().iloc[0]

            conn = storage.get_connection()
            storage.init_db(conn)
            search_id = storage.insert_search(
                conn,
                request,
                total_properties_found=outcome.total_properties_found,
                listings_collected=len(outcome.listings),
                currency=currency,
                max_results=effective_max_results,
            )
            storage.insert_listings(conn, search_id, outcome.listings)

            st.session_state["last_search_id"] = search_id
            st.session_state["last_search_df"] = df
            st.session_state["last_search_place"] = outcome.place_selected
            st.session_state["last_search_total"] = outcome.total_properties_found

    # Rendered unconditionally (not inside `if submitted:`) so results and
    # download buttons survive a rerun triggered by clicking download itself.
    if "last_search_id" in st.session_state:
        st.success(
            f"Search #{st.session_state['last_search_id']} saved to output/booking_booking.db - "
            f"{st.session_state['last_search_place']}, "
            f"{st.session_state['last_search_total']} properties found, "
            f"{len(st.session_state['last_search_df'])} collected."
        )
        result_df = st.session_state["last_search_df"]
        st.dataframe(result_df, width="stretch")

        col1, col2 = st.columns(2)
        col1.download_button(
            "Download CSV",
            data=_download_bytes(result_df, "csv"),
            file_name=f"research_{st.session_state['last_search_id']}.csv",
            mime="text/csv",
        )
        col2.download_button(
            "Download JSON",
            data=_download_bytes(result_df, "json"),
            file_name=f"research_{st.session_state['last_search_id']}.json",
            mime="application/json",
        )
