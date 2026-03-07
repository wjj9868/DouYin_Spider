"""
直播监听 API
"""
import re
import json
from pathlib import Path
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, Body
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from backend.database import get_db
from backend.models import LiveRecord, LiveMessage
from backend.schemas.response import ApiResponse
from backend.services.live import get_live_service, LiveService
from backend.config import settings, DATA_DIR

router = APIRouter(prefix="/live", tags=["直播"])


# ============== 请求模型 ==============

class ParseUrlRequest(BaseModel):
    """解析URL请求"""
    url: str


class SearchLiveRequest(BaseModel):
    """搜索直播请求"""
    keyword: str
    count: int = 20


# ============== 工具函数 ==============

def parse_live_url(url: str) -> dict:
    """
    解析直播链接，提取房间号

    支持格式：
    - https://live.douyin.com/81804234251
    - live.douyin.com/81804234251
    - 81804234251 (纯房间号)
    - https://live.douyin.com/81804234251?xxx=xxx
    """
    url = url.strip()

    # 纯数字房间号
    if url.isdigit():
        return {"room_id": url, "type": "room_id"}

    # 直播间链接
    live_pattern = r'(?:https?://)?live\.douyin\.com/(\d+)'
    match = re.search(live_pattern, url)
    if match:
        return {"room_id": match.group(1), "type": "live_url"}

    return {"room_id": None, "type": "unknown", "error": "无法识别的链接格式"}


class LiveConnectionManager:
    """前端 WebSocket 连接管理器"""
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            # 清理断开的连接
            for conn in disconnected:
                self.disconnect(room_id, conn)


# 全局 WebSocket 管理器
ws_manager = LiveConnectionManager()


def get_ws_manager():
    return ws_manager


@router.get("/rooms", summary="获取直播记录")
async def get_live_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="状态筛选: online/offline"),
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """获取直播记录列表"""
    query = db.query(LiveRecord)

    if status:
        query = query.filter(LiveRecord.status == status)

    total = query.count()
    offset = (page - 1) * page_size

    records = query.order_by(LiveRecord.created_at.desc()).offset(offset).limit(page_size).all()

    items = []
    for r in records:
        # 统计消息数量
        msg_count = db.query(LiveMessage).filter(LiveMessage.room_id == r.room_id).count()

        items.append({
            "id": r.id,
            "room_id": r.room_id,
            "status": r.status,
            "viewer_count": r.viewer_count,
            "like_count": r.like_count,
            "follow_count": r.follow_count,
            "room_title": r.room_title,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "ended_at": r.ended_at.isoformat() if r.ended_at else None,
            "msg_count": msg_count,
            "user_nickname": r.user.nickname if r.user else None,
        })

    return ApiResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/rooms/{room_id}/start", summary="开始监听直播")
async def start_live(room_id: str) -> ApiResponse[dict]:
    """开始监听直播间

    - room_id: 直播间号（从 live.douyin.com/xxx 中获取的 xxx 部分）
    """
    live_service = get_live_service()
    live_service.set_ws_manager(ws_manager)

    result = await live_service.start_listen(room_id)

    if result["success"]:
        return ApiResponse(data=result)
    else:
        return ApiResponse(code=400, message=result["message"], data=result)


@router.post("/rooms/{room_id}/stop", summary="停止监听直播")
async def stop_live(room_id: str) -> ApiResponse[dict]:
    """停止监听直播间"""
    live_service = get_live_service()

    result = await live_service.stop_listen(room_id)

    if result["success"]:
        return ApiResponse(data=result)
    else:
        return ApiResponse(code=400, message=result["message"], data=result)


@router.get("/rooms/{room_id}/status", summary="获取监听状态")
async def get_live_status(room_id: str) -> ApiResponse[dict]:
    """获取直播间监听状态和统计信息"""
    live_service = get_live_service()
    status = live_service.get_status(room_id)
    return ApiResponse(data=status)


@router.get("/status", summary="获取所有监听状态")
async def get_all_status() -> ApiResponse[dict]:
    """获取所有直播间的监听状态"""
    live_service = get_live_service()
    status = live_service.get_status()
    return ApiResponse(data=status)


@router.get("/rooms/{room_id}/messages", summary="获取直播消息")
async def get_live_messages(
    room_id: str,
    msg_type: Optional[str] = Query(None, description="消息类型: chat/gift/like/member/follow"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """获取直播间的消息记录"""
    query = db.query(LiveMessage).filter(LiveMessage.room_id == room_id)

    if msg_type:
        query = query.filter(LiveMessage.msg_type == msg_type)

    total = query.count()
    offset = (page - 1) * page_size

    messages = query.order_by(LiveMessage.created_at.desc()).offset(offset).limit(page_size).all()

    items = []
    for m in messages:
        item = {
            "id": m.id,
            "msg_type": m.msg_type,
            "user_nickname": m.user_nickname,
            "user_sec_uid": m.user_sec_uid,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }

        if m.msg_type == "chat":
            item["content"] = m.content
        elif m.msg_type == "gift":
            item["gift_name"] = m.gift_name
            item["gift_count"] = m.gift_count
            item["to_user_nickname"] = m.to_user_nickname
        elif m.msg_type == "like":
            item["like_count"] = m.like_count
            item["like_total"] = m.like_total

        items.append(item)

    return ApiResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.delete("/rooms/{room_id}", summary="删除直播记录")
async def delete_live_record(room_id: str, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """删除直播记录及其消息"""
    # 先停止监听（如果在监听中）
    live_service = get_live_service()
    if room_id in live_service._clients:
        await live_service.stop_listen(room_id)

    # 删除消息
    db.query(LiveMessage).filter(LiveMessage.room_id == room_id).delete()

    # 删除记录
    deleted = db.query(LiveRecord).filter(LiveRecord.room_id == room_id).delete()
    db.commit()

    return ApiResponse(data={"deleted": deleted})


# ============== 用户友好的 API ==============

@router.post("/parse", summary="解析直播链接")
async def parse_live_link(request: ParseUrlRequest) -> ApiResponse[dict]:
    """解析直播链接，提取房间号

    支持格式：
    - https://live.douyin.com/81804234251
    - live.douyin.com/81804234251
    - 81804234251 (纯房间号)
    """
    result = parse_live_url(request.url)

    if not result.get("room_id"):
        return ApiResponse(code=400, message="无法识别的链接格式", data=result)

    return ApiResponse(data=result)


@router.post("/preview", summary="预览直播间信息")
async def preview_live_room(request: ParseUrlRequest) -> ApiResponse[dict]:
    """预览直播间信息 - 解析链接并获取直播间状态

    用于在开始监听前展示直播间信息
    """
    # 解析链接
    parsed = parse_live_url(request.url)

    if not parsed.get("room_id"):
        return ApiResponse(code=400, message="无法识别的链接格式", data=parsed)

    room_id = parsed["room_id"]

    # 获取直播间信息
    try:
        from backend.core.builder.auth import DouyinAuth
        from backend.core.dy_apis.douyin_api import DouyinAPI
        from backend.config import settings

        auth = DouyinAuth()
        auth.perepare_auth(settings.cookie_str, "", "")
        room_info = DouyinAPI.get_live_info(auth, room_id)

        if not room_info:
            return ApiResponse(code=404, message="直播间不存在或已结束", data={"room_id": room_id})

        # 判断直播状态
        is_living = room_info.get("room_status") == "2"

        return ApiResponse(data={
            "room_id": room_id,
            "room_title": room_info.get("room_title", ""),
            "is_living": is_living,
            "status_text": "直播中" if is_living else "未开播",
            "room_info": room_info
        })

    except Exception as e:
        return ApiResponse(code=500, message=f"获取直播间信息失败: {str(e)}", data={"room_id": room_id})


@router.post("/search", summary="搜索直播")
async def search_live(request: SearchLiveRequest) -> ApiResponse[dict]:
    """搜索直播间

    - keyword: 搜索关键词（主播昵称等）
    - count: 返回数量，默认20
    """
    try:
        from backend.core.builder.auth import DouyinAuth
        from backend.core.dy_apis.douyin_api import DouyinAPI
        from backend.config import settings
        import json

        auth = DouyinAuth()
        auth.perepare_auth(settings.cookie_str, "", "")
        result = DouyinAPI.search_live(auth, request.keyword, offset='0', num=str(request.count))

        # 将原始数据写入文件便于调试
        debug_file = DATA_DIR / "live_search_debug.json"
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        from loguru import logger
        logger.info(f"搜索数据已写入: {debug_file}")
        logger.info(f"搜索直播返回数据类型: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'N/A'}")

        if not result:
            return ApiResponse(data={"items": [], "total": 0, "keyword": request.keyword})

        # 尝试获取数据列表 - 可能在 'data' 或直接是列表
        data_list = result.get('data', []) if isinstance(result, dict) else result
        if not isinstance(data_list, list):
            data_list = []

        logger.info(f"搜索结果数量: {len(data_list)}")

        items = []
        for item in data_list:
            if not isinstance(item, dict):
                continue

            logger.info(f"原始搜索结果 keys: {item.keys()}")

            lives = item.get('lives') or {}
            if not lives:
                continue

            author = lives.get('author') or {}

            rawdata_str = lives.get('rawdata', '')
            rawdata = {}
            if rawdata_str:
                try:
                    rawdata = json.loads(rawdata_str)
                except:
                    pass

            web_rid = lives.get('aweme_id') or str(author.get('room_id', '')) or author.get('room_id_str') or ''
            
            real_room_id = ''
            stream_url = rawdata.get('stream_url', {})
            if stream_url:
                real_room_id = str(stream_url.get('id', '') or stream_url.get('id_str', ''))
            
            if not real_room_id:
                real_room_id = str(rawdata.get('id', ''))
            
            if not real_room_id and web_rid:
                real_room_id = web_rid
            
            if not real_room_id:
                continue

            title = rawdata.get('title') or lives.get('title') or ''

            cover_url = ''
            room_cover = author.get('room_cover') or lives.get('cover')
            if room_cover and isinstance(room_cover, dict):
                url_list = room_cover.get('url_list', [])
                if url_list:
                    cover_url = url_list[0]

            viewer_count = rawdata.get('user_count', 0)

            status = rawdata.get('status', 0)
            is_living = status == 2

            nickname = author.get('nickname') or ''
            sec_uid = author.get('sec_uid') or ''
            follower_count = author.get('follower_count', 0)

            avatar_url = ''
            avatar_thumb = author.get('avatar_thumb') or author.get('avatar_larger')
            if avatar_thumb and isinstance(avatar_thumb, dict):
                url_list = avatar_thumb.get('url_list', [])
                if url_list:
                    avatar_url = url_list[0]

            logger.info(f"解析结果 - web_rid: {web_rid}, real_room_id: {real_room_id}, title: {title}, is_living: {is_living}")

            status_text = "直播中" if is_living else "未开播"

            items.append({
                "room_id": real_room_id,
                "web_rid": web_rid,
                "room_title": title,
                "cover": cover_url,
                "viewer_count": viewer_count,
                "status": status,
                "is_living": is_living,
                "status_text": status_text,
                "owner": {
                    "nickname": nickname,
                    "avatar": avatar_url,
                    "sec_uid": sec_uid,
                    "follower_count": follower_count,
                }
            })

        return ApiResponse(data={
            "items": items,
            "total": len(items),
            "keyword": request.keyword
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse(code=500, message=f"搜索失败: {str(e)}", data={"items": []})


@router.post("/start-by-url", summary="通过链接开始监听")
async def start_live_by_url(request: ParseUrlRequest) -> ApiResponse[dict]:
    """通过链接开始监听 - 自动解析链接并开始监听

    支持格式：
    - https://live.douyin.com/81804234251
    - 81804234251
    """
    # 解析链接
    parsed = parse_live_url(request.url)

    if not parsed.get("room_id"):
        return ApiResponse(code=400, message="无法识别的链接格式", data=parsed)

    room_id = parsed["room_id"]

    # 开始监听
    live_service = get_live_service()
    live_service.set_ws_manager(ws_manager)

    result = await live_service.start_listen(room_id)

    if result["success"]:
        return ApiResponse(data=result)
    else:
        return ApiResponse(code=400, message=result["message"], data=result)
