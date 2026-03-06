"""
直播监听 API
"""
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import LiveRecord, User
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/live", tags=["直播"])

# WebSocket 连接管理器
manager = None


def get_manager():
    global manager
    if manager is None:
        manager = LiveConnectionManager()
    return manager


class LiveConnectionManager:
    """WebSocket 连接管理器"""
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)


# WebSocket 路由将在 main.py 中注册


@router.get("/rooms", summary="获取直播记录")
async def get_live_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """获取直播记录列表"""
    query = db.query(LiveRecord)
    total = query.count()
    offset = (page - 1) * page_size

    records = query.order_by(LiveRecord.created_at.desc()).offset(offset).limit(page_size).all()

    items = []
    for r in records:
        items.append({
            "id": r.id,
            "room_id": r.room_id,
            "status": r.status,
            "viewer_count": r.viewer_count,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "ended_at": r.ended_at.isoformat() if r.ended_at else None,
            "user_nickname": r.user.nickname if r.user else None,
        })

    return ApiResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/rooms/{room_id}/start", summary="开始监听直播")
async def start_live(room_id: str, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """开始监听直播间"""
    # TODO: 实现直播监听启动
    return ApiResponse(data={"room_id": room_id, "status": "listening"})


@router.post("/rooms/{room_id}/stop", summary="停止监听直播")
async def stop_live(room_id: str, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """停止监听直播间"""
    # TODO: 实现直播监听停止
    return ApiResponse(data={"room_id": room_id, "status": "stopped"})
