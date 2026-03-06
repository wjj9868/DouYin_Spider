"""
作品模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.database import Base


class Work(Base):
    """抖音作品表"""
    __tablename__ = "dy_work"

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(String(64), unique=True, nullable=False, index=True, comment="作品ID")
    work_url = Column(String(256), comment="作品链接")
    user_id = Column(Integer, ForeignKey("dy_user.id"), nullable=True, comment="作者ID")
    title = Column(String(512), comment="标题")
    description = Column(Text, comment="描述")
    work_type = Column(String(32), comment="类型: video/image")
    video_url = Column(String(1024), comment="视频地址")
    cover_url = Column(String(512), comment="封面地址")
    images = Column(JSON, comment="图片列表")
    digg_count = Column(Integer, default=0, comment="点赞数")
    comment_count = Column(Integer, default=0, comment="评论数")
    collect_count = Column(Integer, default=0, comment="收藏数")
    share_count = Column(Integer, default=0, comment="分享数")
    admire_count = Column(Integer, default=0, comment="赞赏数")
    topics = Column(JSON, comment="话题列表")
    create_time = Column(DateTime, comment="作品发布时间")
    crawled_at = Column(DateTime, default=datetime.now, comment="采集时间")

    # 关联用户
    user = relationship("User", back_populates="works")
    # 关联评论
    comments = relationship("Comment", back_populates="work")

    def __repr__(self):
        return f"<Work(work_id={self.work_id}, title={self.title})>"
