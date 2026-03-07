"""
Cookie 管理 API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import requests

from backend.database import get_db
from backend.models import Cookie
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/cookies", tags=["Cookie管理"])


COOKIE_TYPES = {
    "default": {"name": "默认 Cookie", "desc": "用于作品采集、用户信息等"},
    "live": {"name": "直播 Cookie", "desc": "用于直播弹幕采集"},
}


class CookieCreate(BaseModel):
    name: str
    cookie_str: str
    cookie_type: str = "default"


class CookieUpdate(BaseModel):
    name: Optional[str] = None
    cookie_str: Optional[str] = None
    cookie_type: Optional[str] = None
    is_active: Optional[bool] = None


class CookieResponse(BaseModel):
    id: int
    name: str
    cookie_type: str
    cookie_str: str
    is_active: bool
    is_valid: bool
    last_check_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CookieListResponse(BaseModel):
    items: list[CookieResponse]
    total: int


class CookieTypeResponse(BaseModel):
    type: str
    name: str
    desc: str


class CookieStatsResponse(BaseModel):
    type: str
    name: str
    desc: str
    total: int
    active: Optional[CookieResponse] = None


def mask_cookie(cookie_str: str) -> str:
    """掩码显示 Cookie，只显示前后各20个字符"""
    if not cookie_str or len(cookie_str) <= 40:
        return cookie_str[:10] + "..." if cookie_str else ""
    return cookie_str[:20] + "..." + cookie_str[-20:]


@router.get("/types", summary="获取Cookie类型列表")
async def get_cookie_types() -> ApiResponse[List[CookieTypeResponse]]:
    """获取所有支持的Cookie类型"""
    types = [
        CookieTypeResponse(type=k, name=v["name"], desc=v["desc"])
        for k, v in COOKIE_TYPES.items()
    ]
    return ApiResponse(data=types)


@router.get("/stats", summary="获取Cookie统计")
async def get_cookie_stats(db: Session = Depends(get_db)) -> ApiResponse[List[CookieStatsResponse]]:
    """获取各类型Cookie统计"""
    stats = []
    for type_key, type_info in COOKIE_TYPES.items():
        total = db.query(Cookie).filter(Cookie.cookie_type == type_key).count()
        active = db.query(Cookie).filter(
            Cookie.cookie_type == type_key,
            Cookie.is_active == True
        ).first()
        
        active_resp = None
        if active:
            active_resp = CookieResponse(
                id=active.id,
                name=active.name,
                cookie_type=active.cookie_type,
                cookie_str=mask_cookie(active.cookie_str),
                is_active=active.is_active,
                is_valid=active.is_valid,
                last_check_at=active.last_check_at,
                last_used_at=active.last_used_at,
                created_at=active.created_at,
                updated_at=active.updated_at,
            )
        
        stats.append(CookieStatsResponse(
            type=type_key,
            name=type_info["name"],
            desc=type_info["desc"],
            total=total,
            active=active_resp
        ))
    
    return ApiResponse(data=stats)


@router.get("", summary="获取Cookie列表")
async def get_cookies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    cookie_type: Optional[str] = Query(None, description="Cookie类型筛选"),
    db: Session = Depends(get_db)
) -> ApiResponse[CookieListResponse]:
    """获取Cookie列表"""
    query = db.query(Cookie)
    
    if cookie_type:
        query = query.filter(Cookie.cookie_type == cookie_type)
    
    total = query.count()
    offset = (page - 1) * page_size
    cookies = query.order_by(Cookie.created_at.desc()).offset(offset).limit(page_size).all()
    
    items = []
    for c in cookies:
        items.append(CookieResponse(
            id=c.id,
            name=c.name,
            cookie_type=c.cookie_type,
            cookie_str=mask_cookie(c.cookie_str),
            is_active=c.is_active,
            is_valid=c.is_valid,
            last_check_at=c.last_check_at,
            last_used_at=c.last_used_at,
            created_at=c.created_at,
            updated_at=c.updated_at,
        ))
    
    return ApiResponse(data=CookieListResponse(items=items, total=total))


@router.get("/{cookie_id}", summary="获取Cookie详情")
async def get_cookie(cookie_id: int, db: Session = Depends(get_db)) -> ApiResponse[CookieResponse]:
    """获取单个Cookie详情"""
    cookie = db.query(Cookie).filter(Cookie.id == cookie_id).first()
    if not cookie:
        return ApiResponse(code=404, message="Cookie不存在")
    
    return ApiResponse(data=CookieResponse(
        id=cookie.id,
        name=cookie.name,
        cookie_type=cookie.cookie_type,
        cookie_str=mask_cookie(cookie.cookie_str),
        is_active=cookie.is_active,
        is_valid=cookie.is_valid,
        last_check_at=cookie.last_check_at,
        last_used_at=cookie.last_used_at,
        created_at=cookie.created_at,
        updated_at=cookie.updated_at,
    ))


@router.post("", summary="创建Cookie")
async def create_cookie(data: CookieCreate, db: Session = Depends(get_db)) -> ApiResponse[CookieResponse]:
    """创建新Cookie"""
    cookie_type = data.cookie_type or "default"
    
    cookie = Cookie(
        name=data.name,
        cookie_str=data.cookie_str,
        cookie_type=cookie_type,
        is_active=False,
        is_valid=True
    )
    db.add(cookie)
    db.commit()
    db.refresh(cookie)
    
    return ApiResponse(data=CookieResponse(
        id=cookie.id,
        name=cookie.name,
        cookie_type=cookie.cookie_type,
        cookie_str=mask_cookie(cookie.cookie_str),
        is_active=cookie.is_active,
        is_valid=cookie.is_valid,
        last_check_at=cookie.last_check_at,
        last_used_at=cookie.last_used_at,
        created_at=cookie.created_at,
        updated_at=cookie.updated_at,
    ), message="创建成功")


@router.put("/{cookie_id}", summary="更新Cookie")
async def update_cookie(
    cookie_id: int,
    data: CookieUpdate,
    db: Session = Depends(get_db)
) -> ApiResponse[CookieResponse]:
    """更新Cookie"""
    cookie = db.query(Cookie).filter(Cookie.id == cookie_id).first()
    if not cookie:
        return ApiResponse(code=404, message="Cookie不存在")
    
    if data.name is not None:
        cookie.name = data.name
    if data.cookie_str is not None:
        cookie.cookie_str = data.cookie_str
        cookie.is_valid = True
    if data.cookie_type is not None:
        cookie.cookie_type = data.cookie_type
    if data.is_active is not None:
        cookie.is_active = data.is_active
    
    db.commit()
    db.refresh(cookie)
    
    return ApiResponse(data=CookieResponse(
        id=cookie.id,
        name=cookie.name,
        cookie_type=cookie.cookie_type,
        cookie_str=mask_cookie(cookie.cookie_str),
        is_active=cookie.is_active,
        is_valid=cookie.is_valid,
        last_check_at=cookie.last_check_at,
        last_used_at=cookie.last_used_at,
        created_at=cookie.created_at,
        updated_at=cookie.updated_at,
    ), message="更新成功")


@router.delete("/{cookie_id}", summary="删除Cookie")
async def delete_cookie(cookie_id: int, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """删除Cookie"""
    cookie = db.query(Cookie).filter(Cookie.id == cookie_id).first()
    if not cookie:
        return ApiResponse(code=404, message="Cookie不存在")
    
    db.delete(cookie)
    db.commit()
    return ApiResponse(message="删除成功")


@router.post("/{cookie_id}/verify", summary="验证Cookie有效性")
async def verify_cookie(cookie_id: int, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """验证Cookie是否有效"""
    cookie = db.query(Cookie).filter(Cookie.id == cookie_id).first()
    if not cookie:
        return ApiResponse(code=404, message="Cookie不存在")
    
    is_valid = False
    error_msg = ""
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Referer": "https://www.douyin.com/",
            "Cookie": cookie.cookie_str,
        }
        
        resp = requests.get(
            "https://www.douyin.com/user/self",
            headers=headers,
            allow_redirects=False,
            timeout=10
        )
        
        if resp.status_code == 200 or resp.status_code == 302:
            is_valid = True
        else:
            error_msg = f"状态码: {resp.status_code}"
    except Exception as e:
        error_msg = str(e)
    
    cookie.is_valid = is_valid
    cookie.last_check_at = datetime.now()
    db.commit()
    
    return ApiResponse(data={
        "is_valid": is_valid,
        "error_msg": error_msg,
        "last_check_at": cookie.last_check_at.isoformat()
    }, message="验证完成")


@router.post("/{cookie_id}/activate", summary="启用Cookie")
async def activate_cookie(cookie_id: int, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    """启用Cookie（同时禁用同类型的其他Cookie）"""
    cookie = db.query(Cookie).filter(Cookie.id == cookie_id).first()
    if not cookie:
        return ApiResponse(code=404, message="Cookie不存在")
    
    db.query(Cookie).filter(Cookie.cookie_type == cookie.cookie_type).update({Cookie.is_active: False})
    cookie.is_active = True
    db.commit()
    
    if cookie.cookie_type == "default":
        from backend.services.collector import get_collector
        collector = get_collector()
        collector.cookie_str = cookie.cookie_str
        if hasattr(collector, 'douyin') and collector.douyin:
            collector.douyin.cookie_str = cookie.cookie_str
    
    if cookie.cookie_type == "live":
        from backend.core.utils.common_util import dy_live_auth
        if dy_live_auth:
            dy_live_auth.perepare_auth(cookie.cookie_str, "", "")
    
    return ApiResponse(message="Cookie已启用")


@router.get("/active/{cookie_type}", summary="获取指定类型当前启用的Cookie")
async def get_active_cookie_by_type(
    cookie_type: str,
    db: Session = Depends(get_db)
) -> ApiResponse[CookieResponse]:
    """获取指定类型当前启用的Cookie"""
    cookie = db.query(Cookie).filter(
        Cookie.cookie_type == cookie_type,
        Cookie.is_active == True
    ).first()
    if not cookie:
        return ApiResponse(code=404, message=f"没有启用的{COOKIE_TYPES.get(cookie_type, {}).get('name', cookie_type)}")
    
    return ApiResponse(data=CookieResponse(
        id=cookie.id,
        name=cookie.name,
        cookie_type=cookie.cookie_type,
        cookie_str=mask_cookie(cookie.cookie_str),
        is_active=cookie.is_active,
        is_valid=cookie.is_valid,
        last_check_at=cookie.last_check_at,
        last_used_at=cookie.last_used_at,
        created_at=cookie.created_at,
        updated_at=cookie.updated_at,
    ))
