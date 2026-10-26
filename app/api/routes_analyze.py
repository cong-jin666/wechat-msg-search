"""分析接口：SSE 流式返回。

前端用 EventSource 只能发 GET，所以这里提供 GET（方便演示）和 POST（可带参数）两个入口。
事件格式：event: chunk / done / error，data 为 JSON。
"""

from __future__ import annotations

import json
import time

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db import repo
from app.services.analyze import local_summary_chunks

log = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["analyze"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # 反代下禁用缓冲，否则流式会变成一次性返回
}


def _event(name: str, payload: dict) -> str:
    return f"event: {name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _stream(delay: float = 0.08):
    settings = get_settings()
    conn = None
    try:
        conn = repo.connect(settings.db_path)
        for chunk in local_summary_chunks(conn, settings):
            yield _event("chunk", {"text": chunk})
            if delay:
                time.sleep(delay)
        yield _event("done", {"ok": True})
    except FileNotFoundError as exc:
        yield _event("error", {"message": str(exc)})
    except Exception as exc:  # 流已经开始，只能以事件形式报错
        log.exception("分析失败")
        yield _event("error", {"message": f"{type(exc).__name__}: {exc}"})
    finally:
        if conn is not None:
            conn.close()


@router.get("/analyze")
def analyze_get(delay: float = Query(0.08, ge=0, le=1.0)):
    settings = get_settings()
    if not settings.db_path.exists():
        raise HTTPException(status_code=503, detail=f"数据库不存在：{settings.db_path}")
    return StreamingResponse(_stream(delay), media_type="text/event-stream", headers=SSE_HEADERS)


@router.post("/analyze")
def analyze_post(delay: float = Query(0.08, ge=0, le=1.0)):
    return analyze_get(delay)
