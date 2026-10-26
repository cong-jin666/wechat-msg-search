"""生成脱敏演示库：结构对齐微信 MSG 表，内容全部是伪造句子。

用法：
    python -m tools.make_demo_db --rows 20000 --out data/de_MSG0.db
"""

from __future__ import annotations

import argparse
import random
import sqlite3
from pathlib import Path

TOPICS = [
    "今天天气不错，下午去公园散步吧",
    "这周的会议改成周四下午，会议室在三楼",
    "餐厅的位置我发你一下，六点半到就行",
    "工地那边的材料明天早上送到，记得签收",
    "项目进度我整理成文档了，晚点发群里",
    "周末要不要一起去爬山，天气预报说是晴天",
    "报销单已经提交，财务说下周能下来",
    "这个方案的预算还要再压一压，超了百分之十",
    "客户反馈说界面太复杂，希望简化操作流程",
    "明天上午的面试安排在公司十二楼会议室",
    "快递到了，放在门口的柜子里",
    "记得把合同扫描件发我一份，要盖章的那版",
    "下午的评审会取消了，改到周五上午十点",
    "地铁四号线今天晚点，我可能要迟到十分钟",
    "这道菜的做法我写下来了，你照着做就行",
]
TALKERS = ["wxid_demo01", "wxid_demo02", "wxid_demo03", "wxid_demo04", "demo_group@chatroom"]


def build(path: Path, rows: int, seed: int = 42) -> None:
    random.seed(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.executescript(
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
    base_time = 1_700_000_000
    batch = []
    for i in range(rows):
        talker = random.choice(TALKERS)
        content = random.choice(TOPICS)
        if i % 7 == 0:
            content = f"{content}（第 {i} 条）"
        batch.append((talker, content, 1, base_time + i * 60))
    # 掺入非文本消息，验证过滤逻辑
    for i in range(rows // 20):
        batch.append((random.choice(TALKERS), "[图片]", 3, base_time + i * 600))
    conn.executemany(
        "INSERT INTO MSG (StrTalker, StrContent, type, CreateTime) VALUES (?, ?, ?, ?)",
        batch,
    )
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM MSG").fetchone()[0]
    conn.close()
    print(f"已生成 {path}：共 {total} 行（文本 {rows} 行）")


def main() -> None:
    parser = argparse.ArgumentParser(description="生成脱敏演示数据库")
    parser.add_argument("--rows", type=int, default=20000)
    parser.add_argument("--out", default="data/de_MSG0.db")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    build(Path(args.out), args.rows, args.seed)


if __name__ == "__main__":
    main()
