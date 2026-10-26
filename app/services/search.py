"""检索服务：FTS5 全文检索（默认）+ LIKE 回退，支持近义词多路召回。

对应方案里的 4.3 / 4.4：不再用 `LIKE '%词%'` 扫全表，也不再让近义词条件挂在整句上。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict
from typing import Iterable, Literal

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db import repo
from app.services.synonyms import expand

log = get_logger(__name__)

SearchMode = Literal["fts", "like"]


@dataclass(slots=True)
class SearchHit:
    rowid: int
    talker: str
    content: str
    created_at: str
    snippet: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _clean_term(term: str) -> str:
    """去掉 FTS5 里有语法含义的字符，避免用户输入变成查询语法。"""
    return term.replace('"', " ").replace("*", " ").strip()


def build_match_query(terms: Iterable[str]) -> str:
    """把词列表拼成 FTS5 查询串：每个词加双引号当短语，词间用 OR。

    注意：这里拼的是「查询表达式」而不是 SQL，所有用户输入都被引号包住，
    无法注入 MATCH 操作符；SQL 本身仍然是参数化的。
    """
    quoted = [f'"{t}"' for t in (_clean_term(x) for x in terms) if t]
    return " OR ".join(quoted)


def _select_columns(conn: sqlite3.Connection, settings: Settings) -> tuple[str, str, str]:
    columns = repo.table_columns(conn)
    content = repo.resolve_column(columns, settings.content_columns) or "StrContent"
    talker = repo.resolve_column(columns, ["StrTalker"]) or "StrTalker"
    time_col = repo.resolve_column(columns, ["CreateTime"]) or "CreateTime"
    created = f"datetime(m.{time_col}, 'unixepoch', 'localtime')"
    return content, talker, created


def search_fts(
    conn: sqlite3.Connection,
    terms: list[str],
    limit: int = 50,
    settings: Settings | None = None,
    ranked: bool = True,
) -> list[SearchHit]:
    """ranked=True 按 bm25 相关度排序；False 时不排序、靠 LIMIT 早停（命中多时快一个量级）。"""
    settings = settings or get_settings()
    match_query = build_match_query(terms)
    if not match_query:
        return []
    content, talker, created = _select_columns(conn, settings)
    order_by = "ORDER BY bm25(msg_fts)" if ranked else ""
    sql = (
        f"SELECT m.rowid AS rid, m.{talker} AS talker, m.{content} AS content, "
        f"{created} AS created_at, "
        f"snippet(msg_fts, 0, '«', '»', '…', 24) AS snippet "
        f"FROM msg_fts JOIN {repo.MESSAGE_TABLE} m ON m.rowid = msg_fts.rowid "
        f"WHERE msg_fts MATCH ? {order_by} LIMIT ?"
    )
    rows = conn.execute(sql, (match_query, max(1, limit))).fetchall()
    return [SearchHit(r["rid"], r["talker"] or "", r["content"] or "", r["created_at"] or "", r["snippet"] or "") for r in rows]


def search_like(
    conn: sqlite3.Connection,
    terms: list[str],
    limit: int = 50,
    settings: Settings | None = None,
) -> list[SearchHit]:
    """回退方案 / 压测对照组：参数化 LIKE，词间 OR。"""
    settings = settings or get_settings()
    terms = [t for t in (_clean_term(x) for x in terms) if t]
    if not terms:
        return []
    content, talker, created = _select_columns(conn, settings)
    clauses = " OR ".join(f"m.{content} LIKE ?" for _ in terms)
    params: list = [f"%{t}%" for t in terms]
    sql = (
        f"SELECT m.rowid AS rid, m.{talker} AS talker, m.{content} AS content, "
        f"{created} AS created_at FROM {repo.MESSAGE_TABLE} m "
        f"WHERE {clauses} LIMIT ?"
    )
    rows = conn.execute(sql, [*params, max(1, limit)]).fetchall()
    return [SearchHit(r["rid"], r["talker"] or "", r["content"] or "", r["created_at"] or "", "") for r in rows]


def search(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 50,
    *,
    expand_synonyms: bool = True,
    mode: SearchMode | None = None,
    settings: Settings | None = None,
    ranked: bool = True,
) -> dict:
    """统一检索入口。

    mode=None 时优先 FTS，索引为空自动回退 LIKE（保证没跑过索引也能用）。
    """
    settings = settings or get_settings()
    query = (query or "").strip()
    if not query:
        return {"query": query, "terms": [], "mode": "none", "hits": []}

    terms = expand(query) if expand_synonyms else [query]
    chosen = mode
    if chosen is None:
        chosen = "fts" if repo.count_indexed(conn) > 0 else "like"

    hits = (
        search_fts(conn, terms, limit, settings, ranked=ranked)
        if chosen == "fts"
        else search_like(conn, terms, limit, settings)
    )
    return {
        "query": query,
        "terms": terms,
        "mode": chosen,
        "hits": [h.to_dict() for h in hits],
    }
