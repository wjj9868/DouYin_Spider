"""
评论模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Comment(Base):
    """抖音评论表"""
    __tablename__ = "dy_comment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(String(64), unique=True, nullable=False, index=True, comment="评论ID")
    work_id = Column(Integer, ForeignKey("dy_work.id"), comment="作品ID")
    parent_id = Column(Integer, ForeignKey("dy_comment.id"), nullable=True, comment="父评论ID")
    user_id = Column(Integer, ForeignKey("dy_user.id"), nullable=True, comment="评论用户ID")
    content = Column(Text, comment="评论内容")
    digg_count = Column(Integer, default=0, comment="点赞数")
    create_time = Column(DateTime, comment="评论时间")
    crawled_at = Column(DateTime, default=datetime.now, comment="采集时间")

    # 关联作品
    work = relationship("Work", back_populates="comments")
    # 关联用户
    user = relationship("User", back_populates="comments")
    # 自关联 - 指向父评论，remote_side 使用主键 id 表示"远端是id"
    parent = relationship("Comment", remote_side=[id], foreign_keys=[parent_id], backref="replies")

    def __repr__(self):
        return f"<Comment(comment_id={self.comment_id})>"
