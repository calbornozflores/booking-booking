import datetime
from pathlib import Path

import pytest

from booking_booking.errors import ElementNotFoundError
from booking_booking.parsing.property_card import parse_property_card_html, parse_property_cards_html

FIXTURES = Path(__file__).parent.parent / "fixtures" / "html"


@pytest.fixture
def single_card_html() -> str:
    return (FIXTURES / "property_card_sample.html").read_text(encoding="utf-8")


@pytest.fixture
def multi_card_html() -> str:
    return (FIXTURES / "property_cards_sample.html").read_text(encoding="utf-8")


def test_parses_real_property_card(single_card_html):
    listing = parse_property_card_html(single_card_html)

    assert listing.name == "Dpto Vip, moderno, centrico, con estacionamiento"
    assert listing.area == "Temuco"
    assert listing.distance_from_centre == "0.5 km from centre"
    assert listing.rating_value == 9.8
    assert listing.rating_description == "Exceptional"
    assert listing.review_count == 66
    assert listing.location_score == 9.7
    assert listing.price == 93.0
    assert listing.currency == "€"
    assert listing.taxes_note == "Includes taxes and charges"
    assert listing.price_note == "2 nights, 2 adults"


def test_attaches_search_dates(single_card_html):
    arrival = datetime.date(2026, 10, 1)
    departure = datetime.date(2026, 10, 3)

    listing = parse_property_card_html(single_card_html, arrival_date=arrival, departure_date=departure)

    assert listing.arrival_date == arrival
    assert listing.departure_date == departure


def test_raises_on_missing_name():
    with pytest.raises(ElementNotFoundError):
        parse_property_card_html('<div data-testid="property-card"></div>')


def test_parses_multiple_cards(multi_card_html):
    listings = parse_property_cards_html(multi_card_html)

    assert len(listings) == 5
    assert all(listing.name for listing in listings)
