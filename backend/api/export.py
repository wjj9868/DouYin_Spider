"""
导出相关 API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database import get_db
from backend.services.exporter import get_exporter
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/export", tags=["导出"])


@router.get("/works", summary="导出作品Excel")
async def export_works(
    work_ids: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """导出作品到 Excel"""
    exporter = get_exporter()

    # 解析 work_ids
    ids = None
    if work_ids:
        ids = [w.strip() for w in work_ids.split(",") if w.strip()]

    # 生成 Excel
    excel_file = exporter.export_works(db, ids, limit)

    # 生成文件名
    filename = f"works_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/users", summary="导出用户Excel")
async def export_users(
    uids: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """导出用户到 Excel"""
    exporter = get_exporter()

    # 解析 uids
    ids = None
    if uids:
        ids = [u.strip() for u in uids.split(",") if u.strip()]

    # 生成 Excel
    excel_file = exporter.export_users(db, ids, limit)

    # 生成文件名
    filename = f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/comments", summary="导出评论Excel")
async def export_comments(
    work_id: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """导出评论到 Excel"""
    exporter = get_exporter()

    # 生成 Excel
    excel_file = exporter.export_comments(db, work_id, limit)

    # 生成文件名
    filename = f"comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
