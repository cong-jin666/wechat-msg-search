import pytest

from app.db import repo
from app.services.ingest import run_pipeline
from app.services.search import build_match_query, search
from app.services.synonyms import expand


@pytest.fixture()
def indexed(ready_conn, settings, synonym_file):
    ready_conn.close()
    run_pipeline(settings.db_path, settings=settings)
    conn = repo.connect(settings.db_path)
    yield conn, settings
    conn.close()


def test_fts_returns_matching_rows(indexed):
    conn, settings = indexed
    result = search(conn, "天气", settings=settings)
    assert result["mode"] == "fts"
    assert len(result["hits"]) == 1
    assert "公园" in result["hits"][0]["content"]
    assert "«" in result["hits"][0]["snippet"]


def test_fts_mode_is_default_when_index_built(indexed):
    conn, settings = indexed
    assert repo.count_indexed(conn) == 5
    assert search(conn, "会议", settings=settings)["mode"] == "fts"


def test_synonym_expansion_finds_related_rows(indexed, synonym_file):
    conn, settings = indexed
    expanded = search(conn, "开会", settings=settings, expand_synonyms=True)
    plain = search(conn, "开会", settings=settings, expand_synonyms=False)
    assert "会议" in expanded["terms"]
    assert len(expanded["hits"]) >= 1
    assert plain["hits"] == []


def test_like_fallback(indexed):
    conn, settings = indexed
    result = search(conn, "餐厅", settings=settings, mode="like")
    assert result["mode"] == "like"
    assert len(result["hits"]) == 1


def test_sql_injection_attempt_is_harmless(indexed):
    conn, settings = indexed
    payload = "' OR 1=1 --"
    result = search(conn, payload, settings=settings)
    assert result["hits"] == []
    like_result = search(conn, payload, settings=settings, mode="like")
    assert like_result["hits"] == []


def test_match_query_quotes_terms():
    assert build_match_query(["会议", "开 会"]) == '"会议" OR "开 会"'
    assert build_match_query(['a"b*']) == '"a b"'
    assert build_match_query(["   "]) == ""


def test_empty_query_returns_nothing(indexed):
    conn, settings = indexed
    assert search(conn, "  ", settings=settings)["hits"] == []


def test_expand_unknown_word_returns_itself(synonym_file):
    assert expand("不存在的词") == ["不存在的词"]
    assert expand("会议")[0] == "会议"
    assert "开会" in expand("会议")
