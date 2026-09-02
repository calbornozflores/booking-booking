import datetime

import pytest

from booking_booking.cli import build_arg_parser


def test_parses_full_cli_args():
    parser = build_arg_parser()
    args = parser.parse_args(["-c", "Temuco, Chile", "-a", "2026-10-01", "-d", "2026-10-03", "-o", "2"])

    assert args.city == "Temuco, Chile"
    assert args.arrival_date == datetime.date(2026, 10, 1)
    assert args.departure_date == datetime.date(2026, 10, 3)
    assert args.option == 2
    assert args.format == "csv"
    assert args.append is False


def test_defaults_when_only_city_given():
    parser = build_arg_parser()
    args = parser.parse_args(["-c", "Temuco, Chile"])

    assert args.arrival_date is None
    assert args.departure_date is None
    assert args.option == 1


def test_rejects_malformed_date():
    parser = build_arg_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["-c", "Temuco, Chile", "-a", "01-10-2026", "-d", "2026-10-03"])


def test_json_format_option():
    parser = build_arg_parser()
    args = parser.parse_args(["-c", "Temuco, Chile", "--format", "json"])
    assert args.format == "json"
