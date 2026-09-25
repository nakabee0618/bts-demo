from datetime import date
from prices.rakuten import dummy_price, fetch_price, is_rakuten_ref


def test_dummy_is_deterministic():
    a = dummy_price("H-TENSEI", date(2026, 11, 20), 1, 2)
    b = dummy_price("H-TENSEI", date(2026, 11, 20), 1, 2)
    assert a.price == b.price and a.source == "dummy"


def test_dummy_saturday_is_higher():
    fri = dummy_price("H-TENSEI", date(2026, 11, 20), 1, 2).price
    sat = dummy_price("H-TENSEI", date(2026, 11, 21), 1, 2).price
    assert sat > fri


def test_fetch_falls_back_to_dummy_without_app_id():
    f = fetch_price("12345", date(2026, 11, 20), 1, 2, application_id="")
    assert f.source == "dummy"


def test_is_rakuten_ref():
    assert is_rakuten_ref("12345") and not is_rakuten_ref("H-TENSEI") and not is_rakuten_ref(None)
