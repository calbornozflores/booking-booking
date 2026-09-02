import datetime
from pathlib import Path

import pandas as pd

from booking_booking.models import HotelListing
from booking_booking.parsing.report import listings_to_dataframe

OUTPUT_DIR = Path("output")


def resolve_output_path(fmt: str, append: bool) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if append:
        return OUTPUT_DIR / f"research.{fmt}"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return OUTPUT_DIR / f"research_{timestamp}.{fmt}"


def write_listings(listings: list[HotelListing], path: Path, fmt: str, append: bool) -> None:
    df = listings_to_dataframe(listings)
    if fmt == "csv":
        df.to_csv(path, mode="a" if append else "w", header=not (append and path.exists()), index=False)
    elif fmt == "json":
        if append and path.exists():
            existing = pd.read_json(path, orient="records")
            df = pd.concat([existing, df], ignore_index=True)
        df.to_json(path, orient="records", indent=2, date_format="iso")
    else:
        raise ValueError(f"Unsupported output format: {fmt!r}")
