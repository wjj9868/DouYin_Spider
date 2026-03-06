"""
作品相关 Schema
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel


class WorkBase(BaseModel):
    work_id: str
    work_url: Optional[str] = None
    user_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    work_type: Optional[str] = None
    video_url: Optional[str] = None
    cover_url: Optional[str] = None
    images: Optional[List[str]] = None
    digg_count: int = 0
    comment_count: int = 0
    collect_count: int = 0
    share_count: int = 0
    admire_count: int = 0
    topics: Optional[List[str]] = None
    create_time: Optional[datetime] = None


class WorkCreate(WorkBase):
    pass


class WorkResponse(WorkBase):
    id: int
    crawled_at: datetime
    author_nickname: Optional[str] = None
    author_avatar: Optional[str] = None
    user_url: Optional[str] = None

    class Config:
        from_attributes = True


class WorkListResponse(BaseModel):
    items: list[WorkResponse]
    total: int
    page: int
    page_size: int
