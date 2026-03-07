"""
搜索相关 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db
from backend.models import Task
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/search", tags=["搜索"])


class SearchWorksParams(BaseModel):
    keyword: str
    max_count: int = 50
    sort_type: str = "0"
    publish_time: str = "0"
    filter_duration: str = ""
    search_range: str = "0"
    content_type: str = "0"


class SearchUsersParams(BaseModel):
    keyword: str
    max_count: int = 20
    douyin_user_fans: str = ""
    douyin_user_type: str = ""


@router.post("/works", summary="搜索作品")
async def search_works(
    params: SearchWorksParams,
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """搜索并采集作品

    筛选条件说明:
    - sort_type: 排序方式 - 0综合排序, 1最多点赞, 2最新发布
    - publish_time: 发布时间 - 0不限, 1一天内, 7一周内, 180半年内
    - filter_duration: 视频时长 - 空不限, 0-1一分钟内, 1-5 1-5分钟, 5-10000 5分钟以上
    - search_range: 搜索范围 - 0不限, 1最近看过, 2还未看过, 3关注的人
    - content_type: 内容形式 - 0不限, 1视频, 2图文
    """
    from backend.services.collector import get_collector
    import json

    task = Task(
        task_type="search",
        task_params=json.dumps(params.model_dump()),
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    collector = get_collector()
    collector.start_task(task.id, "search", params.model_dump())

    return ApiResponse(data={"task_id": task.id}, message="搜索任务已创建")


@router.post("/users", summary="搜索用户")
async def search_users(params: SearchUsersParams) -> ApiResponse[dict]:
    """搜索用户（实时搜索，不保存）

    筛选条件说明:
    - douyin_user_fans: 粉丝数量 - 空不限, 0_1k(1k以下), 1k_1w(1k-1w), 1w_10w(1w-10w), 10w_100w(10w-100w), 100w_(100w以上)
    - douyin_user_type: 用户类型 - 空不限, common_user(普通用户), enterprise_user(企业用户), personal_user(个人认证用户)
    """
    from backend.services.douyin import DouyinService
    from backend.config import settings

    service = DouyinService(settings.cookie_str)
    result = service.search_users(
        params.keyword,
        params.max_count,
        params.douyin_user_fans,
        params.douyin_user_type
    )

    if not result:
        return ApiResponse(code=500, message="搜索失败")

    users = []
    for u in result["users"]:
        users.append({
            "uid": u.get("uid"),
            "sec_uid": u.get("sec_uid"),
            "nickname": u.get("nickname"),
            "avatar": u.get("avatar"),
            "signature": u.get("signature"),
            "follower_count": u.get("follower_count"),
            "aweme_count": u.get("aweme_count"),
            "ip_location": u.get("ip_location"),
        })

    return ApiResponse(data={"users": users, "total": result["total"]})


@router.post("/live", summary="搜索直播")
async def search_live(keyword: str) -> ApiResponse[dict]:
    """搜索直播"""
    return ApiResponse(data={"rooms": [], "has_more": False})
