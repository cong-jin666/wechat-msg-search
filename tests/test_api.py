"""API 冒烟测试：检索、任务状态、SSE 三个入口各跑一次。"""

from __future__ import annotations

import importlib
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, reset_settings_cache
from app.services.ingest import run_pipeline


def _prepare_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE MSG (
            localId INTEGER PRIMARY KEY,
            StrTalker TEXT,
            StrContent TEXT,
            type INTEGER,
            CreateTime INTEGER
        );
        """
    )
    conn.executemany(
        "INSERT INTO MSG (StrTalker, StrContent, type, CreateTime) VALUES (?, ?, ?, ?)",
        [
            ("wxid_a", "今天天气不错，去公园散步", 1, 1700000000),
            ("wxid_b", "这周的会议改成周四下午", 1, 1700000060),
            ("wxid_b", "餐厅位置我发你", 1, 1700000120),
        ],
    )
    conn.commit()
    conn.close()
    run_pipeline(path, settings=Settings(db_path=path, synonym_file=path.parent / "syn.txt"))


@pytest.fixture()
def client(monkeypatch, tmp_path):
    db_path = tmp_path / "api.db"
    _prepare_db(db_path)
    monkeypatch.setenv("WCM_DB_PATH", str(db_path))
    reset_settings_cache()

    import app.main as main_module

    main_module = importlib.reload(main_module)
    with TestClient(main_module.app) as c:
        yield c
    reset_settings_cache()


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["db_exists"] is True


def test_search_endpoint(client):
    body = client.get("/api/search", params={"q": "天气"}).json()
    assert body["mode"] == "fts"
    assert body["count"] == 1
    assert "公园" in body["hits"][0]["content"]


def test_search_requires_query(client):
    assert client.get("/api/search", params={"q": ""}).status_code == 422


def test_stats_endpoint(client):
    body = client.get("/api/stats").json()
    assert body["messages"] == 3
    assert body["fts_rows"] == 3


def test_task_lifecycle(client):
    created = client.post("/api/tasks", json={"kind": "index"})
    assert created.status_code == 202
    task_id = created.json()["task_id"]
    state = client.get(f"/api/tasks/{task_id}").json()
    assert state["status"] == "success"
    assert state["result"]["indexed"] == 3


def test_unknown_task_returns_404(client):
    assert client.get("/api/tasks/not-exist").status_code == 404


def test_analyze_sse_stream(client):
    with client.stream("GET", "/api/analyze", params={"delay": 0}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())
    assert "event: chunk" in body
    assert "event: done" in body
    assert "条文本消息" in body
