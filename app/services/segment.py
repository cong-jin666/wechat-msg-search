"""分词与关键词抽取：入参字符串，出参字符串 / 列表，不碰任何数据库和界面。

替代原 `提取词模型.py`、`总结关键词模型.py` 里的内联逻辑。
关键词抽取用 jieba.analyse（TF-IDF），替掉停更的 synonyms 包。
"""

from __future__ import annotations

import re

import jieba
import jieba.analyse

_WHITESPACE = re.compile(r"\s+")


def segment_text(text: str | None, *, fine_grained: bool = True) -> str:
    """把一句话切成空格分隔的词串。空白 token 会被丢弃。

    默认用 `lcut_for_search`（搜索引擎模式）：它会把长词再切出子词，
    例如「今天天气」→「今天 天天 天气 今天天气」。建索引用这种粒度召回更高，
    代价是索引稍大——这是 FTS 场景的标准取舍。

    >>> segment_text("今天天气不错")
    '今天 天天 天气 今天天气 不错'
    """
    if not text:
        return ""
    cut = jieba.lcut_for_search if fine_grained else jieba.lcut
    tokens = [tok.strip() for tok in cut(text)]
    return " ".join(tok for tok in tokens if tok and not _WHITESPACE.fullmatch(tok))


def extract_keywords(text: str | None, topk: int = 5) -> list[str]:
    """抽取关键词。短句 / 全是停用词时可能返回空列表，调用方自己决定如何兜底。"""
    if not text or not text.strip():
        return []
    return [w for w in jieba.analyse.extract_tags(text, topK=topk) if w]


def keywords_to_text(keywords: list[str]) -> str:
    return ", ".join(keywords)
