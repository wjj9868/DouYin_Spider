"""
作品相关 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import requests

from backend.database import get_db
from backend.models import Work, User
from backend.schemas.work import WorkResponse, WorkListResponse
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/works", tags=["作品"])


@router.get("", summary="获取作品列表")
async def get_works(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    work_type: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
) -> ApiResponse[WorkListResponse]:
    """获取作品列表（分页）"""
    query = db.query(Work).join(User, isouter=True)

    if work_type:
        query = query.filter(Work.work_type == work_type)
    if keyword:
        query = query.filter(Work.title.contains(keyword))

    total = query.count()
    total_pages = (total + page_size - 1) // page_size
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


@router.get("/{work_id}/video", summary="获取视频流")
async def get_video_stream(work_id: str, db: Session = Depends(get_db)):
    """代理视频流，解决403问题"""
    work = db.query(Work).filter(Work.work_id == work_id).first()
    if not work or not work.video_url:
        return ApiResponse(code=404, message="视频不存在")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    def iter_content():
        with requests.get(work.video_url, headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=8192):
                yield chunk

    return StreamingResponse(
        iter_content(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f'inline; filename="{work_id}.mp4"',
            "Accept-Ranges": "bytes",
        }
    )
