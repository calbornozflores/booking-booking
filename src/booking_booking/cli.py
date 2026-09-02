import argparse
import datetime
import logging
import sys

from tqdm import tqdm

from booking_booking.errors import BookingBookingError
from booking_booking.io.prompts import ask_for_dates, ask_for_place
from booking_booking.io.writers import resolve_output_path, write_listings
from booking_booking.models import SearchRequest
from booking_booking.orchestration import SearchProgress, run_search

logger = logging.getLogger(__name__)


def _parse_date(value: str) -> datetime.date:
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a valid date; expected YYYY-MM-DD") from exc


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="booking-booking",
        description="Search Booking.com for hotels in a city over a date range and export the results.",
    )
    parser.add_argument("-c", "--city", help='City to search, e.g. "Temuco, Chile"')
    parser.add_argument("-a", "--arrival-date", type=_parse_date, help="Arrival date, YYYY-MM-DD")
    parser.add_argument("-d", "--departure-date", type=_parse_date, help="Departure date, YYYY-MM-DD")
    parser.add_argument(
        "-o", "--option", type=int, default=1, help="Which destination suggestion to pick (1-indexed)"
    )
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format")
    parser.add_argument(
        "--append", action="store_true", help="Append to a persistent output file instead of a fresh one"
    )
    parser.add_argument(
        "--max-results", type=int, default=None, help="Stop after collecting this many properties"
    )
    parser.add_argument("--headed", action="store_true", help="Run the browser with a visible window")
    return parser


def run(
    city: str,
    arrival_date: datetime.date,
    departure_date: datetime.date,
    option: int,
    fmt: str = "csv",
    append: bool = False,
    max_results: int | None = None,
    headed: bool = False,
) -> None:
    if departure_date <= arrival_date:
        raise ValueError("departure_date must be after arrival_date")

    request = SearchRequest(
        city=city, arrival_date=arrival_date, departure_date=departure_date, place_option=option
    )

    bar = tqdm(desc="Scraping properties")
    last_logged_stage = None

    def on_progress(evt: SearchProgress) -> None:
        nonlocal last_logged_stage
        if evt.stage == "collecting" and evt.total:
            bar.total = evt.total
            bar.n = evt.current or 0
            bar.refresh()
            return
        # waf_wait/waiting_for_results tick once per second; log only the
        # first message per stage instead of spamming a line every second.
        if evt.stage != last_logged_stage and evt.stage != "done":
            logger.info(evt.message)
            last_logged_stage = evt.stage

    try:
        outcome = run_search(request, max_results=max_results, headed=headed, on_progress=on_progress)
    finally:
        bar.close()

    output_path = resolve_output_path(fmt, append)
    write_listings(outcome.listings, output_path, fmt, append)
    logger.info("Wrote results to %s", output_path)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    city = args.city or ask_for_place()
    if args.arrival_date and args.departure_date:
        arrival_date, departure_date = args.arrival_date, args.departure_date
    else:
        arrival_date, departure_date = ask_for_dates()

    try:
        run(
            city=city,
            arrival_date=arrival_date,
            departure_date=departure_date,
            option=args.option,
            fmt=args.format,
            append=args.append,
            max_results=args.max_results,
            headed=args.headed,
        )
    except BookingBookingError as exc:
        logger.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
