from dataclasses import dataclass
from datetime import date


@dataclass
class SearchRequest:
    city: str
    arrival_date: date
    departure_date: date
    place_option: int = 1


@dataclass
class HotelListing:
    name: str | None = None
    area: str | None = None
    distance_from_centre: str | None = None
    rating_value: float | None = None
    rating_description: str | None = None
    review_count: int | None = None
    location_score: float | None = None
    price: float | None = None
    currency: str | None = None
    price_note: str | None = None
    taxes_note: str | None = None
    arrival_date: date | None = None
    departure_date: date | None = None
