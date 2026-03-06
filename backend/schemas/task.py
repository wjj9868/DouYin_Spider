"""
任务相关 Schema
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, field_validator
import json


class TaskBase(BaseModel):
    task_type: str
    task_params: dict


class TaskCreate(TaskBase):
    pass


class TaskResponse(BaseModel):
    id: int
    task_type: str
    task_params: dict
    status: str = "pending"
    progress: int = 0
    total_count: int = 0
    result_count: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator('task_params', mode='before')
    @classmethod
    def parse_task_params(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int
