"""兼容入口：为所有文本消息生成分词列（原「提取词模型.py」）。

真正的逻辑已迁到 `app.services.ingest`：
- 按 rowid 定位 + 批量事务写回（原来是 StrTalker+StrContent 逐行更新，N² 全表扫描）
- 按 `segmented_content IS NULL` 增量处理（原来列已存在就整段跳过，新消息永远进不来）

用法：
    python 提取词模型.py
    python 提取词模型.py --db D:/path/de_MSG0.db
"""

import sys

from app.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["segment", *sys.argv[1:]]))
