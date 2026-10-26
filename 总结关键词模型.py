"""兼容入口：为所有文本消息生成关键词列（原「总结关键词模型.py」）。

真正的逻辑已迁到 `app.services.segment.extract_keywords` + `app.services.ingest`。
关键词抽取改用 jieba.analyse（TF-IDF），不再依赖停更的 synonyms 包。

用法：
    python 总结关键词模型.py
"""

import sys

from app.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["keywords", *sys.argv[1:]]))
