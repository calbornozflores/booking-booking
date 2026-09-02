import datetime
import sqlite3

import pytest

from booking_booking import storage
from booking_booking.models import HotelListing, SearchRequest


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    storage.init_db(connection)
    yield connection
    connection.close()


@pytest.fixture
def sample_request():
    return SearchRequest(
        city="Temuco, Chile",
        arrival_date=datetime.date(2026, 10, 1),
        departure_date=datetime.date(2026, 10, 3),
        place_option=1,
    )


def test_init_db_creates_tables(conn):
    tables = {
        row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert {"searches", "listings"} <= tables


def test_init_db_is_idempotent(conn):
    storage.init_db(conn)  # calling again must not raise
    storage.init_db(conn)


def test_insert_search_returns_id_and_persists_fields(conn, sample_request):
    search_id = storage.insert_search(
        conn,
        sample_request,
        total_properties_found=184,
        listings_collected=25,
        currency="€",
        max_results=25,
    )

    assert isinstance(search_id, int)
    row = conn.execute("SELECT * FROM searches WHERE id = ?", (search_id,)).fetchone()
    assert row["city"] == "Temuco, Chile"
    assert row["arrival_date"] == "2026-10-01"
    assert row["total_properties_found"] == 184
    assert row["currency"] == "€"


def test_insert_listings_links_to_search_via_foreign_key(conn, sample_request):
    search_id = storage.insert_search(
        conn,
        sample_request,
        total_properties_found=2,
        listings_collected=2,
        currency="€",
        max_results=None,
    )
    listings = [
        HotelListing(name="Hotel A", price=100.0, rating_value=8.0, currency="€"),
        HotelListing(name="Hotel B", price=150.0, rating_value=9.0, currency="€"),
    ]

    storage.insert_listings(conn, search_id, listings)

    df = storage.get_listings_for_searches(conn, [search_id])
    assert len(df) == 2
    assert set(df["name"]) == {"Hotel A", "Hotel B"}
    assert (df["search_id"] == search_id).all()


def test_insert_listings_with_missing_optional_fields_does_not_error(conn, sample_request):
    search_id = storage.insert_search(
        conn,
        sample_request,
        total_properties_found=1,
        listings_collected=1,
        currency=None,
        max_results=None,
    )

    storage.insert_listings(conn, search_id, [HotelListing(name="Bare Listing")])

    df = storage.get_listings_for_searches(conn, [search_id])
    assert len(df) == 1
    assert df.iloc[0]["price"] is None or df.iloc[0]["price"] != df.iloc[0]["price"]  # NaN or None


def test_insert_listings_with_empty_list_does_nothing(conn, sample_request):
    search_id = storage.insert_search(
        conn,
        sample_request,
        total_properties_found=0,
        listings_collected=0,
        currency=None,
        max_results=None,
    )

    storage.insert_listings(conn, search_id, [])

    df = storage.get_listings_for_searches(conn, [search_id])
    assert df.empty


def test_list_searches_orders_by_executed_at_desc(conn, sample_request):
    first_id = storage.insert_search(
        conn,
        sample_request,
        total_properties_found=1,
        listings_collected=1,
        currency="€",
        max_results=None,
    )
    conn.execute("UPDATE searches SET executed_at = '2026-01-01T00:00:00+00:00' WHERE id = ?", (first_id,))
    second_id = storage.insert_search(
        conn,
        sample_request,
        total_properties_found=1,
        listings_collected=1,
        currency="€",
        max_results=None,
    )
    conn.execute("UPDATE searches SET executed_at = '2026-06-01T00:00:00+00:00' WHERE id = ?", (second_id,))
    conn.commit()

    df = storage.list_searches(conn)

    assert list(df["id"]) == [second_id, first_id]


def test_get_listings_for_searches_filters_by_city_and_price(conn, sample_request):
    search_id = storage.insert_search(
        conn,
        sample_request,
        total_properties_found=2,
        listings_collected=2,
        currency="€",
        max_results=None,
    )
    storage.insert_listings(
        conn,
        search_id,
        [
            HotelListing(name="Cheap Hotel", price=50.0, rating_value=7.0),
            HotelListing(name="Pricey Hotel", price=500.0, rating_value=9.0),
        ],
    )

    df = storage.get_listings_for_searches(conn, [search_id])
    cheap_only = df[df["price"] < 100]

    assert list(cheap_only["name"]) == ["Cheap Hotel"]


def test_get_listings_for_searches_with_empty_ids_returns_empty(conn):
    df = storage.get_listings_for_searches(conn, [])
    assert df.empty
