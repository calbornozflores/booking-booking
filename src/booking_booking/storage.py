import datetime
import sqlite3
from pathlib import Path

import pandas as pd

from booking_booking.models import HotelListing, SearchRequest
from booking_booking.parsing.report import listings_to_dataframe

DB_PATH = Path("output") / "booking_booking.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    arrival_date TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    place_option INTEGER NOT NULL,
    executed_at TEXT NOT NULL,
    total_properties_found INTEGER,
    listings_collected INTEGER,
    currency TEXT,
    max_results INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_id INTEGER NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
    name TEXT,
    area TEXT,
    distance_from_centre TEXT,
    rating_value REAL,
    rating_description TEXT,
    review_count INTEGER,
    location_score REAL,
    price REAL,
    currency TEXT,
    price_note TEXT,
    taxes_note TEXT,
    arrival_date TEXT,
    departure_date TEXT,
    scraped_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_listings_search_id ON listings(search_id);
CREATE INDEX IF NOT EXISTS idx_searches_city ON searches(city);
"""


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()


def insert_search(
    conn: sqlite3.Connection,
    request: SearchRequest,
    total_properties_found: int,
    listings_collected: int,
    currency: str | None,
    max_results: int | None,
    notes: str | None = None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO searches
            (city, arrival_date, departure_date, place_option, executed_at,
             total_properties_found, listings_collected, currency, max_results, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request.city,
            request.arrival_date.isoformat(),
            request.departure_date.isoformat(),
            request.place_option,
            datetime.datetime.now(datetime.timezone.utc).isoformat(),
            total_properties_found,
            listings_collected,
            currency,
            max_results,
            notes,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def insert_listings(conn: sqlite3.Connection, search_id: int, listings: list[HotelListing]) -> None:
    if not listings:
        return
    df = listings_to_dataframe(listings)
    df["search_id"] = search_id
    df["scraped_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    df.to_sql("listings", conn, if_exists="append", index=False)
    conn.commit()


def list_searches(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM searches ORDER BY executed_at DESC", conn)


def get_listings_for_searches(conn: sqlite3.Connection, search_ids: list[int]) -> pd.DataFrame:
    if not search_ids:
        return pd.DataFrame()
    placeholders = ",".join("?" for _ in search_ids)
    query = f"""
        SELECT l.*, s.city, s.arrival_date AS search_arrival_date, s.departure_date AS search_departure_date
        FROM listings l
        JOIN searches s ON l.search_id = s.id
        WHERE l.search_id IN ({placeholders})
    """
    return pd.read_sql(query, conn, params=search_ids)
