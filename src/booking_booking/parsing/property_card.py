import re
from datetime import date

from bs4 import BeautifulSoup, Tag

from booking_booking.config import CARD_FIELD_SELECTORS
from booking_booking.errors import ElementNotFoundError
from booking_booking.models import HotelListing

_REVIEW_COUNT_RE = re.compile(r"([\d,]+)\s*reviews?", re.IGNORECASE)
_LOCATION_SCORE_RE = re.compile(r"Scored\s+([\d.]+)", re.IGNORECASE)
_PRICE_RE = re.compile(r"([^\d]*)\s*([\d.,]+)\s*$")


def _text(tag: Tag | None) -> str | None:
    if tag is None:
        return None
    text = tag.get_text(strip=True, separator=" ")
    return text or None


def _parse_review_score(card: Tag) -> tuple[float | None, str | None, int | None]:
    review_div = card.select_one(CARD_FIELD_SELECTORS["review_score"])
    if review_div is None:
        return None, None, None

    value_div = review_div.select_one('div[aria-hidden="true"]')
    rating_value = None
    if value_div is not None:
        try:
            rating_value = float(_text(value_div).replace(",", "."))
        except (ValueError, AttributeError):
            rating_value = None

    detail_div = review_div.select_one('div[aria-hidden="false"]')
    rating_description = None
    review_count = None
    if detail_div is not None:
        children = [c for c in detail_div.find_all("div", recursive=False)]
        if len(children) >= 1:
            rating_description = _text(children[0])
        if len(children) >= 2:
            match = _REVIEW_COUNT_RE.search(_text(children[1]) or "")
            if match:
                review_count = int(match.group(1).replace(",", ""))

    return rating_value, rating_description, review_count


def _parse_location_score(card: Tag) -> float | None:
    link = card.select_one(CARD_FIELD_SELECTORS["secondary_review_link"])
    if link is None:
        return None
    label = link.get("aria-label", "")
    match = _LOCATION_SCORE_RE.search(label)
    return float(match.group(1)) if match else None


def _parse_price(card: Tag) -> tuple[float | None, str | None]:
    price_tag = card.select_one(CARD_FIELD_SELECTORS["price"])
    text = _text(price_tag)
    if not text:
        return None, None
    match = _PRICE_RE.match(text)
    if not match:
        return None, text.strip() or None
    currency, amount = match.groups()
    try:
        return float(amount.replace(",", "")), currency.strip() or None
    except ValueError:
        return None, currency.strip() or None


def parse_property_card_html(
    html: str,
    arrival_date: date | None = None,
    departure_date: date | None = None,
) -> HotelListing:
    """Parse a single property-card element's outerHTML into a HotelListing.

    Raises ElementNotFoundError if the card has no recognizable name - that
    signals Booking.com's markup has changed rather than a merely-missing
    optional field.
    """
    soup = BeautifulSoup(html, "lxml")
    card = soup.select_one('[data-testid="property-card"]') or soup

    name = _text(card.select_one(CARD_FIELD_SELECTORS["name"]))
    if not name:
        raise ElementNotFoundError(
            f"Could not find property name using selector {CARD_FIELD_SELECTORS['name']!r} - "
            "Booking.com's card markup may have changed."
        )

    rating_value, rating_description, review_count = _parse_review_score(card)

    price, currency = _parse_price(card)

    return HotelListing(
        name=name,
        area=_text(card.select_one(CARD_FIELD_SELECTORS["area"])),
        distance_from_centre=_text(card.select_one(CARD_FIELD_SELECTORS["distance_from_centre"])),
        rating_value=rating_value,
        rating_description=rating_description,
        review_count=review_count,
        location_score=_parse_location_score(card),
        price=price,
        currency=currency,
        price_note=_text(card.select_one(CARD_FIELD_SELECTORS["price_note"])),
        taxes_note=_text(card.select_one(CARD_FIELD_SELECTORS["taxes_note"])),
        arrival_date=arrival_date,
        departure_date=departure_date,
    )


def parse_property_cards_html(
    html: str,
    arrival_date: date | None = None,
    departure_date: date | None = None,
) -> list[HotelListing]:
    """Parse a page/container fragment containing multiple property-card elements."""
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select('[data-testid="property-card"]')
    listings = []
    for card in cards:
        try:
            listings.append(parse_property_card_html(str(card), arrival_date, departure_date))
        except ElementNotFoundError:
            continue
    return listings
