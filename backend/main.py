"""
FastAPI 主入口
"""
import sys
from pathlib import Path
# 将项目根目录添加到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from backend.config import API_PREFIX
from backend.database import init_db
from backend.api import (
    works_router, users_router, search_router,
    tasks_router, live_router, export_router
)
from backend.api.live import LiveConnectionManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    logger.info("正在初始化数据库...")
    init_db()
    logger.info("数据库初始化完成")

    # 加载 Cookie
    from dotenv import load_dotenv
    import os
    load_dotenv()

    cookie = os.getenv("DY_COOKIES", "")
    if cookie:
        from backend.services.collector import get_collector
        collector = get_collector()
        collector.cookie_str = cookie
        collector.douyin.cookie_str = cookie
        logger.info("Cookie 已加载")

    logger.info("服务启动完成")

    yield

    # 关闭时
    logger.info("服务正在关闭...")


# 创建应用
app = FastAPI(
    title="DouYin Spider API",
    description="抖音数据采集系统 API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(works_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)
app.include_router(tasks_router, prefix=API_PREFIX)
app.include_router(live_router, prefix=API_PREFIX)
app.include_router(export_router, prefix=API_PREFIX)


@app.get("/", tags=["根"])
async def root():
    """根路径"""
    return {"message": "DouYin Spider API", "version": "2.0.0"}


@app.get("/health", tags=["健康检查"])
async def health():
    """健康检查"""
    return {"status": "healthy"}


# WebSocket 直播弹幕
ws_manager = LiveConnectionManager()


@app.websocket("/ws/live/{room_id}")
async def websocket_live(websocket: WebSocket, room_id: str):
    """直播弹幕 WebSocket"""
    await ws_manager.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(room_id, websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
