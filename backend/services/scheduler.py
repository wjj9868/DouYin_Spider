"""
定时任务调度服务
"""
import asyncio
import json
from datetime import datetime
from typing import Optional
from croniter import croniter
from sqlalchemy.orm import Session

from loguru import logger

from backend.database import SessionLocal
from backend.models import ScheduledTask, Task
from backend.services.collector import get_collector


class SchedulerService:
    """定时任务调度服务"""

    def __init__(self):
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动调度器"""
        if self._running:
            return
        self._running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        logger.info("定时任务调度器已启动")

    async def stop(self):
        """停止调度器"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            self._scheduler_task = None
        logger.info("定时任务调度器已停止")

    async def _run_scheduler(self):
        """调度器主循环"""
        while self._running:
            try:
                await self._check_scheduled_tasks()
            except Exception as e:
                logger.error(f"调度器检查失败: {e}")
            await asyncio.sleep(60)

    async def _check_scheduled_tasks(self):
        """检查并执行到期的定时任务"""
        db = SessionLocal()
        try:
            now = datetime.now()
            scheduled_tasks = db.query(ScheduledTask).filter(
                ScheduledTask.is_active == True,
                ScheduledTask.next_run_at <= now
            ).all()

            for st in scheduled_tasks:
                try:
                    await self._execute_scheduled_task(st)
                    self._update_next_run_time(db, st)
                except Exception as e:
                    logger.error(f"执行定时任务失败 [{st.name}]: {e}")
                    st.error_message = str(e)
                    db.commit()
        finally:
            db.close()

    async def _execute_scheduled_task(self, scheduled_task: ScheduledTask):
        """执行定时任务"""
        logger.info(f"开始执行定时任务: {scheduled_task.name}")

        task = Task(
            task_type=scheduled_task.task_type,
            task_params=scheduled_task.task_params,
            status="pending"
        )
        db = SessionLocal()
        try:
            db.add(task)
            db.commit()
            db.refresh(task)

            params = json.loads(scheduled_task.task_params)
            collector = get_collector()
            collector.start_task(task.id, scheduled_task.task_type, params)

            scheduled_task.last_run_at = datetime.now()
            logger.info(f"定时任务 [{scheduled_task.name}] 已创建采集任务: {task.id}")
        finally:
            db.close()

    def _update_next_run_time(self, db: Session, scheduled_task: ScheduledTask):
        """更新下次执行时间"""
        try:
            cron = croniter(scheduled_task.cron_expression, datetime.now())
            scheduled_task.next_run_at = cron.get_next(datetime.now())
            db.commit()
            logger.info(f"定时任务 [{scheduled_task.name}] 下次执行时间: {scheduled_task.next_run_at}")
        except Exception as e:
            logger.error(f"解析Cron表达式失败: {e}")
            scheduled_task.is_active = False
            db.commit()


scheduler_service = SchedulerService()


def get_scheduler():
    """获取调度器实例"""
    return scheduler_service
