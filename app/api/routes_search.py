"""检索接口。每次请求一个连接，避免 sqlite 连接跨线程问题。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.db import repo
from app.services.search import search

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
def api_search(
    q: str = Query(..., min_length=1, description="检索词"),
    limit: int = Query(50, ge=1, le=500),
    expand: bool = Query(True, description="是否做近义词扩展"),
    mode: str = Query("auto", pattern="^(auto|fts|like)$"),
):
    settings = get_settings()
    try:
        conn = repo.connect(settings.db_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        result = search(
            conn,
            q,
            limit=min(limit, settings.max_limit),
            expand_synonyms=expand,
            mode=None if mode == "auto" else mode,
            settings=settings,
        )
        result["count"] = len(result["hits"])
        return result
    finally:
        conn.close()
