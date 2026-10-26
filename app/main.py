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
WEB_DIR = BASE_DIR / "web"

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
    }


if WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(WEB_DIR / "index.html")


def main() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False, workers=1)


if __name__ == "__main__":
    main()
