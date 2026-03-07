"""
作品相关 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
import requests

from backend.database import get_db
from backend.models import Work, User
from backend.schemas.work import WorkResponse, WorkListResponse
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/works", tags=["作品"])


class WorkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    topics: Optional[list[str]] = None


class WorkStats(BaseModel):
    videos: int = 0
    images: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_collects: int = 0
    total_shares: int = 0


@router.get("/stats", summary="获取作品统计")
async def get_work_stats(db: Session = Depends(get_db)) -> ApiResponse[WorkStats]:
    """获取作品统计数据"""
    video_count = db.query(func.count(Work.id)).filter(Work.work_type == 'video').scalar() or 0
    image_count = db.query(func.count(Work.id)).filter(Work.work_type == 'image').scalar() or 0
    total_likes = db.query(func.sum(Work.digg_count)).scalar() or 0
    total_comments = db.query(func.sum(Work.comment_count)).scalar() or 0
    total_collects = db.query(func.sum(Work.collect_count)).scalar() or 0
    total_shares = db.query(func.sum(Work.share_count)).scalar() or 0

    return ApiResponse(data=WorkStats(
        videos=video_count,
        images=image_count,
        total_likes=total_likes,
        total_comments=total_comments,
        total_collects=total_collects,
        total_shares=total_shares,
    ))


@router.get("", summary="获取作品列表")
async def get_works(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    work_type: Optional[str] = None,
    keyword: Optional[str] = None,
    author_uid: Optional[str] = None,
    min_digg: Optional[int] = None,
    max_digg: Optional[int] = None,
    db: Session = Depends(get_db)
) -> ApiResponse[WorkListResponse]:
    """获取作品列表（分页、筛选）"""
    query = db.query(Work).join(User, isouter=True)

    if work_type:
        query = query.filter(Work.work_type == work_type)
    if keyword:
        query = query.filter(Work.title.contains(keyword))
    if author_uid:
        query = query.filter(User.uid == author_uid)
    if min_digg is not None:
        query = query.filter(Work.digg_count >= min_digg)
    if max_digg is not None:
        query = query.filter(Work.digg_count <= max_digg)

    total = query.count()
    offset = (page - 1) * page_size

    works = query.order_by(Work.crawled_at.desc()).offset(offset).limit(page_size).all()

    items = []
    for w in works:
        items.append(WorkResponse(
            id=w.id,
            work_id=w.work_id,
            work_url=w.work_url,
            user_id=w.user_id,
            title=w.title,
            description=w.description,
            work_type=w.work_type,
            video_url=w.video_url,
            cover_url=w.cover_url,
            images=w.images,
            digg_count=w.digg_count,
            comment_count=w.comment_count,
            collect_count=w.collect_count,
            share_count=w.share_count,
            admire_count=w.admire_count,
            topics=w.topics,
            create_time=w.create_time,
            crawled_at=w.crawled_at,
            author_nickname=w.user.nickname if w.user else None,
            author_avatar=w.user.avatar if w.user else None,
            user_url=w.user.user_url if w.user else None,
        ))

    return ApiResponse(data=WorkListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ))


@router.get("/{work_id}", summary="获取作品详情")
async def get_work(work_id: str, db: Session = Depends(get_db)) -> ApiResponse[WorkResponse]:
    """获取单个作品详情"""
    work = db.query(Work).filter(Work.work_id == work_id).first()
    if not work:
        return ApiResponse(code=404, message="作品不存在")

    return ApiResponse(data=WorkResponse(
        id=work.id,
        work_id=work.work_id,
        work_url=work.work_url,
        user_id=work.user_id,
        title=work.title,
        description=work.description,
        work_type=work.work_type,
        video_url=work.video_url,
        cover_url=work.cover_url,
        images=work.images,
        digg_count=work.digg_count,
        comment_count=work.comment_count,
        collect_count=work.collect_count,
        share_count=work.share_count,
        admire_count=work.admire_count,
        topics=work.topics,
        create_time=work.create_time,
        crawled_at=work.crawled_at,
        author_nickname=work.user.nickname if work.user else None,
        author_avatar=work.user.avatar if work.user else None,
        user_url=work.user.user_url if work.user else None,
    ))


@router.put("/{work_id}", summary="更新作品信息")
async def update_work(
    work_id: str,
    data: WorkUpdate,
    db: Session = Depends(get_db)
) -> ApiResponse[WorkResponse]:
    """更新作品信息"""
    work = db.query(Work).filter(Work.work_id == work_id).first()
    if not work:
        return ApiResponse(code=404, message="作品不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(work, key, value)

    db.commit()
    db.refresh(work)
    return ApiResponse(data=WorkResponse(
        id=work.id,
        work_id=work.work_id,
        work_url=work.work_url,
        user_id=work.user_id,
        title=work.title,
        description=work.description,
        work_type=work.work_type,
        video_url=work.video_url,
        cover_url=work.cover_url,
        images=work.images,
        digg_count=work.digg_count,
        comment_count=work.comment_count,
        collect_count=work.collect_count,
        share_count=work.share_count,
        admire_count=work.admire_count,
        topics=work.topics,
        create_time=work.create_time,
        crawled_at=work.crawled_at,
        author_nickname=work.user.nickname if work.user else None,
        author_avatar=work.user.avatar if work.user else None,
        user_url=work.user.user_url if work.user else None,
    ), message="更新成功")


@router.delete("/{work_id}", summary="删除作品")
async def delete_work(work_id: str, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """删除作品"""
    from backend.models import Comment
    work = db.query(Work).filter(Work.work_id == work_id).first()
    if not work:
        return ApiResponse(code=404, message="作品不存在")

    db.query(Comment).filter(Comment.work_id == work.id).delete()
    db.delete(work)
    db.commit()
    return ApiResponse(message="删除成功")


@router.delete("/batch", summary="批量删除作品")
async def batch_delete_works(
    work_ids: list[str] = Body(..., embed=True),
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """批量删除作品"""
    from backend.models import Comment
    works = db.query(Work).filter(Work.work_id.in_(work_ids)).all()
    work_db_ids = [w.id for w in works]
    db.query(Comment).filter(Comment.work_id.in_(work_db_ids)).delete(synchronize_session=False)
    deleted = len(works)
    for work in works:
        db.delete(work)
    db.commit()
    return ApiResponse(data={"deleted": deleted}, message=f"成功删除 {deleted} 个作品")


@router.post("/collect", summary="采集作品")
async def collect_work(work_id: str, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """创建采集任务采集单个作品"""
    from backend.models import Task
    from backend.services.collector import get_collector
    import json

    # 检查是否已存在
    existing = db.query(Work).filter(Work.work_id == work_id).first()
    if existing:
        return ApiResponse(code=400, message="作品已存在，无需重复采集")

    # 创建任务
    task = Task(
        task_type="work",
        task_params=json.dumps({"work_id": work_id}),
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 启动采集
    collector = get_collector()
    collector.start_task(task.id, "work", {"work_id": work_id})

    return ApiResponse(data={"task_id": task.id}, message="采集任务已创建")


@router.get("/{work_id}/comments", summary="获取作品评论")
async def get_work_comments(
    work_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> ApiResponse[dict]:
    """获取作品评论列表"""
    from backend.models import Comment

    work = db.query(Work).filter(Work.work_id == work_id).first()
    if not work:
        return ApiResponse(code=404, message="作品不存在")

    query = db.query(Comment).filter(Comment.work_id == work.id, Comment.parent_id == None)
    total = query.count()
    offset = (page - 1) * page_size

    comments = query.order_by(Comment.crawled_at.desc()).offset(offset).limit(page_size).all()

    items = []
    for c in comments:
        items.append({
            "id": c.id,
            "comment_id": c.comment_id,
            "content": c.content,
            "digg_count": c.digg_count,
            "create_time": c.create_time.isoformat() if c.create_time else None,
            "user_nickname": c.user.nickname if c.user else None,
            "user_avatar": c.user.avatar if c.user else None,
        })

    return ApiResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/{work_id}/video", summary="获取视频/音频流")
async def get_video_stream(work_id: str, db: Session = Depends(get_db)):
    """代理视频/音频流，解决403问题（图集的video_url是背景音乐）"""
    work = db.query(Work).filter(Work.work_id == work_id).first()
    if not work or not work.video_url:
        return ApiResponse(code=404, message="媒体资源不存在")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    video_url = work.video_url
    if work.work_type == "image":
        media_type = "audio/mpeg"
        filename = f"{work_id}.mp3"
    else:
        media_type = "video/mp4"
        filename = f"{work_id}.mp4"

    def iter_content():
        with requests.get(video_url, headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=8192):
                yield chunk

    return StreamingResponse(
        iter_content(),
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Accept-Ranges": "bytes",
        }
    )
