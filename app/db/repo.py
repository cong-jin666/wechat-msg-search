"""数据访问层：全部 SQL 走参数化，列名从白名单里取，杜绝拼接。

这一层只关心「库里有什么、怎么读写」，不做业务判断。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Sequence

from app.core.config import Settings
from app.core.logging import get_logger

log = get_logger(__name__)

SCHEMA_FILE = Path(__file__).with_name("schema.sql")

# 只允许出现的列名，防止列名参与 SQL 拼接时被注入
ALLOWED_COLUMNS = {"segmented_content", "keywords"}
MESSAGE_TABLE = "MSG"


def connect(db_path: Path | str) -> sqlite3.Connection:
    """打开数据库连接。连接失败由调用方处理，这里不吞异常。"""
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"数据库不存在：{path}")
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def table_exists(conn: sqlite3.Connection, name: str = MESSAGE_TABLE) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone()
    return row is not None


def table_columns(conn: sqlite3.Connection, name: str = MESSAGE_TABLE) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA table_info({name})")]


def resolve_column(columns: Iterable[str], candidates: Sequence[str]) -> str | None:
    """按候选名找真实列名（不同版本导出工具大小写不一致）。"""
    lower_map = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def ensure_schema(conn: sqlite3.Connection, settings: Settings) -> dict[str, object]:
    """补列、建索引、建 FTS5 虚表与触发器。幂等，可重复调用。"""
    if not table_exists(conn):
        raise RuntimeError(f"库中没有 {MESSAGE_TABLE} 表，可能不是微信导出的数据库")

    columns = table_columns(conn)
    added: list[str] = []
    for col in ("segmented_content", "keywords"):
        if col not in {c.lower() for c in columns}:
            conn.execute(f"ALTER TABLE {MESSAGE_TABLE} ADD COLUMN {col} TEXT")
            added.append(col)
    if added:
        log.info("新增列：%s", ", ".join(added))
        columns = table_columns(conn)

    # 会话人索引：按 StrTalker 过滤 / 分组都要用
    if resolve_column(columns, ["StrTalker"]):
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_msg_talker ON {MESSAGE_TABLE}(StrTalker)")

    # 增量扫描索引：只处理「还没分词」的行
    type_col = resolve_column(columns, ["type"])
    if type_col:
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_msg_type_seg ON {MESSAGE_TABLE}({type_col}, segmented_content)"
        )

    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.commit()
    return {"added_columns": added, "columns": table_columns(conn)}


def _type_filter(columns: Sequence[str], settings: Settings) -> tuple[str, list[object]]:
    """生成「仅文本消息」的 WHERE 片段与参数。"""
    type_col = resolve_column(columns, ["type"])
    if not type_col:
        return "1 = 1", []
    placeholders = ",".join("?" for _ in settings.text_message_types)
    return f"{type_col} IN ({placeholders})", list(settings.text_message_types)


def count_messages(conn: sqlite3.Connection, settings: Settings) -> int:
    columns = table_columns(conn)
    where, params = _type_filter(columns, settings)
    row = conn.execute(f"SELECT COUNT(*) AS n FROM {MESSAGE_TABLE} WHERE {where}", params).fetchone()
    return int(row["n"])


def count_pending(conn: sqlite3.Connection, column: str, settings: Settings) -> int:
    """统计还有多少行没处理。column 必须在白名单内。"""
    if column not in ALLOWED_COLUMNS:
        raise ValueError(f"非法列名：{column}")
    columns = table_columns(conn)
    where, params = _type_filter(columns, settings)
    sql = f"SELECT COUNT(*) AS n FROM {MESSAGE_TABLE} WHERE {where} AND {column} IS NULL"
    return int(conn.execute(sql, params).fetchone()["n"])


def fetch_pending_batch(
    conn: sqlite3.Connection, column: str, limit: int, settings: Settings
) -> list[sqlite3.Row]:
    """取一批待处理行，带上 rowid 以便精确更新（不再用 StrTalker+StrContent 定位）。"""
    if column not in ALLOWED_COLUMNS:
        raise ValueError(f"非法列名：{column}")
    columns = table_columns(conn)
    content_col = resolve_column(columns, settings.content_columns)
    if not content_col:
        raise RuntimeError(f"{MESSAGE_TABLE} 表缺少正文列：{settings.content_columns}")
    where, params = _type_filter(columns, settings)
    sql = (
        f"SELECT rowid AS rid, {content_col} AS content FROM {MESSAGE_TABLE} "
        f"WHERE {where} AND {column} IS NULL "
        f"AND {content_col} IS NOT NULL AND {content_col} <> '' "
        f"ORDER BY rowid LIMIT ?"
    )
    return list(conn.execute(sql, [*params, limit]))


def apply_updates(
    conn: sqlite3.Connection, column: str, pairs: Sequence[tuple[str, int]]
) -> None:
    """一次事务批量写回。pairs = [(value, rowid), ...]"""
    if column not in ALLOWED_COLUMNS:
        raise ValueError(f"非法列名：{column}")
    if not pairs:
        return
    conn.executemany(
        f"UPDATE {MESSAGE_TABLE} SET {column} = ? WHERE rowid = ?", pairs
    )
    conn.commit()


def count_indexed(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS n FROM msg_fts").fetchone()
    return int(row["n"])


def rebuild_fts(conn: sqlite3.Connection, settings: Settings) -> int:
    """按主表重建 FTS 索引（用于历史数据或索引漂移后的修复）。"""
    conn.execute("DELETE FROM msg_fts")
    columns = table_columns(conn)
    where, params = _type_filter(columns, settings)
    rows = conn.execute(
        f"SELECT rowid AS rid, segmented_content AS seg FROM {MESSAGE_TABLE} "
        f"WHERE {where} AND segmented_content IS NOT NULL AND segmented_content <> ''",
        params,
    ).fetchall()
    conn.executemany(
        "INSERT INTO msg_fts(rowid, segmented) VALUES (?, ?)",
        [(r["rid"], r["seg"]) for r in rows],
    )
    conn.commit()
    log.info("FTS 重建完成：%d 行", len(rows))
    return len(rows)


def stats(conn: sqlite3.Connection, settings: Settings) -> dict[str, object]:
    return {
        "db_path": str(settings.db_path),
        "messages": count_messages(conn, settings),
        "segmented_pending": count_pending(conn, "segmented_content", settings),
        "keywords_pending": count_pending(conn, "keywords", settings),
        "fts_rows": count_indexed(conn),
    }
