import logging
from collections.abc import Callable
from dataclasses import dataclass

from booking_booking import config
from booking_booking.browser.results_page import collect_property_cards_html, get_property_count
from booking_booking.browser.search_form import dismiss_overlay, set_date_range, set_place, submit_search
from booking_booking.browser.session import browser_session, wait_for_waf_clear
from booking_booking.models import HotelListing, SearchRequest
from booking_booking.parsing.property_card import parse_property_cards_html

logger = logging.getLogger(__name__)

# Stage names, in the order they occur:
# connecting | waf_wait | selecting_destination | selecting_dates |
# waiting_for_results | counting_properties | collecting | parsing | done


@dataclass
class SearchProgress:
    stage: str
    message: str
    current: int | None = None
    total: int | None = None


@dataclass
class SearchOutcome:
    listings: list[HotelListing]
    total_properties_found: int
    place_selected: str


ProgressCallback = Callable[[SearchProgress], None]


def _emit(
    on_progress: ProgressCallback | None,
    stage: str,
    message: str,
    current: int | None = None,
    total: int | None = None,
) -> None:
    if on_progress is not None:
        on_progress(SearchProgress(stage=stage, message=message, current=current, total=total))


def run_search(
    request: SearchRequest,
    max_results: int | None = None,
    headed: bool = False,
    on_progress: ProgressCallback | None = None,
) -> SearchOutcome:
    """Run a full Booking.com search and return the parsed listings.

    This is the shared engine behind both the CLI (cli.run) and the web UI -
    it does no file/DB writing itself, only scraping + parsing. on_progress,
    if given, is called repeatedly as the search moves through its stages;
    see SearchProgress.stage for the fixed set of stage names.
    """

    def _waf_tick(elapsed_s: int, timeout_s: int, stage: str) -> None:
        _emit(on_progress, stage, f"Waiting for anti-bot challenge to clear... ({elapsed_s}s elapsed)")

    def _collect_tick(current: int, total: int | None) -> None:
        _emit(on_progress, "collecting", f"Collecting properties ({current}/{total or '?'})", current, total)

    with browser_session(headless=not headed) as page:
        _emit(on_progress, "connecting", f"Navigating to {config.BASE_URL}")
        page.goto(config.BASE_URL, wait_until="domcontentloaded", timeout=config.NAVIGATION_TIMEOUT_MS)

        _emit(on_progress, "waf_wait", "Waiting for anti-bot challenge to clear...")
        wait_for_waf_clear(page, on_tick=lambda e, t: _waf_tick(e, t, "waf_wait"))
        page.wait_for_load_state("networkidle", timeout=config.NAVIGATION_TIMEOUT_MS)

        dismiss_overlay(page)

        _emit(on_progress, "selecting_destination", f"Selecting destination: {request.city}")
        chosen_place = set_place(page, request.city, request.place_option)
        logger.info("Selected destination: %s", chosen_place.replace("\n", " / "))

        _emit(on_progress, "selecting_dates", "Selecting date range")
        set_date_range(page, request.arrival_date, request.departure_date)
        submit_search(page)

        _emit(on_progress, "waiting_for_results", "Waiting for search results to load...")
        page.wait_for_load_state("domcontentloaded", timeout=config.NAVIGATION_TIMEOUT_MS)
        wait_for_waf_clear(page, on_tick=lambda e, t: _waf_tick(e, t, "waiting_for_results"))
        page.wait_for_load_state("networkidle", timeout=config.NAVIGATION_TIMEOUT_MS)

        _emit(on_progress, "counting_properties", "Counting properties found")
        total_properties_found = get_property_count(page)
        logger.info("%d properties found", total_properties_found)
        limit = min(total_properties_found, max_results) if max_results else total_properties_found

        cards_html = collect_property_cards_html(
            page, max_results=max_results, target_total=limit, on_progress=_collect_tick
        )

    _emit(on_progress, "parsing", "Parsing collected properties")
    listings = parse_property_cards_html(
        "\n".join(cards_html), arrival_date=request.arrival_date, departure_date=request.departure_date
    )
    logger.info("Parsed %d listings", len(listings))

    _emit(on_progress, "done", "Done", current=len(listings), total=len(listings))

    return SearchOutcome(
        listings=listings,
        total_properties_found=total_properties_found,
        place_selected=chosen_place,
    )
