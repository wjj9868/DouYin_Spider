"""
用户相关 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserBase(BaseModel):
    uid: str
    sec_uid: Optional[str] = None
    unique_id: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    signature: Optional[str] = None
    gender: int = 0
    age: Optional[int] = None
    follower_count: int = 0
    following_count: int = 0
    aweme_count: int = 0
    favorited_count: int = 0
    total_favorited: int = 0
    ip_location: Optional[str] = None
    user_url: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
