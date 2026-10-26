"""近义词扩展。

原实现依赖 synonyms 包（2017 年后基本停更，Python 3.11+ 装不上），
改为读一份纯文本近义词表：`主词 近义词1 近义词2 ...`，一行一组。
文件不存在或词不在表里时退化为只搜原词，不抛异常。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


@lru_cache
def _load_table(path_str: str) -> dict[str, tuple[str, ...]]:
    path = Path(path_str)
    if not path.exists():
        log.warning("近义词表不存在：%s，近义扩展将退化为仅原词", path)
        return {}
    table: dict[str, tuple[str, ...]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p for p in line.replace(",", " ").split() if p]
        if len(parts) < 2:
            continue
        head, rest = parts[0], tuple(dict.fromkeys(parts[1:]))
        table[head] = rest
        # 反向登记，保证表里任意一个词都能扩展
        for word in rest:
            merged = tuple(dict.fromkeys((head, *[w for w in rest if w != word])))
            table.setdefault(word, merged)
    return table


def load_synonyms(path: Path | None = None) -> dict[str, tuple[str, ...]]:
    target = path or get_settings().synonym_file
    return _load_table(str(target))


def expand(word: str, path: Path | None = None) -> list[str]:
    """返回 [原词, 近义词...]，去重且保序。"""
    word = (word or "").strip()
    if not word:
        return []
    table = load_synonyms(path)
    return [word, *table.get(word, ())]
