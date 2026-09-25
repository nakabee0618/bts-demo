from datetime import date, timedelta
from ranking import is_new


def test_is_new():
    assert is_new(date.today().isoformat())
    assert is_new((date.today() - timedelta(days=14)).isoformat())
    assert not is_new((date.today() - timedelta(days=15)).isoformat())
    assert not is_new(None)
