"""
任务管理 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Body
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


@router.get("/stats", summary="任务统计")
async def get_task_stats(db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """获取任务统计数据"""
    total = db.query(Task).count()
    pending = db.query(Task).filter(Task.status == "pending").count()
    running = db.query(Task).filter(Task.status == "running").count()
    completed = db.query(Task).filter(Task.status == "completed").count()
    failed = db.query(Task).filter(Task.status == "failed").count()

    return ApiResponse(data={
        "total": total,
        "pending": pending,
        "running": running,
        "completed": completed,
        "failed": failed
    })


@router.post("", summary="创建任务")
async def create_task(task: TaskCreate, db: Session = Depends(get_db)) -> ApiResponse[TaskResponse]:
    """创建新任务"""
    import json
    from backend.services.collector import get_collector

    new_task = Task(
        task_type=task.task_type,
        task_params=json.dumps(task.task_params),
        status="pending"
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    collector = get_collector()

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


@router.delete("/batch", summary="批量删除任务")
async def batch_delete_tasks(ids: list[int] = Body(..., embed=True), db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """批量删除任务"""
    from backend.services.collector import get_collector

    tasks = db.query(Task).filter(Task.id.in_(ids)).all()
    
    collector = get_collector()
    for task in tasks:
        if task.status == "running":
            collector.cancel_task(task.id)
    
    db.query(Task).filter(Task.id.in_(ids)).delete(synchronize_session=False)
    db.commit()

    return ApiResponse(message=f"已删除 {len(tasks)} 个任务")


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

    if task.status not in ["running", "pending"]:
        return ApiResponse(code=400, message="任务不在运行或等待中")

    collector = get_collector()
    collector.cancel_task(task_id)
    
    task.status = "cancelled"
    db.commit()

    return ApiResponse(message="任务已取消")


@router.post("/{task_id}/retry", summary="重试任务")
async def retry_task(task_id: int, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """重试失败的任务"""
    import json
    from backend.services.collector import get_collector

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return ApiResponse(code=404, message="任务不存在")

    if task.status != "failed":
        return ApiResponse(code=400, message="只能重试失败的任务")

    task.status = "pending"
    task.progress = 0
    task.result_count = 0
    task.error_message = None
    db.commit()

    collector = get_collector()
    task_type_map = {
        "work": "work",
        "user_works": "user_works",
        "search": "search",
        "comment": "comment",
    }
    
    task_params = json.loads(task.task_params) if isinstance(task.task_params, str) else task.task_params
    collector.start_task(
        task.id,
        task_type_map.get(task.task_type, task.task_type),
        task_params
    )

    return ApiResponse(message="任务已重新开始执行")
