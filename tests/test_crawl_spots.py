from prices.crawl_spots import extract_spots

HTML = """<html><body>
<h2>箱根彫刻の森美術館</h2><p>屋外彫刻が並ぶ。<a href="/spot/chokoku">詳しく</a></p>
<h3>甘酒茶屋</h3><p>江戸時代から続く茶屋</p>
<h2></h2>
</body></html>"""


def test_extract_spots():
    spots = extract_spots(HTML, "https://example.com/hakone")
    assert len(spots) == 2
    assert spots[0]["name"] == "箱根彫刻の森美術館" and spots[0]["url"] == "https://example.com/spot/chokoku"
    assert spots[1]["url"] == "https://example.com/hakone"
