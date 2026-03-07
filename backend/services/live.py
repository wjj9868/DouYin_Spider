"""
直播服务 - 管理直播间监听、消息处理和广播
"""
import asyncio
import gzip
import json
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from urllib.parse import urlencode

import websockets
from loguru import logger
from sqlalchemy.orm import Session

import backend.core.static.Live_pb2 as Live_pb2
from backend.core.dy_apis.douyin_api import DouyinAPI
from backend.core.builder.header import HeaderBuilder
from backend.core.builder.params import Params
from backend.core.utils.dy_util import generate_signature
from backend.database import SessionLocal
from backend.models import LiveRecord, LiveMessage


class LiveClient:
    """异步直播 WebSocket 客户端"""

    def __init__(
        self,
        room_id: str,
        cookie_str: str = "",
        on_message: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.room_id = room_id
        self.cookie_str = cookie_str
        self.on_message = on_message

        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self._ping_task: Optional[asyncio.Task] = None
        self._recv_task: Optional[asyncio.Task] = None

        # 直播间信息
        self.room_info: Dict[str, Any] = {}
        self.ttwid: str = ""
        self.real_room_id: str = ""
        self.user_unique_id: str = ""

        # 统计信息
        self.stats = {
            "danmu_count": 0,
            "gift_count": 0,
            "like_count": 0,
            "follow_count": 0,
            "member_count": 0,
        }

    async def connect(self) -> bool:
        """连接直播间"""
        try:
            # 获取直播间信息
            from backend.core.builder.auth import DouyinAuth
            auth = DouyinAuth()
            auth.perepare_auth(self.cookie_str, "", "")

            room_info = DouyinAPI.get_live_info(auth, self.room_id)
            if not room_info:
                logger.error(f"获取直播间信息失败: {self.room_id}")
                return False

            # 检查直播状态 (2 = 直播中, 4 = 未开播)
            if room_info.get("room_status") == "4":
                logger.warning(f"直播间未开播: {self.room_id}")
                return False

            self.room_info = room_info
            self.real_room_id = room_info["room_id"]
            self.user_unique_id = room_info["user_id"]
            self.ttwid = room_info["ttwid"]

            # 构建 WebSocket URL
            wss_url = self._build_wss_url()
            if not wss_url:
                return False

            # 连接 WebSocket
            headers = self._build_headers()
            self.ws = await websockets.connect(
                wss_url,
                extra_headers=headers,
                origin="https://live.douyin.com"
            )

            self.running = True
            logger.info(f"已连接直播间: {self.room_id}")

            # 启动心跳和接收任务
            self._ping_task = asyncio.create_task(self._ping_loop())
            self._recv_task = asyncio.create_task(self._recv_loop())

            return True

        except Exception as e:
            logger.error(f"连接直播间失败: {e}")
            return False

    def _build_wss_url(self) -> Optional[str]:
        """构建 WebSocket 连接 URL"""
        try:
            params = Params()
            (params
             .add_param('app_name', 'douyin_web')
             .add_param('version_code', '180800')
             .add_param('webcast_sdk_version', '1.0.14-beta.0')
             .add_param('update_version_code', '1.0.14-beta.0')
             .add_param('compress', 'gzip')
             .add_param('device_platform', 'web')
             .add_param('cookie_enabled', 'true')
             .add_param('screen_width', '1707')
             .add_param('screen_height', '960')
             .add_param('browser_language', 'zh-CN')
             .add_param('browser_platform', 'Win32')
             .add_param('browser_name', 'Mozilla')
             .add_param('browser_version', HeaderBuilder.ua.split('Mozilla/')[-1])
             .add_param('browser_online', 'true')
             .add_param('tz_name', 'Etc/GMT-8')
             .add_param('host', 'https://live.douyin.com')
             .add_param('aid', '6383')
             .add_param('live_id', '1')
             .add_param('did_rule', '3')
             .add_param('endpoint', 'live_pc')
             .add_param('support_wrds', '1')
             .add_param('user_unique_id', str(self.user_unique_id))
             .add_param('im_path', '/webcast/im/fetch/')
             .add_param('identity', 'audience')
             .add_param('need_persist_msg_count', '15')
             .add_param('insert_task_id', '')
             .add_param('live_reason', '')
             .add_param('room_id', self.real_room_id)
             .add_param('heartbeatDuration', '0')
             .add_param('signature', generate_signature(self.real_room_id, self.user_unique_id))
            )
            return f"wss://webcast5-ws-web-lf.douyin.com/webcast/im/push/v2/?{urlencode(params.get())}"
        except Exception as e:
            logger.error(f"构建 WebSocket URL 失败: {e}")
            return None

    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        return {
            'Pragma': 'no-cache',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'User-Agent': HeaderBuilder.ua,
            'Upgrade': 'websocket',
            'Cache-Control': 'no-cache',
            'Connection': 'Upgrade',
            'Cookie': f"ttwid={self.ttwid};",
        }

    async def _ping_loop(self):
        """心跳循环"""
        while self.running:
            try:
                frame = Live_pb2.PushFrame()
                frame.payloadType = "hb"
                await self.ws.send(frame.SerializeToString())
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"心跳发送失败: {e}")
                break

    async def _recv_loop(self):
        """消息接收循环"""
        while self.running:
            try:
                message = await self.ws.recv()
                await self._handle_message(message)
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"WebSocket 连接关闭: {self.room_id}")
                break
            except Exception as e:
                logger.error(f"接收消息失败: {e}")
                await asyncio.sleep(1)

    async def _handle_message(self, message: bytes):
        """处理收到的消息"""
        try:
            frame = Live_pb2.PushFrame()
            frame.ParseFromString(message)

            # 解压 payload
            origin_bytes = gzip.decompress(frame.payload)
            response = Live_pb2.LiveResponse()
            response.ParseFromString(origin_bytes)

            # 发送 ACK
            if response.needAck:
                ack = Live_pb2.PushFrame()
                ack.payloadType = "ack"
                ack.payload = response.internalExt.encode('utf-8')
                ack.logId = frame.logId
                await self.ws.send(ack.SerializeToString())

            # 处理各类消息
            for item in response.messagesList:
                msg_data = await self._parse_message(item)
                if msg_data and self.on_message:
                    await self.on_message(msg_data)

        except Exception as e:
            logger.error(f"消息处理失败: {e}")

    async def _parse_message(self, item) -> Optional[Dict[str, Any]]:
        """解析消息"""
        try:
            msg_data = {
                "room_id": self.room_id,
                "real_room_id": self.real_room_id,
                "msg_type": "",
                "timestamp": datetime.now().isoformat(),
            }

            if item.method == 'WebcastGiftMessage':
                message = Live_pb2.GiftMessage()
                message.ParseFromString(item.payload)

                msg_data["msg_type"] = "gift"
                msg_data["user"] = {
                    "sec_uid": message.user.sec_uid,
                    "nickname": message.user.nickname,
                }
                msg_data["to_user"] = {
                    "sec_uid": message.toUser.sec_uid,
                    "nickname": message.toUser.nickname,
                }
                msg_data["gift"] = {
                    "id": message.giftId,
                    "name": message.gift.name,
                    "count": message.comboCount,
                }
                self.stats["gift_count"] += 1

            elif item.method == "WebcastChatMessage":
                message = Live_pb2.ChatMessage()
                message.ParseFromString(item.payload)

                msg_data["msg_type"] = "chat"
                msg_data["user"] = {
                    "sec_uid": message.user.sec_uid,
                    "nickname": message.user.nickname,
                }
                msg_data["content"] = message.content
                self.stats["danmu_count"] += 1

            elif item.method == "WebcastMemberMessage":
                message = Live_pb2.MemberMessage()
                message.ParseFromString(item.payload)

                msg_data["msg_type"] = "member"
                msg_data["user"] = {
                    "sec_uid": message.user.sec_uid,
                    "nickname": message.user.nickname,
                }
                msg_data["member_count"] = message.memberCount
                self.stats["member_count"] += 1

            elif item.method == "WebcastLikeMessage":
                message = Live_pb2.LikeMessage()
                message.ParseFromString(item.payload)

                msg_data["msg_type"] = "like"
                msg_data["user"] = {
                    "sec_uid": message.user.sec_uid,
                    "nickname": message.user.nickname,
                }
                msg_data["like_count"] = message.count
                msg_data["like_total"] = message.total
                self.stats["like_count"] += message.count

            elif item.method == "WebcastSocialMessage":
                message = Live_pb2.SocialMessage()
                message.ParseFromString(item.payload)

                if message.action == 1:  # 关注
                    msg_data["msg_type"] = "follow"
                    msg_data["user"] = {
                        "sec_uid": message.user.sec_uid,
                        "nickname": message.user.nickname,
                    }
                    self.stats["follow_count"] += 1
                else:
                    return None

            elif item.method == "WebcastRoomStatsMessage":
                message = Live_pb2.RoomStatsMessage()
                message.ParseFromString(item.payload)

                msg_data["msg_type"] = "room_stats"
                msg_data["display"] = message.displayLong
                msg_data["total"] = message.total

            else:
                return None

            return msg_data

        except Exception as e:
            logger.error(f"解析消息失败: {e}")
            return None

    async def disconnect(self):
        """断开连接"""
        self.running = False

        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass

        if self._recv_task:
            self._recv_task.cancel()
            try:
                await self._recv_task
            except asyncio.CancelledError:
                pass

        if self.ws:
            await self.ws.close()
            self.ws = None

        logger.info(f"已断开直播间: {self.room_id}")


class LiveService:
    """直播服务 - 管理多个直播间的监听"""

    def __init__(self, cookie_str: str = ""):
        self.cookie_str = cookie_str
        self._clients: Dict[str, LiveClient] = {}
        self._broadcast_callbacks: list = []
        self._ws_manager = None

    def set_ws_manager(self, manager):
        """设置 WebSocket 管理器"""
        self._ws_manager = manager

    def add_broadcast_callback(self, callback):
        """添加广播回调"""
        self._broadcast_callbacks.append(callback)

    async def start_listen(self, room_id: str) -> Dict[str, Any]:
        """开始监听直播间"""
        if room_id in self._clients:
            return {
                "success": False,
                "message": "该直播间已在监听中",
                "room_id": room_id
            }

        # 创建直播记录
        db = SessionLocal()
        try:
            record = self._create_or_update_record(db, room_id)
        finally:
            db.close()

        # 创建客户端
        client = LiveClient(
            room_id=room_id,
            cookie_str=self.cookie_str,
            on_message=lambda msg: self._on_message(room_id, msg, record.id if record else None)
        )

        # 连接
        if not await client.connect():
            return {
                "success": False,
                "message": "连接直播间失败，请检查房间号或直播状态",
                "room_id": room_id
            }

        self._clients[room_id] = client

        return {
            "success": True,
            "message": "开始监听",
            "room_id": room_id,
            "room_info": client.room_info,
            "stats": client.stats
        }

    async def stop_listen(self, room_id: str) -> Dict[str, Any]:
        """停止监听直播间"""
        if room_id not in self._clients:
            return {
                "success": False,
                "message": "该直播间未在监听",
                "room_id": room_id
            }

        client = self._clients[room_id]

        # 更新直播记录
        db = SessionLocal()
        try:
            record = db.query(LiveRecord).filter(
                LiveRecord.room_id == room_id,
                LiveRecord.status == "online"
            ).first()
            if record:
                record.status = "offline"
                record.ended_at = datetime.now()
                record.viewer_count = client.stats.get("member_count", 0)
                record.like_count = client.stats.get("like_count", 0)
                record.follow_count = client.stats.get("follow_count", 0)
                db.commit()
        finally:
            db.close()

        # 断开连接
        await client.disconnect()
        del self._clients[room_id]

        return {
            "success": True,
            "message": "已停止监听",
            "room_id": room_id,
            "final_stats": client.stats
        }

    async def _on_message(self, room_id: str, msg_data: Dict[str, Any], record_id: int = None):
        """消息回调 - 广播到前端并存储"""
        # 广播到前端 WebSocket
        if self._ws_manager:
            await self._ws_manager.broadcast(room_id, msg_data)

        # 调用其他回调
        for callback in self._broadcast_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(room_id, msg_data)
                else:
                    callback(room_id, msg_data)
            except Exception as e:
                logger.error(f"广播回调执行失败: {e}")

        # 存储消息到数据库
        if record_id:
            await self._save_message(record_id, msg_data)

    def _create_or_update_record(self, db: Session, room_id: str) -> Optional[LiveRecord]:
        """创建或更新直播记录"""
        try:
            # 查找现有在线记录
            record = db.query(LiveRecord).filter(
                LiveRecord.room_id == room_id,
                LiveRecord.status == "online"
            ).first()

            if not record:
                # 创建新记录
                record = LiveRecord(
                    room_id=room_id,
                    status="online",
                    started_at=datetime.now()
                )
                db.add(record)
                db.commit()
                db.refresh(record)

            return record
        except Exception as e:
            logger.error(f"创建直播记录失败: {e}")
            return None

    async def _save_message(self, record_id: int, msg_data: Dict[str, Any]):
        """保存消息到数据库"""
        db = SessionLocal()
        try:
            user = msg_data.get("user", {})
            message = LiveMessage(
                record_id=record_id,
                room_id=msg_data.get("room_id", ""),
                msg_type=msg_data.get("msg_type", ""),
                user_id=user.get("id"),
                user_sec_uid=user.get("sec_uid"),
                user_nickname=user.get("nickname"),
                content=json.dumps(msg_data, ensure_ascii=False),
            )

            # 礼物特有字段
            if msg_data.get("msg_type") == "gift":
                gift = msg_data.get("gift", {})
                to_user = msg_data.get("to_user", {})
                message.gift_id = gift.get("id")
                message.gift_name = gift.get("name")
                message.gift_count = gift.get("count", 0)
                message.to_user_nickname = to_user.get("nickname")

            # 点赞特有字段
            elif msg_data.get("msg_type") == "like":
                message.like_count = msg_data.get("like_count", 0)
                message.like_total = msg_data.get("like_total", 0)

            db.add(message)
            db.commit()
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
        finally:
            db.close()

    def get_status(self, room_id: str = None) -> Dict[str, Any]:
        """获取监听状态"""
        if room_id:
            if room_id in self._clients:
                client = self._clients[room_id]
                return {
                    "listening": True,
                    "room_id": room_id,
                    "stats": client.stats,
                    "room_info": client.room_info
                }
            return {"listening": False, "room_id": room_id}

        # 返回所有监听状态
        return {
            "rooms": [
                {
                    "room_id": rid,
                    "stats": client.stats,
                    "room_info": client.room_info
                }
                for rid, client in self._clients.items()
            ],
            "total": len(self._clients)
        }

    async def stop_all(self):
        """停止所有监听"""
        for room_id in list(self._clients.keys()):
            await self.stop_listen(room_id)


# 全局实例
live_service: Optional[LiveService] = None


def get_live_service() -> LiveService:
    """获取直播服务实例"""
    global live_service
    if live_service is None:
        from backend.config import settings
        live_service = LiveService(cookie_str=settings.cookie_str)
    return live_service
