import datetime

from booking_booking.models import HotelListing
from booking_booking.parsing.report import listings_to_dataframe


def test_listings_to_dataframe_columns_and_values():
    listing = HotelListing(
        name="Test Hotel",
        area="Test City",
        rating_value=8.5,
        review_count=42,
        price=120.5,
        currency="€",
        arrival_date=datetime.date(2026, 10, 1),
        departure_date=datetime.date(2026, 10, 3),
    )

    df = listings_to_dataframe([listing])

    assert list(df.columns) == [
        "name",
        "area",
        "distance_from_centre",
        "rating_value",
        "rating_description",
        "review_count",
        "location_score",
        "price",
        "currency",
        "price_note",
        "taxes_note",
        "arrival_date",
        "departure_date",
    ]
    assert df.iloc[0]["name"] == "Test Hotel"
    assert df.iloc[0]["rating_value"] == 8.5
    assert df.iloc[0]["review_count"] == 42


def test_empty_listings_produces_empty_dataframe():
    df = listings_to_dataframe([])
    assert df.empty
