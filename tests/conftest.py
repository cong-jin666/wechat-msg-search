"""测试夹具：用临时 sqlite 建一个和微信导出结构一致的 MSG 表，不依赖真实聊天记录。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.core.config import Settings, reset_settings_cache
from app.db import repo

SAMPLE_MESSAGES = [
    ("wxid_a", "今天天气不错，下午去公园散步吧", 1, 1700000000),
    ("wxid_a", "好的，我三点到南门等你", 1, 1700000060),
    ("wxid_b", "这周的会议改成周四下午了", 1, 1700000120),
    ("wxid_b", "另外餐厅的位置我发你一下", 1, 1700000180),
    ("wxid_c", "工地那边的材料明天送到", 1, 1700000240),
    ("wxid_c", "[图片]", 3, 1700000300),
]


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    reset_settings_cache()
    return Settings(
        db_path=tmp_path / "test.db",
        synonym_file=tmp_path / "synonyms.txt",
        batch_size=2,
    )


@pytest.fixture()
def synonym_file(settings: Settings) -> Path:
    path = settings.synonym_file
    path.write_text("会议 开会 例会\n餐厅 饭店 馆子\n", encoding="utf-8")
    return path


@pytest.fixture()
def conn(settings: Settings):
    connection = sqlite3.connect(settings.db_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE MSG (
            localId INTEGER PRIMARY KEY,
            StrTalker TEXT,
            StrContent TEXT,
            type INTEGER,
            CreateTime INTEGER,
            Des INTEGER
        );
        """
    )
    connection.executemany(
        "INSERT INTO MSG (StrTalker, StrContent, type, CreateTime) VALUES (?, ?, ?, ?)",
        SAMPLE_MESSAGES,
    )
    connection.commit()
    yield connection
    connection.close()


@pytest.fixture()
def ready_conn(conn, settings: Settings):
    repo.ensure_schema(conn, settings)
    return conn
