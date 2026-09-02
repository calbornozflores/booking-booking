import logging
import re
from collections.abc import Callable

from playwright.sync_api import Page

from booking_booking import config
from booking_booking.errors import NoResultsError

logger = logging.getLogger(__name__)

_PROPERTY_COUNT_RE = re.compile(r"([\d,]+)\s*propert(?:y|ies)\s*found", re.IGNORECASE)

SCROLL_STEP_PX = 4_000
SCROLL_SETTLE_MS = 1_200
STABLE_ROUNDS_TO_STOP = 3


def get_property_count(page: Page) -> int:
    header = page.locator(config.SELECTORS["results_header"])
    if header.count() == 0:
        raise NoResultsError("No results header found on the page.")
    text = header.first.inner_text()
    match = _PROPERTY_COUNT_RE.search(text)
    if not match:
        raise NoResultsError(f"Could not parse a property count from header text: {text!r}")
    return int(match.group(1).replace(",", ""))


def collect_property_cards_html(
    page: Page,
    max_results: int | None = None,
    target_total: int | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[str]:
    """Booking.com's results page is infinite-scroll (not paginated with a
    'Next page' button as of this rewrite) - scroll down repeatedly, growing
    the loaded card count, until it stabilizes or max_results is reached.

    on_progress(current, total), if given, is called after each scroll round
    (loading phase) and after each card's HTML is extracted (extraction
    phase), sharing target_total so a caller's progress bar advances
    monotonically through both phases instead of resetting between them.
    """
    card_locator = page.locator(config.SELECTORS["property_card"])
    stable_rounds = 0
    previous_count = card_locator.count()
    total = target_total if target_total is not None else max_results

    while stable_rounds < STABLE_ROUNDS_TO_STOP:
        if max_results is not None and previous_count >= max_results:
            break
        page.mouse.wheel(0, SCROLL_STEP_PX)
        page.wait_for_timeout(SCROLL_SETTLE_MS)
        current_count = card_locator.count()
        if current_count > previous_count:
            stable_rounds = 0
        else:
            stable_rounds += 1
        previous_count = current_count
        if on_progress is not None:
            on_progress(min(current_count, total) if total else current_count, total)

    count = card_locator.count()
    if max_results is not None:
        count = min(count, max_results)
    logger.info("Collected %d property cards.", count)

    cards_html = []
    for i in range(count):
        cards_html.append(card_locator.nth(i).evaluate("e => e.outerHTML"))
        if on_progress is not None:
            on_progress(i + 1, total if total else count)

    return cards_html
