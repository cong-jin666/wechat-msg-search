from app.db import repo
from app.services.ingest import run_pipeline


def test_schema_is_idempotent(ready_conn, settings):
    first = repo.ensure_schema(ready_conn, settings)
    second = repo.ensure_schema(ready_conn, settings)
    assert second["added_columns"] == []
    assert "segmented_content" in first["columns"]


def test_pipeline_marks_all_text_rows(ready_conn, settings):
    ready_conn.close()
    result = run_pipeline(settings.db_path, settings=settings)
    assert result.segmented == 5  # type=3 的图片消息被过滤
    assert result.indexed == 5

    conn = repo.connect(settings.db_path)
    try:
        assert repo.count_pending(conn, "segmented_content", settings) == 0
        assert repo.count_pending(conn, "keywords", settings) == 0
    finally:
        conn.close()


def test_pipeline_is_incremental(ready_conn, settings):
    """第二次运行只处理新增消息 —— 原脚本在这里是永远跳过整段回填。"""
    ready_conn.close()
    run_pipeline(settings.db_path, settings=settings)

    conn = repo.connect(settings.db_path)
    try:
        conn.execute(
            "INSERT INTO MSG (StrTalker, StrContent, type, CreateTime) VALUES (?, ?, ?, ?)",
            ("wxid_new", "新来的消息也要能被检索到", 1, 1700001000),
        )
        conn.commit()
        assert repo.count_pending(conn, "segmented_content", settings) == 1
    finally:
        conn.close()

    second = run_pipeline(settings.db_path, settings=settings)
    assert second.segmented == 1
    assert second.indexed == 6


def test_batch_size_is_respected(ready_conn, settings):
    """batch_size=2 时分多批处理，结果仍要全部写完。"""
    assert settings.batch_size == 2
    ready_conn.close()
    run_pipeline(settings.db_path, settings=settings)
    conn = repo.connect(settings.db_path)
    try:
        empty = conn.execute(
            "SELECT COUNT(*) AS n FROM MSG WHERE type = 1 AND (segmented_content IS NULL OR segmented_content = '')"
        ).fetchone()["n"]
        assert empty == 0
    finally:
        conn.close()
