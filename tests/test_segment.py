from app.services.segment import extract_keywords, keywords_to_text, segment_text


def test_segment_splits_and_filters_whitespace():
    result = segment_text("今天  天气\t不错\n")
    assert "  " not in result
    assert "\n" not in result
    assert result.split() == ["今天", "天气", "不错"]


def test_segment_empty_input():
    assert segment_text("") == ""
    assert segment_text(None) == ""
    assert segment_text("   ") == ""


def test_extract_keywords_returns_terms():
    words = extract_keywords("这周的会议改成周四下午了，会议室在三楼", topk=3)
    assert words
    assert all(isinstance(w, str) and w for w in words)


def test_extract_keywords_empty_text():
    assert extract_keywords("") == []


def test_keywords_to_text():
    assert keywords_to_text(["会议", "周四"]) == "会议, 周四"
