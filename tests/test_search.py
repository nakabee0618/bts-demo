from datetime import date, timedelta
from search import Condition, validate


def test_validate_ok():
    assert validate(Condition(None, None, date.today() + timedelta(days=7), 2, 30000)) is None


def test_validate_adults():
    assert validate(Condition(None, None, None, 0, None)) is not None


def test_validate_past_date():
    assert validate(Condition(None, None, date.today() - timedelta(days=1), 2, None)) is not None


def test_validate_budget():
    assert validate(Condition(None, None, None, 2, -1)) is not None
