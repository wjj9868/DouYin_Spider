"""
用户相关 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body, Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from backend.database import get_db
from backend.models import User, Work
from backend.schemas.user import UserResponse, UserListResponse
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/users", tags=["用户"])


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    signature: Optional[str] = None
    gender: Optional[int] = None
    age: Optional[int] = None


class UserSearchResult(BaseModel):
    uid: str
    sec_uid: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    signature: Optional[str] = None
    follower_count: int = 0
    aweme_count: int = 0
    is_collected: bool = False


class UserStats(BaseModel):
    total: int = 0
    male: int = 0
    female: int = 0
    total_followers: int = 0
    total_works: int = 0


@router.get("/stats", summary="获取用户统计")
async def get_user_stats(db: Session = Depends(get_db)) -> ApiResponse[UserStats]:
    """获取用户统计数据"""
    total = db.query(func.count(User.id)).scalar() or 0
    male = db.query(func.count(User.id)).filter(User.gender == 1).scalar() or 0
    female = db.query(func.count(User.id)).filter(User.gender == 2).scalar() or 0
    total_followers = db.query(func.sum(User.follower_count)).scalar() or 0
    total_works = db.query(func.sum(User.aweme_count)).scalar() or 0

    return ApiResponse(data=UserStats(
        total=total,
        male=male,
        female=female,
        total_followers=total_followers,
        total_works=total_works,
    ))


@router.get("", summary="获取用户列表")
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    gender: Optional[int] = None,
    min_followers: Optional[int] = None,
    max_followers: Optional[int] = None,
    db: Session = Depends(get_db)
) -> ApiResponse[UserListResponse]:
    """获取用户列表（分页、筛选）"""
    query = db.query(User)

    if keyword:
        query = query.filter(
            User.nickname.contains(keyword) | User.uid.contains(keyword) | User.unique_id.contains(keyword)
        )
    if gender is not None:
        query = query.filter(User.gender == gender)
    if min_followers is not None:
        query = query.filter(User.follower_count >= min_followers)
    if max_followers is not None:
        query = query.filter(User.follower_count <= max_followers)

    total = query.count()
    offset = (page - 1) * page_size

    users = query.order_by(User.updated_at.desc()).offset(offset).limit(page_size).all()

    items = [UserResponse.model_validate(u) for u in users]

    return ApiResponse(data=UserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ))


@router.get("/{uid}", summary="获取用户详情")
async def get_user(uid: str, db: Session = Depends(get_db)) -> ApiResponse[UserResponse]:
    """获取用户详情"""
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        return ApiResponse(code=404, message="用户不存在")

    return ApiResponse(data=UserResponse.model_validate(user))


@router.put("/{uid}", summary="更新用户信息")
async def update_user(
    uid: str,
    data: UserUpdate,
    db: Session = Depends(get_db)
) -> ApiResponse[UserResponse]:
    """更新用户信息"""
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        return ApiResponse(code=404, message="用户不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return ApiResponse(data=UserResponse.model_validate(user), message="更新成功")


@router.delete("/{uid}", summary="删除用户")
async def delete_user(uid: str, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """删除用户及其作品"""
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        return ApiResponse(code=404, message="用户不存在")

    db.query(Work).filter(Work.user_id == user.id).delete()
    db.delete(user)
    db.commit()
    return ApiResponse(message="删除成功")


@router.delete("/batch", summary="批量删除用户")
async def batch_delete_users(
    uids: list[str] = Body(..., embed=True),
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """批量删除用户"""
    users = db.query(User).filter(User.uid.in_(uids)).all()
    user_ids = [u.id for u in users]
    db.query(Work).filter(Work.user_id.in_(user_ids)).delete(synchronize_session=False)
    deleted = len(users)
    for user in users:
        db.delete(user)
    db.commit()
    return ApiResponse(data={"deleted": deleted}, message=f"成功删除 {deleted} 个用户")


@router.get("/{uid}/works", summary="获取用户作品")
async def get_user_works(
    uid: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """获取用户作品列表"""
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        return ApiResponse(code=404, message="用户不存在")

    query = db.query(Work).filter(Work.user_id == user.id)
    total = query.count()
    offset = (page - 1) * page_size

    works = query.order_by(Work.create_time.desc()).offset(offset).limit(page_size).all()

    items = []
    for w in works:
        items.append({
            "id": w.id,
            "work_id": w.work_id,
            "title": w.title,
            "work_type": w.work_type,
            "cover_url": w.cover_url,
            "digg_count": w.digg_count,
            "comment_count": w.comment_count,
            "collect_count": w.collect_count,
            "create_time": w.create_time.isoformat() if w.create_time else None,
        })

    return ApiResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/{uid}/collect", summary="采集用户信息")
async def collect_user(uid: str, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """采集用户信息"""
    from backend.models import Task
    from backend.services.collector import get_collector
    import json

    # 创建任务
    task = Task(
        task_type="user",
        task_params=json.dumps({"uid": uid}),
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 这里暂时只采集用户基本信息，如需采集用户作品需要 sec_uid
    return ApiResponse(data={"task_id": task.id}, message="用户采集任务已创建")


@router.post("/{uid}/collect-works", summary="采集用户作品")
async def collect_user_works(
    uid: str,
    sec_uid: str,
    max_count: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """采集用户所有作品"""
    from backend.models import Task
    from backend.services.collector import get_collector
    import json

    # 创建任务
    task = Task(
        task_type="user_works",
        task_params=json.dumps({
            "uid": uid,
            "sec_uid": sec_uid,
            "max_count": max_count
        }),
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 启动采集
    collector = get_collector()
    collector.start_task(task.id, "user_works", {
        "sec_uid": sec_uid,
        "max_count": max_count
    })

    return ApiResponse(data={"task_id": task.id}, message="用户作品采集任务已创建")


@router.post("/collect-by-url", summary="通过主页URL采集用户")
async def collect_user_by_url(
    user_url: str = Body(..., embed=True),
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """通过用户主页URL采集用户信息"""
    from backend.models import Task
    from backend.services.collector import get_collector
    import json

    sec_uid = user_url.split("/")[-1].split("?")[0]
    if not sec_uid:
        return ApiResponse(code=400, message="无效的用户主页URL")

    existing = db.query(User).filter(User.sec_uid == sec_uid).first()
    if existing:
        return ApiResponse(data={"user_id": existing.id, "sec_uid": sec_uid}, message="用户已存在")

    task = Task(
        task_type="user_by_url",
        task_params=json.dumps({
            "sec_uid": sec_uid,
            "user_url": user_url
        }),
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    collector = get_collector()
    collector.start_task(task.id, "user_by_url", {
        "sec_uid": sec_uid,
        "user_url": user_url
    })

    return ApiResponse(data={"task_id": task.id, "sec_uid": sec_uid}, message="用户采集任务已创建")


@router.post("/search-douyin", summary="搜索抖音用户")
async def search_douyin_users(
    keyword: str = Body(..., embed=True),
    num: int = Body(20, embed=True),
    db: Session = Depends(get_db)
) -> ApiResponse[list[UserSearchResult]]:
    """搜索抖音用户"""
    from backend.services.douyin import DouyinService
    from backend.config import settings

    try:
        service = DouyinService(settings.cookie_str)
        result = service.search_users(keyword, num)
        if not result:
            return ApiResponse(data=[], message="未找到用户")

        users = []
        for u in result.get("users", []):
            existing = db.query(User).filter(User.uid == u.get("uid")).first()
            users.append(UserSearchResult(
                uid=u.get("uid", ""),
                sec_uid=u.get("sec_uid", ""),
                nickname=u.get("nickname", ""),
                avatar=u.get("avatar", ""),
                signature=u.get("signature", ""),
                follower_count=u.get("follower_count", 0),
                aweme_count=u.get("aweme_count", 0),
                is_collected=existing is not None
            ))

        return ApiResponse(data=users)
    except Exception as e:
        return ApiResponse(code=500, message=f"搜索失败: {str(e)}")


@router.post("/collect-by-sec-uid", summary="通过sec_uid采集用户")
async def collect_user_by_sec_uid(
    sec_uid: str = Body(..., embed=True),
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """通过sec_uid采集用户信息"""
    from backend.models import Task
    from backend.services.collector import get_collector
    import json

    existing = db.query(User).filter(User.sec_uid == sec_uid).first()
    if existing:
        return ApiResponse(data={"user_id": existing.id, "sec_uid": sec_uid}, message="用户已存在")

    task = Task(
        task_type="user_by_url",
        task_params=json.dumps({"sec_uid": sec_uid}),
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    collector = get_collector()
    collector.start_task(task.id, "user_by_url", {"sec_uid": sec_uid})

    return ApiResponse(data={"task_id": task.id, "sec_uid": sec_uid}, message="用户采集任务已创建")
