from datetime import date
from nl_search import _parse_rule

AREAS = ["箱根", "熱海", "軽井沢", "京都", "沖縄"]


def test_rule_basic():
    p = _parse_rule("来週末に箱根で2人、3万円以内で温泉に泊まりたい", AREAS)
    assert p.area_name == "箱根" and p.category == "stay" and p.adults == 2 and p.budget == 30000 and p.checkin


def test_rule_meal_and_kanji_number():
    p = _parse_rule("京都で四人でランチ 5000円", AREAS)
    assert p.area_name == "京都" and p.category == "meal" and p.adults == 4 and p.budget == 5000


def test_rule_none():
    p = _parse_rule("どこかいいところ", AREAS)
    assert p.area_name is None and p.category is None and p.adults is None
