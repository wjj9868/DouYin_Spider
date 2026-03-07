"""
配置管理
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载环境变量
load_dotenv(BASE_DIR / ".env")

# 数据目录
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 数据库配置
DATABASE_URL = f"sqlite:///{DATA_DIR}/douyin.db"

# 核心模块路径
CORE_DIR = BASE_DIR / "core"
STATIC_DIR = CORE_DIR / "static"

# 导出目录
EXPORT_DIR = DATA_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)

# 媒体目录
MEDIA_DIR = DATA_DIR / "media"
MEDIA_DIR.mkdir(exist_ok=True)

# Cookie 配置
COOKIE_FILE = BASE_DIR / ".env"

# API 配置
API_PREFIX = "/api"

# 分页配置
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class Settings:
    """应用配置"""
    def __init__(self):
        self.cookie_str = os.getenv("DY_COOKIES", "")


settings = Settings()
