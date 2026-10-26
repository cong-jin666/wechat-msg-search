"""长任务接口：提交 → 返回 task_id → 轮询状态。

解析/分词不能塞在一个 HTTP 请求里同步跑完，否则必然超时并阻塞事件循环。
这里用线程 + 内存任务表实现最小可用版本：单机个人使用足够，
需要多机或持久化时把 `TASKS` 换成 Redis / 数据库即可，接口契约不变。
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db import repo
from app.services.ingest import run_pipeline

log = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["tasks"])

TASKS: dict[str, dict] = {}
_LOCK = threading.Lock()


class TaskRequest(BaseModel):
    kind: Literal["pipeline", "segment", "keywords", "index"] = "pipeline"
    db_path: str | None = None


def _update(task_id: str, **fields) -> None:
    with _LOCK:
        task = TASKS.setdefault(task_id, {})
        task.update(fields)
        task["updated_at"] = time.time()


def _run(task_id: str, kind: str, db_path: str | None) -> None:
    _update(task_id, status="running", started_at=time.time())

    def progress(done: int, total: int) -> None:
        percent = int(done * 100 / total) if total else 100
        _update(task_id, done=done, total=total, percent=percent)

    steps = {
        "pipeline": ("segment", "keywords", "index"),
        "segment": ("segment",),
        "keywords": ("keywords",),
        "index": ("index",),
    }[kind]
    try:
        result = run_pipeline(db_path, steps=steps, progress=progress)
        _update(task_id, status="success", percent=100, result=result.to_dict())
    except Exception as exc:  # 任务失败要写进状态，前端才能提示
        log.exception("任务失败 %s", task_id)
        _update(task_id, status="failed", error=f"{type(exc).__name__}: {exc}")


@router.post("/tasks", status_code=202)
def create_task(req: TaskRequest, background: BackgroundTasks):
    task_id = uuid.uuid4().hex
    _update(task_id, status="pending", percent=0, kind=req.kind, error=None)
    background.add_task(_run, task_id, req.kind, req.db_path)
    return {"task_id": task_id, "status": "pending"}


@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    with _LOCK:
        task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"task_id": task_id, **task}


@router.get("/stats")
def get_stats():
    settings = get_settings()
    try:
        conn = repo.connect(settings.db_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        return repo.stats(conn, settings)
    finally:
        conn.close()
