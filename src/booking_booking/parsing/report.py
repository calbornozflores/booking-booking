import pandas as pd

from booking_booking.models import HotelListing


def listings_to_dataframe(listings: list[HotelListing]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "name": listing.name,
                "area": listing.area,
                "distance_from_centre": listing.distance_from_centre,
                "rating_value": listing.rating_value,
                "rating_description": listing.rating_description,
                "review_count": listing.review_count,
                "location_score": listing.location_score,
                "price": listing.price,
                "currency": listing.currency,
                "price_note": listing.price_note,
                "taxes_note": listing.taxes_note,
                "arrival_date": listing.arrival_date,
                "departure_date": listing.departure_date,
            }
            for listing in listings
        ]
    )
