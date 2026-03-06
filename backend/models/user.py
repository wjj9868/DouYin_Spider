"""
用户模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from backend.database import Base


class User(Base):
    """抖音用户表"""
    __tablename__ = "dy_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(64), unique=True, nullable=False, index=True, comment="抖音用户ID")
    sec_uid = Column(String(128), comment="安全ID")
    unique_id = Column(String(64), comment="抖音号")
    nickname = Column(String(128), comment="昵称")
    avatar = Column(String(512), comment="头像URL")
    signature = Column(Text, comment="个人简介")
    gender = Column(Integer, default=0, comment="性别: 0未知, 1男, 2女")
    age = Column(Integer, comment="年龄")
    follower_count = Column(Integer, default=0, comment="粉丝数")
    following_count = Column(Integer, default=0, comment="关注数")
    aweme_count = Column(Integer, default=0, comment="作品数")
    favorited_count = Column(Integer, default=0, comment="获赞数")
    total_favorited = Column(Integer, default=0, comment="作品被赞和收藏数量")
    ip_location = Column(String(64), comment="IP归属地")
    user_url = Column(String(256), comment="用户主页URL")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    works = relationship("Work", back_populates="user")
    comments = relationship("Comment", back_populates="user")

    def __repr__(self):
        return f"<User(uid={self.uid}, nickname={self.nickname})>"
