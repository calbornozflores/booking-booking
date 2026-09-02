"""Live smoke test against the real Booking.com site.

NOT run in CI (see .github/workflows/ci.yml) - Booking.com fronts all
traffic with an AWS WAF bot challenge, and repeated automated requests from
the same IP (such as a CI runner's) escalate that challenge until it no
longer clears. Run this manually, sparingly, when validating that the
selectors in config.py still match the live site.

    pytest tests/integration -v -m live
"""

import datetime

import pytest

from booking_booking.cli import run

pytestmark = pytest.mark.live


def test_full_search_flow_against_live_site(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    arrival = datetime.date.today() + datetime.timedelta(days=30)
    departure = arrival + datetime.timedelta(days=2)

    run(
        city="Temuco, Chile",
        arrival_date=arrival,
        departure_date=departure,
        option=1,
        max_results=10,
    )

    output_files = list((tmp_path / "output").glob("research_*.csv"))
    assert output_files, "expected a research_<timestamp>.csv file to be written"
