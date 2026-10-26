"""入库流水线：分词 → 关键词 → FTS 索引。

三个特性对应方案 P0/P2 的要求：
1. 增量：按「列是否为 NULL」驱动，第二次运行只处理新消息；
2. 批量：rowid 定位 + executemany + 分批提交，避免 N² 全表更新；
3. 可观测：每批回调进度，Web 端据此轮询任务状态。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db import repo
from app.services.segment import extract_keywords, keywords_to_text, segment_text

log = get_logger(__name__)

ProgressFn = Callable[[int, int], None]


@dataclass
class PipelineResult:
    segmented: int = 0
    keywords: int = 0
    indexed: int = 0
    elapsed_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "segmented": self.segmented,
            "keywords": self.keywords,
            "indexed": self.indexed,
            "elapsed_ms": self.elapsed_ms,
        }


def _run_stage(
    conn: sqlite3.Connection,
    column: str,
    transform: Callable[[str], str],
    settings: Settings,
    progress: ProgressFn | None,
) -> int:
    """按批取待处理行、批量写回。返回处理条数。"""
    total = repo.count_pending(conn, column, settings)
    if total == 0:
        log.info("%s：无待处理数据", column)
        return 0

    done = 0
    while True:
        rows = repo.fetch_pending_batch(conn, column, settings.batch_size, settings)
        if not rows:
            break
        pairs: list[tuple[str, int]] = []
        for row in rows:
            try:
                value = transform(row["content"])
            except Exception as exc:  # 单条失败不阻塞整批
                log.warning("处理失败 rowid=%s: %s", row["rid"], exc)
                value = ""
            pairs.append((value, row["rid"]))
        repo.apply_updates(conn, column, pairs)
        done += len(pairs)
        if progress:
            progress(done, total)
        log.info("%s 进度 %d/%d", column, done, total)
    return done


def segment_messages(
    conn: sqlite3.Connection,
    settings: Settings | None = None,
    progress: ProgressFn | None = None,
) -> int:
    settings = settings or get_settings()
    return _run_stage(conn, "segmented_content", segment_text, settings, progress)


def keyword_messages(
    conn: sqlite3.Connection,
    settings: Settings | None = None,
    progress: ProgressFn | None = None,
) -> int:
    settings = settings or get_settings()
    return _run_stage(
        conn,
        "keywords",
        lambda text: keywords_to_text(extract_keywords(text)),
        settings,
        progress,
    )


def run_pipeline(
    db_path: Path | str | None = None,
    *,
    steps: Iterable[str] = ("segment", "keywords", "index"),
    settings: Settings | None = None,
    progress: ProgressFn | None = None,
) -> PipelineResult:
    """一次性跑完整条流水线。可重复执行，第二次只处理新增消息。"""
    import time

    settings = settings or get_settings()
    path = Path(db_path) if db_path else settings.db_path
    started = time.perf_counter()
    result = PipelineResult()

    conn = repo.connect(path)
    try:
        repo.ensure_schema(conn, settings)
        if "segment" in steps:
            result.segmented = segment_messages(conn, settings, progress)
        if "keywords" in steps:
            result.keywords = keyword_messages(conn, settings, progress)
        if "index" in steps:
            result.indexed = repo.rebuild_fts(conn, settings)
        result.elapsed_ms = int((time.perf_counter() - started) * 1000)
        log.info("流水线完成：%s", result.to_dict())
        return result
    finally:
        conn.close()
