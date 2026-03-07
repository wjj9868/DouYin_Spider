from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, text
from sqlalchemy.sql import func
from backend.database import Base


class Cookie(Base):
    __tablename__ = "cookies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="Cookie名称/备注")
    cookie_type = Column(String(50), server_default=text("'default'"), comment="Cookie类型: default/live等")
    cookie_str = Column(Text, nullable=False, comment="Cookie字符串")
    is_active = Column(Boolean, server_default=text("0"), comment="是否启用")
    is_valid = Column(Boolean, server_default=text("1"), comment="是否有效")
    last_check_at = Column(DateTime, comment="最后检查时间")
    last_used_at = Column(DateTime, comment="最后使用时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Cookie(id={self.id}, name={self.name}, type={self.cookie_type}, is_active={self.is_active})>"
