"""
定时任务 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from croniter import croniter

from backend.database import get_db
from backend.models import ScheduledTask
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/scheduled-tasks", tags=["定时任务"])


class ScheduledTaskCreate(BaseModel):
    name: str
    task_type: str
    task_params: str
    cron_expression: str


class ScheduledTaskUpdate(BaseModel):
    name: Optional[str] = None
    task_params: Optional[str] = None
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduledTaskResponse(BaseModel):
    id: int
    name: str
    task_type: str
    task_params: str
    cron_expression: str
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", summary="获取定时任务列表")
async def get_scheduled_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """获取定时任务列表"""
    query = db.query(ScheduledTask)
    if is_active is not None:
        query = query.filter(ScheduledTask.is_active == is_active)

    total = query.count()
    offset = (page - 1) * page_size
    tasks = query.order_by(ScheduledTask.created_at.desc()).offset(offset).limit(page_size).all()

    items = [ScheduledTaskResponse.model_validate(t) for t in tasks]
    return ApiResponse(data={"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("", summary="创建定时任务")
async def create_scheduled_task(
    data: ScheduledTaskCreate,
    db: Session = Depends(get_db)
) -> ApiResponse[ScheduledTaskResponse]:
    """创建定时任务"""
    try:
        croniter(data.cron_expression)
    except Exception:
        return ApiResponse(code=400, message="无效的Cron表达式")

    cron = croniter(data.cron_expression, datetime.now())
    next_run_at = cron.get_next(datetime.now())

    task = ScheduledTask(
        name=data.name,
        task_type=data.task_type,
        task_params=data.task_params,
        cron_expression=data.cron_expression,
        next_run_at=next_run_at
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return ApiResponse(data=ScheduledTaskResponse.model_validate(task), message="创建成功")


@router.get("/{task_id}", summary="获取定时任务详情")
async def get_scheduled_task(
    task_id: int,
    db: Session = Depends(get_db)
) -> ApiResponse[ScheduledTaskResponse]:
    """获取定时任务详情"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        return ApiResponse(code=404, message="任务不存在")
    return ApiResponse(data=ScheduledTaskResponse.model_validate(task))


@router.put("/{task_id}", summary="更新定时任务")
async def update_scheduled_task(
    task_id: int,
    data: ScheduledTaskUpdate,
    db: Session = Depends(get_db)
) -> ApiResponse[ScheduledTaskResponse]:
    """更新定时任务"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        return ApiResponse(code=404, message="任务不存在")

    update_data = data.model_dump(exclude_unset=True)
    if "cron_expression" in update_data:
        try:
            croniter(update_data["cron_expression"])
            cron = croniter(update_data["cron_expression"], datetime.now())
            update_data["next_run_at"] = cron.get_next(datetime.now())
        except Exception:
            return ApiResponse(code=400, message="无效的Cron表达式")

    for key, value in update_data.items():
        if value is not None:
            setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return ApiResponse(data=ScheduledTaskResponse.model_validate(task), message="更新成功")


@router.delete("/{task_id}", summary="删除定时任务")
async def delete_scheduled_task(
    task_id: int,
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """删除定时任务"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        return ApiResponse(code=404, message="任务不存在")

    db.delete(task)
    db.commit()
    return ApiResponse(message="删除成功")


@router.post("/{task_id}/toggle", summary="启用/禁用定时任务")
async def toggle_scheduled_task(
    task_id: int,
    db: Session = Depends(get_db)
) -> ApiResponse[ScheduledTaskResponse]:
    """启用/禁用定时任务"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        return ApiResponse(code=404, message="任务不存在")

    task.is_active = not task.is_active
    if task.is_active:
        cron = croniter(task.cron_expression, datetime.now())
        task.next_run_at = cron.get_next(datetime.now())

    db.commit()
    db.refresh(task)
    return ApiResponse(
        data=ScheduledTaskResponse.model_validate(task),
        message=f"已{'启用' if task.is_active else '禁用'}"
    )


@router.post("/{task_id}/run-now", summary="立即执行定时任务")
async def run_scheduled_task_now(
    task_id: int,
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """立即执行定时任务"""
    from backend.models import Task
    from backend.services.collector import get_collector
    import json

    scheduled_task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not scheduled_task:
        return ApiResponse(code=404, message="任务不存在")

    task = Task(
        task_type=scheduled_task.task_type,
        task_params=scheduled_task.task_params,
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    params = json.loads(scheduled_task.task_params)
    collector = get_collector()
    collector.start_task(task.id, scheduled_task.task_type, params)

    scheduled_task.last_run_at = datetime.now()
    db.commit()

    return ApiResponse(data={"task_id": task.id}, message="任务已开始执行")
