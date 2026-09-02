import logging
import time
from collections.abc import Callable
from contextlib import contextmanager

from playwright.sync_api import Page, sync_playwright

from booking_booking import config
from booking_booking.errors import ChallengeBlockedError

logger = logging.getLogger(__name__)


@contextmanager
def browser_session(headless: bool = True):
    """Context-managed Playwright session; guarantees browser/context teardown
    even if the caller raises."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            context = browser.new_context(
                user_agent=config.USER_AGENT,
                viewport={"width": 1366, "height": 900},
            )
            try:
                page = context.new_page()
                yield page
            finally:
                context.close()
        finally:
            browser.close()


def wait_for_waf_clear(
    page: Page,
    timeout_s: int = config.WAF_CLEAR_TIMEOUT_S,
    on_tick: Callable[[int, int], None] | None = None,
) -> None:
    """Wait for Booking.com's AWS WAF JS challenge to clear.

    Raises ChallengeBlockedError if it hasn't cleared within timeout_s.

    on_tick(elapsed_s, timeout_s), if given, is called once per second while
    waiting - useful for surfacing elapsed-time progress, since the challenge
    can clear at any point before the deadline and has no meaningful percentage.
    """
    start = time.monotonic()
    deadline = start + timeout_s
    while time.monotonic() < deadline:
        try:
            if config.SELECTORS["waf_marker"] not in page.content():
                return
        except Exception as exc:
            logger.debug("Transient error reading page content while waiting on WAF: %s", exc)
        if on_tick is not None:
            on_tick(int(time.monotonic() - start), timeout_s)
        time.sleep(1)

    if config.SELECTORS["waf_marker"] in page.content():
        raise ChallengeBlockedError(
            f"Booking.com's anti-bot challenge did not clear within {timeout_s}s. "
            "This site actively blocks automated traffic; scraping it may not work reliably."
        )
