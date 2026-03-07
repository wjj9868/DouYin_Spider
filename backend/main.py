"""
FastAPI 主入口
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from backend.core.logger import setup_logging
setup_logging()

from backend.config import API_PREFIX
from backend.database import init_db
from backend.api import (
    works_router, users_router, search_router,
    tasks_router, live_router, export_router
)
from backend.api.scheduled_tasks import router as scheduled_tasks_router
from backend.api.cookies import router as cookies_router
from backend.api.live import get_ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info("正在初始化数据库...")
    init_db()
    logger.info("数据库初始化完成")

    from backend.database import SessionLocal
    from backend.models import Cookie as CookieModel

    db = SessionLocal()
    live_cookie_str = ""
    try:
        default_cookie = db.query(CookieModel).filter(
            CookieModel.cookie_type == "default",
            CookieModel.is_active == True
        ).first()

        if default_cookie:
            from backend.services.collector import get_collector
            collector = get_collector()
            collector.cookie_str = default_cookie.cookie_str
            if hasattr(collector, 'douyin') and collector.douyin:
                collector.douyin.cookie_str = default_cookie.cookie_str
            logger.info(f"默认 Cookie 已加载: {default_cookie.name}")
        else:
            logger.warning("未找到启用的默认 Cookie，请在系统设置中添加")

        live_cookie = db.query(CookieModel).filter(
            CookieModel.cookie_type == "live",
            CookieModel.is_active == True
        ).first()

        if live_cookie:
            live_cookie_str = live_cookie.cookie_str
            from backend.core.utils.common_util import dy_live_auth
            if dy_live_auth:
                dy_live_auth.perepare_auth(live_cookie.cookie_str, "", "")
            logger.info(f"直播 Cookie 已加载: {live_cookie.name}")
        else:
            logger.warning("未找到启用的直播 Cookie，请在系统设置中添加")
    finally:
        db.close()

    from backend.services.scheduler import get_scheduler
    scheduler = get_scheduler()
    await scheduler.start()
    logger.info("定时任务调度器已启动")

    # 初始化直播服务
    from backend.services.live import get_live_service
    live_service = get_live_service()
    live_service.cookie_str = live_cookie_str
    live_service.set_ws_manager(get_ws_manager())
    logger.info("直播服务已初始化")

    logger.info("服务启动完成")

    yield

    logger.info("服务正在关闭...")
    await scheduler.stop()

    # 停止所有直播监听
    await live_service.stop_all()
    logger.info("直播监听已停止")


app = FastAPI(
    title="DouYin Spider API",
    description="抖音数据采集系统 API",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(works_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)
app.include_router(tasks_router, prefix=API_PREFIX)
app.include_router(live_router, prefix=API_PREFIX)
app.include_router(export_router, prefix=API_PREFIX)
app.include_router(scheduled_tasks_router, prefix=API_PREFIX)
app.include_router(cookies_router, prefix=API_PREFIX)


@app.get("/", tags=["根"])
async def root():
    """根路径"""
    return {"message": "DouYin Spider API", "version": "2.0.0"}


@app.get("/health", tags=["健康检查"])
async def health():
    """健康检查"""
    return {"status": "healthy"}


# WebSocket 直播弹幕端点
@app.websocket("/ws/live/{room_id}")
async def websocket_live(websocket: WebSocket, room_id: str):
    """直播弹幕 WebSocket - 前端连接此端点接收实时消息

    使用方式：
    1. 先调用 POST /api/live/rooms/{room_id}/start 开始监听
    2. 连接 ws://host/ws/live/{room_id} 接收消息
    3. 监听结束后调用 POST /api/live/rooms/{room_id}/stop
    """
    ws_manager = get_ws_manager()
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
