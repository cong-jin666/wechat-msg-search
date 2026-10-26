"""分析服务：本地统计式摘要，按块吐出，供 SSE 流式返回。

先落地「流式」这条链路本身，LLM 版本在 `llm.py` 里留了接入点：
把 `local_summary_chunks` 换成模型 token 流即可，接口层不用改。
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from typing import Iterator

from app.core.config import Settings, get_settings
from app.db import repo


def _top_keywords(conn: sqlite3.Connection, sample: int = 20000, topk: int = 12) -> list[tuple[str, int]]:
    rows = conn.execute(
        f"SELECT keywords FROM {repo.MESSAGE_TABLE} "
        "WHERE keywords IS NOT NULL AND keywords <> '' LIMIT ?",
        (sample,),
    ).fetchall()
    counter: Counter[str] = Counter()
    for row in rows:
        for word in str(row["keywords"]).split(","):
            word = word.strip()
            if word:
                counter[word] += 1
    return counter.most_common(topk)


def _top_talkers(conn: sqlite3.Connection, topk: int = 5) -> list[tuple[str, int]]:
    rows = conn.execute(
        f"SELECT StrTalker AS talker, COUNT(*) AS n FROM {repo.MESSAGE_TABLE} "
        "GROUP BY StrTalker ORDER BY n DESC LIMIT ?",
        (topk,),
    ).fetchall()
    return [(row["talker"] or "(未知)", row["n"]) for row in rows]


def local_summary_chunks(
    conn: sqlite3.Connection, settings: Settings | None = None, sample: int = 20000
) -> Iterator[str]:
    """生成一段本地摘要文本，逐块 yield。"""
    settings = settings or get_settings()
    total = repo.count_messages(conn, settings)
    span = conn.execute(
        f"SELECT MIN(CreateTime) AS lo, MAX(CreateTime) AS hi FROM {repo.MESSAGE_TABLE}"
    ).fetchone()
    lo = conn.execute(
        "SELECT datetime(?, 'unixepoch', 'localtime') AS t", (span["lo"],)
    ).fetchone()["t"] if span and span["lo"] else "-"
    hi = conn.execute(
        "SELECT datetime(?, 'unixepoch', 'localtime') AS t", (span["hi"],)
    ).fetchone()["t"] if span and span["hi"] else "-"

    yield f"本次分析覆盖 {total} 条文本消息，时间范围 {lo} 至 {hi}。\n\n"

    talkers = _top_talkers(conn)
    if talkers:
        yield "【高频会话对象】\n"
        for name, count in talkers:
            yield f"- {name}：{count} 条\n"
        yield "\n"

    keywords = _top_keywords(conn, sample=sample)
    if keywords:
        yield "【关键词分布】\n"
        for word, count in keywords:
            yield f"- {word}（{count} 次）\n"
        yield "\n"
    else:
        yield "【关键词分布】\n- 尚未生成关键词，请先执行分词与关键词抽取。\n\n"

    yield "以上为基于本地统计的摘要。接入大模型后，可在此基础上生成话题归纳与时间线。"


def llm_summary_chunks(prompt: str) -> Iterator[str]:
    """预留：真实 LLM 流式生成。未配置密钥时给出明确提示而不是静默失败。"""
    yield "未配置大模型（WCM_LLM_API_KEY），当前返回本地统计摘要。"
