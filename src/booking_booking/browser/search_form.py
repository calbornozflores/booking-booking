import logging
import re
from datetime import date

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from booking_booking import config
from booking_booking.errors import ElementNotFoundError

logger = logging.getLogger(__name__)

MAX_MONTH_ADVANCES = 12


def dismiss_overlay(page: Page) -> None:
    """Dismiss a sign-in/promo modal if one is showing. Not an error if absent."""
    overlay_button = page.locator(config.SELECTORS["dismiss_overlay"])
    try:
        if overlay_button.count() > 0:
            overlay_button.first.click(timeout=config.DEFAULT_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        logger.debug("Overlay dismiss button present but not clickable in time; continuing.")


def set_place(page: Page, city: str, option: int = 1) -> str:
    """Type the destination and select a suggestion. Returns the selected
    suggestion's display text.

    Raises ElementNotFoundError if the destination input or the requested
    suggestion index isn't available.
    """
    destination_input = page.locator(config.SELECTORS["destination_input"])
    try:
        destination_input.wait_for(state="visible", timeout=config.DEFAULT_TIMEOUT_MS)
    except PlaywrightTimeoutError as exc:
        raise ElementNotFoundError(
            f"Destination input ({config.SELECTORS['destination_input']!r}) not found."
        ) from exc

    # .fill() sets the value in one shot and doesn't reliably trigger Booking.com's
    # keystroke-driven autocomplete, leaving stale default suggestions showing.
    # Typing key-by-key and then waiting for a suggestion that matches what we
    # typed (not just "any" suggestion) avoids picking one of those stale defaults.
    destination_input.click()
    destination_input.fill("")
    destination_input.press_sequentially(city, delay=30)

    search_term = city.split(",")[0].strip()
    options = page.locator(config.SELECTORS["autocomplete_option"]).filter(
        has_text=re.compile(re.escape(search_term), re.IGNORECASE)
    )
    try:
        options.first.wait_for(state="visible", timeout=config.DEFAULT_TIMEOUT_MS)
    except PlaywrightTimeoutError as exc:
        raise ElementNotFoundError(f"No destination suggestions appeared for {city!r}.") from exc

    count = options.count()
    index = option - 1
    if not (0 <= index < count):
        logger.warning("Requested place option %d out of range (1-%d); defaulting to 1.", option, count)
        index = 0

    chosen = options.nth(index)
    chosen_text = chosen.inner_text()
    chosen.click()
    return chosen_text


def _open_date_picker(page: Page) -> None:
    trigger = page.locator(config.SELECTORS["date_display_trigger"])
    trigger.wait_for(state="visible", timeout=config.DEFAULT_TIMEOUT_MS)
    trigger.click()
    try:
        page.locator(config.SELECTORS["any_date_cell"]).first.wait_for(state="visible", timeout=3_000)
        return
    except PlaywrightTimeoutError:
        # Booking.com's picker occasionally needs a second click to open.
        trigger.click()
        page.locator(config.SELECTORS["any_date_cell"]).first.wait_for(
            state="visible", timeout=config.DEFAULT_TIMEOUT_MS
        )


def _click_date_cell(page: Page, target: date) -> None:
    date_str = target.isoformat()
    cell = page.locator(config.SELECTORS["date_cell"].format(date=date_str))

    for _ in range(MAX_MONTH_ADVANCES):
        if cell.count() > 0:
            cell.first.click()
            return
        next_month = page.locator(config.SELECTORS["next_month_button"])
        if next_month.count() == 0:
            break
        next_month.first.click()
        page.locator(config.SELECTORS["any_date_cell"]).first.wait_for(
            state="visible", timeout=config.DEFAULT_TIMEOUT_MS
        )

    raise ElementNotFoundError(f"Could not find a selectable date cell for {date_str}.")


def set_date_range(page: Page, arrival_date: date, departure_date: date) -> None:
    _open_date_picker(page)
    _click_date_cell(page, arrival_date)
    _click_date_cell(page, departure_date)


def submit_search(page: Page) -> None:
    button = page.locator(config.SELECTORS["search_button"])
    try:
        button.first.click(timeout=config.DEFAULT_TIMEOUT_MS)
    except PlaywrightTimeoutError as exc:
        raise ElementNotFoundError(
            f"Search button ({config.SELECTORS['search_button']!r}) not found or not clickable."
        ) from exc
