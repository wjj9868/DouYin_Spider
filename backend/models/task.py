"""
任务模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.database import Base


class Task(Base):
    """采集任务表"""
    __tablename__ = "dy_task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(32), nullable=False, comment="任务类型: work/user/search/live")
    task_params = Column(Text, nullable=False, comment="JSON参数")
    status = Column(String(32), default="pending", comment="状态: pending/running/completed/failed")
    progress = Column(Integer, default=0, comment="进度 0-100")
    total_count = Column(Integer, default=0, comment="总数量")
    result_count = Column(Integer, default=0, comment="已采集数量")
    error_message = Column(Text, comment="错误信息")
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    def __repr__(self):
        return f"<Task(id={self.id}, type={self.task_type}, status={self.status})>"
