"""FastAPI 入口：`uvicorn app.main:app --reload` 或 `python -m app.main`。

单 worker 运行：FTS 索引与 sqlite 连接不跨进程共享，多 worker 只会重复建索引。
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import routes_analyze, routes_search, routes_task
from app.core.config import BASE_DIR, get_settings
from app.core.logging import get_logger

log = get_logger(__name__)
settings = get_settings()

# 前端两套产物，优先用 Vite 构建版：
#   frontend/dist  —— npm run build 产物（runtime-only，体积小）
#   web/           —— 重构前的单文件版，未构建时的兜底，克隆即可跑
LEGACY_WEB_DIR = BASE_DIR / "web"
DIST_DIR = BASE_DIR / "frontend" / "dist"
WEB_DIR = DIST_DIR if (DIST_DIR / "index.html").exists() else LEGACY_WEB_DIR

app = FastAPI(title="微信聊天记录智能检索", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_search.router)
app.include_router(routes_task.router)
app.include_router(routes_analyze.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": __version__,
        "db_path": str(settings.db_path),
        "db_exists": settings.db_path.exists(),
        "web_dir": WEB_DIR.name if WEB_DIR.exists() else None,
        "frontend": "vite" if WEB_DIR == DIST_DIR else "legacy",
    }


if WEB_DIR.exists():
    if (WEB_DIR / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(WEB_DIR / "index.html")


def main() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False, workers=1)


if __name__ == "__main__":
    main()
