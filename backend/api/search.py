"""
搜索相关 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Task
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/search", tags=["搜索"])


@router.post("/works", summary="搜索作品")
async def search_works(
    keyword: str,
    max_count: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """搜索并采集作品"""
    from backend.services.collector import get_collector
    import json

    # 创建任务
    task = Task(
        task_type="search",
        task_params=json.dumps({
            "keyword": keyword,
            "max_count": max_count
        }),
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 启动采集
    collector = get_collector()
    collector.start_task(task.id, "search", {
        "keyword": keyword,
        "max_count": max_count
    })

    return ApiResponse(data={"task_id": task.id}, message="搜索任务已创建")


@router.post("/users", summary="搜索用户")
async def search_users(keyword: str, max_count: int = Query(20, ge=1, le=100)) -> ApiResponse[dict]:
    """搜索用户（实时搜索，不保存）"""
    from backend.services.douyin import DouyinService
    from dotenv import load_dotenv
    import os

    load_dotenv()
    cookie = os.getenv("DY_COOKIES", "")

    service = DouyinService(cookie)
    result = service.search_users(keyword, max_count)

    if not result:
        return ApiResponse(code=500, message="搜索失败")

    users = []
    for u in result["users"]:
        users.append({
            "uid": u.get("uid"),
            "sec_uid": u.get("sec_uid"),
            "nickname": u.get("nickname"),
            "avatar": u.get("avatar"),
            "follower_count": u.get("follower_count"),
            "aweme_count": u.get("aweme_count"),
        })

    return ApiResponse(data={"users": users, "total": result["total"]})


@router.post("/live", summary="搜索直播")
async def search_live(keyword: str) -> ApiResponse[dict]:
    """搜索直播"""
    # TODO: 实现直播搜索
    return ApiResponse(data={"rooms": [], "has_more": False})
