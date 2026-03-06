"""
直播记录模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
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
    started_at = Column(DateTime, comment="开始时间")
    ended_at = Column(DateTime, comment="结束时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    def __repr__(self):
        return f"<LiveRecord(room_id={self.room_id}, status={self.status})>"
