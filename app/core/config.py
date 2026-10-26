"""集中配置：所有路径与运行参数从环境变量 / .env 读取，代码里不再硬编码。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """运行配置。环境变量前缀 WCM_，例如 WCM_DB_PATH=D:/data/de_MSG0.db。"""

    model_config = SettingsConfigDict(
        env_prefix="WCM_",
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_path: Path = BASE_DIR / "data" / "de_MSG0.db"
    synonym_file: Path = BASE_DIR / "data" / "synonyms.txt"
    log_level: str = "INFO"

    # 批量写库的分片大小，避免一次性把全表读进内存
    batch_size: int = 2000
    # 单次检索返回上限
    max_limit: int = 200
    # MSG 表里正文列的候选名（PyWxDump 导出的库大小写不统一）
    content_columns: tuple[str, ...] = ("StrContent", "strContent")
    # 只处理文本消息
    text_message_types: tuple[int, ...] = (1,)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """测试里切换配置后调用。"""
    get_settings.cache_clear()
