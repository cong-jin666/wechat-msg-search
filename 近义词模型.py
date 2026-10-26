"""兼容入口：按关键词 + 近义词检索聊天记录（原「近义词模型.py」）。

原实现有两个硬伤，已在新实现里修掉：
1. 用户输入直接拼进 SQL（`f"... LIKE '%{word}%'"`）—— 现在全部参数化；
2. 近义词条件写成 `segmented_content IN ('词1','词2')`，而该列是整句分词结果，
   永远不会等于单个词，等于没生效 —— 现在每个词独立参与 MATCH。

用法：
    python 近义词模型.py 会议
    python 近义词模型.py 会议 --limit 30 --no-expand
"""

import sys

from app.cli import main

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        raise SystemExit(1)
    raise SystemExit(main(["search", *args]))
