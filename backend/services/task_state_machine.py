"""
任务状态机 - 管理任务生命周期和状态转换
"""
from enum import Enum
from typing import Optional, Callable, Awaitable
from datetime import datetime
from dataclasses import dataclass, field
from loguru import logger


class TaskState(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskEvent(Enum):
    """任务事件枚举"""
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    COMPLETE = "complete"
    FAIL = "fail"
    CANCEL = "cancel"
    RETRY = "retry"


STATE_TRANSITIONS = {
    TaskState.PENDING: {
        TaskEvent.START: TaskState.QUEUED,
        TaskEvent.CANCEL: TaskState.CANCELLED,
    },
    TaskState.QUEUED: {
        TaskEvent.START: TaskState.RUNNING,
        TaskEvent.CANCEL: TaskState.CANCELLED,
    },
    TaskState.RUNNING: {
        TaskEvent.PAUSE: TaskState.PAUSED,
        TaskEvent.COMPLETE: TaskState.COMPLETED,
        TaskEvent.FAIL: TaskState.FAILED,
        TaskEvent.CANCEL: TaskState.CANCELLED,
    },
    TaskState.PAUSED: {
        TaskEvent.RESUME: TaskState.RUNNING,
        TaskEvent.CANCEL: TaskState.CANCELLED,
    },
    TaskState.FAILED: {
        TaskEvent.RETRY: TaskState.QUEUED,
        TaskEvent.CANCEL: TaskState.CANCELLED,
    },
    TaskState.COMPLETED: {},
    TaskState.CANCELLED: {},
}


@dataclass
class TaskContext:
    """任务上下文"""
    task_id: int
    task_type: str
    params: dict
    state: TaskState = TaskState.PENDING
    progress: int = 0
    total_count: int = 1
    result_count: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    on_state_change: Optional[Callable[[int, TaskState, int, int], Awaitable[None]]] = None

    def can_transition(self, event: TaskEvent) -> bool:
        """检查是否可以执行状态转换"""
        return event in STATE_TRANSITIONS.get(self.state, {})

    def get_next_state(self, event: TaskEvent) -> Optional[TaskState]:
        """获取下一个状态"""
        transitions = STATE_TRANSITIONS.get(self.state, {})
        return transitions.get(event)


class TaskStateMachine:
    """任务状态机"""

    def __init__(self):
        self._tasks: dict[int, TaskContext] = {}
        self._lock = None

    async def _get_lock(self):
        """获取异步锁"""
        if self._lock is None:
            import asyncio
            self._lock = asyncio.Lock()
        return self._lock

    async def create_task(self, task_id: int, task_type: str, params: dict,
                          total_count: int = 1, max_retries: int = 3,
                          on_state_change: Optional[Callable] = None) -> TaskContext:
        """创建新任务"""
        lock = await self._get_lock()
        async with lock:
            context = TaskContext(
                task_id=task_id,
                task_type=task_type,
                params=params,
                total_count=total_count,
                max_retries=max_retries,
                on_state_change=on_state_change,
            )
            self._tasks[task_id] = context
            logger.info(f"[状态机] 创建任务: id={task_id}, type={task_type}")
            return context

    async def get_task(self, task_id: int) -> Optional[TaskContext]:
        """获取任务上下文"""
        return self._tasks.get(task_id)

    async def transition(self, task_id: int, event: TaskEvent, 
                         error_message: str = None) -> bool:
        """执行状态转换"""
        lock = await self._get_lock()
        async with lock:
            context = self._tasks.get(task_id)
            if not context:
                logger.warning(f"[状态机] 任务不存在: id={task_id}")
                return False

            if not context.can_transition(event):
                logger.warning(
                    f"[状态机] 无效状态转换: id={task_id}, "
                    f"state={context.state.value}, event={event.value}"
                )
                return False

            next_state = context.get_next_state(event)
            old_state = context.state
            context.state = next_state
            context.error_message = error_message

            if next_state == TaskState.RUNNING:
                context.started_at = datetime.now()
            elif next_state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]:
                context.completed_at = datetime.now()

            if next_state == TaskState.FAILED:
                context.retry_count += 1

            logger.info(
                f"[状态机] 状态转换: id={task_id}, "
                f"{old_state.value} -> {next_state.value}"
            )

            if context.on_state_change:
                try:
                    await context.on_state_change(
                        task_id, next_state, context.progress, context.result_count
                    )
                except Exception as e:
                    logger.error(f"[状态机] 状态变更回调失败: {e}")

            return True

    async def update_progress(self, task_id: int, progress: int, result_count: int = None):
        """更新任务进度"""
        lock = await self._get_lock()
        async with lock:
            context = self._tasks.get(task_id)
            if not context:
                return

            context.progress = min(100, max(0, progress))
            if result_count is not None:
                context.result_count = result_count

            if context.on_state_change:
                try:
                    await context.on_state_change(
                        task_id, context.state, context.progress, context.result_count
                    )
                except Exception as e:
                    logger.error(f"[状态机] 进度更新回调失败: {e}")

    async def can_retry(self, task_id: int) -> bool:
        """检查是否可以重试"""
        context = self._tasks.get(task_id)
        if not context:
            return False
        return context.retry_count < context.max_retries

    async def remove_task(self, task_id: int):
        """移除任务"""
        lock = await self._get_lock()
        async with lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                logger.info(f"[状态机] 移除任务: id={task_id}")

    def get_running_tasks(self) -> list[int]:
        """获取运行中的任务ID列表"""
        return [
            tid for tid, ctx in self._tasks.items()
            if ctx.state == TaskState.RUNNING
        ]

    def get_stats(self) -> dict:
        """获取任务统计"""
        stats = {state.value: 0 for state in TaskState}
        for ctx in self._tasks.values():
            stats[ctx.state.value] += 1
        return stats


task_state_machine = TaskStateMachine()


def get_state_machine() -> TaskStateMachine:
    """获取状态机实例"""
    return task_state_machine
