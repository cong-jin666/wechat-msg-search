"""检索性能压测：LIKE 全表扫描 vs FTS5 索引。

两个维度都要看，否则会得出错误结论：
1. **全量匹配计数**（不带 LIMIT）——这才是「扫了多少行」的真实成本；
2. **不同数据量下的扩展性**——LIKE 随行数线性增长，FTS 基本平坦。

注意：`LIKE ... LIMIT 50` 在命中密集时会被 SQLite 提前短路，
看起来很快，但那只是「恰好前 50 条就命中了」，不代表全表扫描便宜。

用法：
    python -m tools.benchmark --sizes 20000,100000 --runs 10
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from app.core.config import Settings
from app.db import repo
from app.services.ingest import run_pipeline
from app.services.search import search
from tools.make_demo_db import build

TERMS = ["会议", "餐厅", "预算", "面试"]
BENCH_DIR = Path("data/bench")


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))
    return ordered[idx]


def _time(fn, runs: int) -> dict:
    timings: list[float] = []
    result = None
    for _ in range(runs):
        started = time.perf_counter()
        result = fn()
        timings.append((time.perf_counter() - started) * 1000)
    return {
        "p50_ms": round(statistics.median(timings), 3),
        "p95_ms": round(_p95(timings), 3),
        "result": result,
    }


def measure(conn, settings: Settings, runs: int) -> dict:
    content = "StrContent"
    like_counts, fts_counts, like_top, fts_top, fts_fast = [], [], [], [], []
    for term in TERMS:
        like_counts.append(
            _time(lambda t=term: conn.execute(
                f"SELECT COUNT(*) FROM MSG WHERE {content} LIKE ?", (f"%{t}%",)
            ).fetchone()[0], runs)
        )
        fts_counts.append(
            _time(lambda t=term: conn.execute(
                "SELECT COUNT(*) FROM msg_fts WHERE msg_fts MATCH ?", (f'"{t}"',)
            ).fetchone()[0], runs)
        )
        like_top.append(_time(lambda t=term: search(conn, t, limit=50, expand_synonyms=False, mode="like", settings=settings)["hits"], runs))
        fts_top.append(_time(lambda t=term: search(conn, t, limit=50, expand_synonyms=False, mode="fts", settings=settings)["hits"], runs))
        fts_fast.append(_time(lambda t=term: search(conn, t, limit=50, expand_synonyms=False, mode="fts", settings=settings, ranked=False)["hits"], runs))

    def agg(items: list[dict]) -> dict:
        return {
            "p50_ms": round(statistics.median([i["p50_ms"] for i in items]), 3),
            "p95_ms": round(max(i["p95_ms"] for i in items), 3),
        }

    return {
        "like_count": agg(like_counts),
        "fts_count": agg(fts_counts),
        "like_top50": agg(like_top),
        "fts_top50": agg(fts_top),
        "fts_top50_unranked": agg(fts_fast),
        "like_count_abs": [i["result"] for i in like_counts],
        "fts_count_abs": [i["result"] for i in fts_counts],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="检索性能压测（LIKE vs FTS5）")
    parser.add_argument("--sizes", default="20000,100000", help="要测试的数据量，逗号分隔")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--reuse", action="store_true", help="复用已建好的压测库，跳过生成与索引")
    args = parser.parse_args()

    sizes = [int(x) for x in args.sizes.split(",")]
    BENCH_DIR.mkdir(parents=True, exist_ok=True)
    report: list[dict] = []

    for size in sizes:
        db_path = BENCH_DIR / f"bench_{size}.db"
        settings = Settings(db_path=db_path)
        if args.reuse and db_path.exists():
            pipeline_ms = 0
        else:
            build(db_path, size)
            pipeline_ms = run_pipeline(db_path, settings=settings).elapsed_ms
        conn = repo.connect(db_path)
        try:
            metrics = measure(conn, settings, args.runs)
        finally:
            conn.close()
        metrics["rows"] = size
        metrics["index_build_ms"] = pipeline_ms
        report.append(metrics)
        print(f"[{size} 行] 索引构建 {pipeline_ms} ms｜"
              f"全量匹配 LIKE {metrics['like_count']['p50_ms']} ms vs FTS {metrics['fts_count']['p50_ms']} ms")

    print("\n| 数据量 | LIKE 全量匹配 P50 | FTS 全量匹配 P50 | LIKE 取前50 P50 | FTS 取前50(排序) | FTS 取前50(早停) |")
    print("|---|---|---|---|---|---|")
    for row in report:
        print(
            f"| {row['rows']} | {row['like_count']['p50_ms']} ms | {row['fts_count']['p50_ms']} ms | "
            f"{row['like_top50']['p50_ms']} ms | {row['fts_top50']['p50_ms']} ms | {row['fts_top50_unranked']['p50_ms']} ms |"
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
