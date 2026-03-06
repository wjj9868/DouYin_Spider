"""
评论相关 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CommentBase(BaseModel):
    comment_id: str
    work_id: Optional[int] = None
    parent_id: Optional[int] = None
    user_id: Optional[int] = None
    content: Optional[str] = None
    digg_count: int = 0
    create_time: Optional[datetime] = None


class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: int
    crawled_at: datetime
    # 用户信息
    user_nickname: Optional[str] = None
    user_avatar: Optional[str] = None

    class Config:
        from_attributes = True
