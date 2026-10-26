"""命令行入口：`python -m app.cli <command>`。

桌面端 / Web 端 / CLI 共用 services 层，三条入口逻辑一致。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.logging import setup_logging
from app.db import repo
from app.services.ingest import keyword_messages, run_pipeline, segment_messages
from app.services.search import search


def _settings(args: argparse.Namespace) -> Settings:
    base = get_settings()
    if getattr(args, "db", None):
        return base.model_copy(update={"db_path": Path(args.db)})
    return base


def cmd_stats(args) -> int:
    settings = _settings(args)
    conn = repo.connect(settings.db_path)
    try:
        print(json.dumps(repo.stats(conn, settings), ensure_ascii=False, indent=2))
    finally:
        conn.close()
    return 0


def cmd_pipeline(args) -> int:
    settings = _settings(args)

    def progress(done: int, total: int) -> None:
        print(f"\r进度 {done}/{total}", end="", flush=True)

    result = run_pipeline(settings.db_path, settings=settings, progress=progress)
    print()
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_stage(args) -> int:
    settings = _settings(args)
    conn = repo.connect(settings.db_path)
    try:
        repo.ensure_schema(conn, settings)
        if args.command == "segment":
            n = segment_messages(conn, settings)
        elif args.command == "keywords":
            n = keyword_messages(conn, settings)
        else:
            n = repo.rebuild_fts(conn, settings)
        print(f"{args.command}: {n}")
    finally:
        conn.close()
    return 0


def cmd_search(args) -> int:
    settings = _settings(args)
    conn = repo.connect(settings.db_path)
    try:
        result = search(
            conn,
            args.query,
            limit=args.limit,
            expand_synonyms=not args.no_expand,
            mode=None if args.mode == "auto" else args.mode,
            settings=settings,
        )
    finally:
        conn.close()
    print(f"模式 {result['mode']}｜扩展词 {result['terms']}｜命中 {len(result['hits'])} 条")
    for hit in result["hits"]:
        print(f"- [{hit['created_at']}] {hit['talker']}: {hit['content'][:60]}")
    return 0


def cmd_serve(args) -> int:
    import uvicorn

    uvicorn.run("app.main:app", host=args.host, port=args.port, workers=1)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wechat-msg", description="微信聊天记录检索工具")
    parser.add_argument("--db", help="数据库路径，默认读 WCM_DB_PATH 或 data/de_MSG0.db")
    parser.add_argument("--log-level", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("stats", help="查看数据与索引状态").set_defaults(func=cmd_stats)
    sub.add_parser("pipeline", help="跑完整流水线：分词 + 关键词 + 建索引").set_defaults(func=cmd_pipeline)
    for name, help_text in (
        ("segment", "只跑分词"),
        ("keywords", "只跑关键词"),
        ("index", "重建 FTS 索引"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(func=cmd_stage)

    p = sub.add_parser("search", help="检索")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--mode", choices=["auto", "fts", "like"], default="auto")
    p.add_argument("--no-expand", action="store_true", help="关闭近义词扩展")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("serve", help="启动 Web 服务")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.set_defaults(func=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = _settings(args)
    setup_logging(args.log_level or settings.log_level)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        print("提示：用 --db 指定数据库路径，或设置环境变量 WCM_DB_PATH", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
