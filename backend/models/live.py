"""
直播记录模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base


class LiveRecord(Base):
    """直播记录表"""
    __tablename__ = "dy_live_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(String(64), nullable=False, index=True, comment="直播间ID")
    user_id = Column(Integer, ForeignKey("dy_user.id"), comment="主播用户ID")
    status = Column(String(32), default="online", comment="状态: online/offline")
    viewer_count = Column(Integer, default=0, comment="观众数")
    like_count = Column(Integer, default=0, comment="点赞总数")
    follow_count = Column(Integer, default=0, comment="关注数")
    room_title = Column(String(256), comment="直播间标题")
    started_at = Column(DateTime, comment="开始时间")
    ended_at = Column(DateTime, comment="结束时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关联消息
    messages = relationship("LiveMessage", back_populates="record", lazy="dynamic")

    def __repr__(self):
        return f"<LiveRecord(room_id={self.room_id}, status={self.status})>"


class LiveMessage(Base):
    """直播消息表 - 存储弹幕、礼物、点赞等消息"""
    __tablename__ = "dy_live_message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey("dy_live_record.id"), comment="直播记录ID")
    room_id = Column(String(64), nullable=False, index=True, comment="直播间ID")

    # 消息类型: chat(弹幕), gift(礼物), like(点赞), member(进入), follow(关注), room_stats(房间统计)
    msg_type = Column(String(32), nullable=False, index=True, comment="消息类型")

    # 用户信息
    user_id = Column(String(64), comment="用户ID")
    user_sec_uid = Column(String(256), comment="用户sec_uid")
    user_nickname = Column(String(128), comment="用户昵称")

    # 消息内容
    content = Column(Text, comment="消息内容(JSON格式)")

    # 礼物特有字段
    gift_id = Column(String(64), comment="礼物ID")
    gift_name = Column(String(128), comment="礼物名称")
    gift_count = Column(Integer, default=0, comment="礼物数量")
    to_user_nickname = Column(String(128), comment="接收者昵称(送礼目标)")

    # 点赞特有字段
    like_count = Column(Integer, default=0, comment="点赞数")
    like_total = Column(Integer, default=0, comment="总点赞数")

    created_at = Column(DateTime, default=datetime.now, index=True, comment="创建时间")

    # 关联直播记录
    record = relationship("LiveRecord", back_populates="messages")

    def __repr__(self):
        return f"<LiveMessage(room_id={self.room_id}, type={self.msg_type})>"
