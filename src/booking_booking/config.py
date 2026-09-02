"""Single source of truth for Booking.com selectors and constants.

Selectors were confirmed against the live site in September 2026 (see the
plan/README for verification notes). Booking.com's DOM changes over time -
if scraping starts failing, this is the first file to check.
"""

BASE_URL = "https://www.booking.com"

DEFAULT_TIMEOUT_MS = 10_000
WAF_CLEAR_TIMEOUT_S = 30
NAVIGATION_TIMEOUT_MS = 30_000

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

SELECTORS = {
    "waf_marker": "awsWafCookieDomainList",
    # Structural selector, not text-based: Booking.com serves different
    # locales (e.g. Italian) depending on network/IP, and an English
    # aria-label substring match silently fails to find the button then.
    "dismiss_overlay": "[data-bui-trap-root] button",
    "destination_input": 'input[name="ss"]',
    "autocomplete_option": 'li[role="option"]',
    "date_display_trigger": '[data-testid="date-display-field-start"]',
    "date_cell": 'span[data-date="{date}"]',
    "any_date_cell": "span[data-date]",
    "next_month_button": 'button[aria-label="Next month"]',
    "search_button": 'button[type="submit"]',
    "results_header": "h1",
    "property_card": '[data-testid="property-card"]',
}

# Nested selectors, scoped within a single property-card element.
CARD_FIELD_SELECTORS = {
    "name": '[data-testid="title"]',
    "area": '[data-testid="address-link"]',
    "distance_from_centre": '[data-testid="distance"]',
    "review_score": '[data-testid="review-score"]',
    "secondary_review_link": '[data-testid="secondary-review-score-link"]',
    "price": '[data-testid="price-and-discounted-price"]',
    "taxes_note": '[data-testid="taxes-and-charges"]',
    "price_note": '[data-testid="price-for-x-nights"]',
}
