import datetime
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from booking_booking.models import HotelListing, SearchRequest
from booking_booking.orchestration import run_search

_ARRIVAL = datetime.date(2026, 10, 1)
_DEPARTURE = datetime.date(2026, 10, 3)


def _fake_page():
    page = MagicMock()
    page.content.return_value = "<html>no waf marker here</html>"
    return page


def _run_with_mocks(monkeypatch, cards_html=None, listings=None):
    page = _fake_page()

    @contextmanager
    def fake_browser_session(headless=True):
        yield page

    monkeypatch.setattr("booking_booking.orchestration.browser_session", fake_browser_session)
    monkeypatch.setattr("booking_booking.orchestration.dismiss_overlay", lambda p: None)
    monkeypatch.setattr("booking_booking.orchestration.set_place", lambda p, city, option: "Temuco / Chile")
    monkeypatch.setattr("booking_booking.orchestration.set_date_range", lambda p, a, d: None)
    monkeypatch.setattr("booking_booking.orchestration.submit_search", lambda p: None)
    monkeypatch.setattr("booking_booking.orchestration.get_property_count", lambda p: 2)
    monkeypatch.setattr(
        "booking_booking.orchestration.collect_property_cards_html",
        lambda p, max_results=None, target_total=None, on_progress=None: cards_html or [],
    )
    monkeypatch.setattr(
        "booking_booking.orchestration.parse_property_cards_html",
        lambda html, arrival_date=None, departure_date=None: listings or [],
    )

    request = SearchRequest(city="Temuco, Chile", arrival_date=_ARRIVAL, departure_date=_DEPARTURE)
    events = []
    outcome = run_search(request, on_progress=events.append)
    return outcome, events


def test_on_progress_receives_ordered_stages_ending_in_done(monkeypatch):
    listings = [HotelListing(name="Hotel A")]
    outcome, events = _run_with_mocks(monkeypatch, cards_html=["<div></div>"], listings=listings)

    stages = [evt.stage for evt in events]
    expected_order = [
        "connecting",
        "waf_wait",
        "selecting_destination",
        "selecting_dates",
        "waiting_for_results",
        "counting_properties",
        "parsing",
        "done",
    ]
    for stage in expected_order:
        assert stage in stages
    assert stages[-1] == "done"
    assert stages.index("connecting") < stages.index("selecting_destination") < stages.index("done")


def test_run_search_returns_outcome_with_listings_and_place(monkeypatch):
    listings = [HotelListing(name="Hotel A"), HotelListing(name="Hotel B")]
    outcome, _ = _run_with_mocks(monkeypatch, cards_html=["<div></div>", "<div></div>"], listings=listings)

    assert outcome.listings == listings
    assert outcome.total_properties_found == 2
    assert outcome.place_selected == "Temuco / Chile"


def test_max_results_caps_limit_passed_to_collection(monkeypatch):
    page = _fake_page()
    captured = {}

    @contextmanager
    def fake_browser_session(headless=True):
        yield page

    def fake_collect(p, max_results=None, target_total=None, on_progress=None):
        captured["target_total"] = target_total
        return []

    with (
        patch("booking_booking.orchestration.browser_session", fake_browser_session),
        patch("booking_booking.orchestration.dismiss_overlay", lambda p: None),
        patch("booking_booking.orchestration.set_place", lambda p, city, option: "Place"),
        patch("booking_booking.orchestration.set_date_range", lambda p, a, d: None),
        patch("booking_booking.orchestration.submit_search", lambda p: None),
        patch("booking_booking.orchestration.get_property_count", lambda p: 100),
        patch("booking_booking.orchestration.collect_property_cards_html", fake_collect),
        patch("booking_booking.orchestration.parse_property_cards_html", lambda *a, **k: []),
    ):
        request = SearchRequest(city="Temuco, Chile", arrival_date=_ARRIVAL, departure_date=_DEPARTURE)
        run_search(request, max_results=5)

    assert captured["target_total"] == 5
