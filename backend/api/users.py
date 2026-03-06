"""
用户相关 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Work
from backend.schemas.user import UserResponse, UserListResponse
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("", summary="获取用户列表")
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
) -> ApiResponse[UserListResponse]:
    """获取用户列表（分页）"""
    query = db.query(User)

    if keyword:
        query = query.filter(
            User.nickname.contains(keyword) | User.uid.contains(keyword)
        )

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
