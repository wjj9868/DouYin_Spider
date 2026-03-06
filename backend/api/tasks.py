"""
任务管理 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Task
from backend.schemas.task import TaskResponse, TaskCreate, TaskListResponse
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/tasks", tags=["任务"])


@router.get("", summary="获取任务列表")
async def get_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    db: Session = Depends(get_db)
) -> ApiResponse[TaskListResponse]:
    """获取任务列表"""
    query = db.query(Task)

    if status:
        query = query.filter(Task.status == status)
    if task_type:
        query = query.filter(Task.task_type == task_type)

    total = query.count()
    offset = (page - 1) * page_size

    tasks = query.order_by(Task.created_at.desc()).offset(offset).limit(page_size).all()

    items = [TaskResponse.model_validate(t) for t in tasks]

    return ApiResponse(data=TaskListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ))


@router.post("", summary="创建任务")
async def create_task(task: TaskCreate, db: Session = Depends(get_db)) -> ApiResponse[TaskResponse]:
    """创建新任务"""
    import json
    from backend.services.collector import get_collector

    # 创建任务记录
    new_task = Task(
        task_type=task.task_type,
        task_params=json.dumps(task.task_params),
        status="pending"
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # 启动任务
    collector = get_collector()

    # 根据任务类型调用不同的采集方法
    task_type_map = {
        "work": "work",
        "user_works": "user_works",
        "search": "search",
        "comment": "comment",
    }

    collector.start_task(
        new_task.id,
        task_type_map.get(task.task_type, task.task_type),
        task.task_params
    )

    return ApiResponse(data=TaskResponse.model_validate(new_task), message="任务已创建")


@router.get("/{task_id}", summary="获取任务详情")
async def get_task(task_id: int, db: Session = Depends(get_db)) -> ApiResponse[TaskResponse]:
    """获取任务详情"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return ApiResponse(code=404, message="任务不存在")

    return ApiResponse(data=TaskResponse.model_validate(task))


@router.delete("/{task_id}", summary="删除任务")
async def delete_task(task_id: int, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """删除/取消任务"""
    from backend.services.collector import get_collector

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return ApiResponse(code=404, message="任务不存在")

    # 如果任务正在运行，先取消
    if task.status == "running":
        collector = get_collector()
        collector.cancel_task(task_id)

    db.delete(task)
    db.commit()

    return ApiResponse(message="任务已删除")


@router.post("/{task_id}/cancel", summary="取消任务")
async def cancel_task(task_id: int, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """取消正在运行的任务"""
    from backend.services.collector import get_collector

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return ApiResponse(code=404, message="任务不存在")

    if task.status != "running":
        return ApiResponse(code=400, message="任务不在运行中")

    collector = get_collector()
    collector.cancel_task(task_id)

    return ApiResponse(message="任务已取消")
