"""
采集服务 - 负责执行采集任务，支持异步并发和状态机管理
"""
import asyncio
import json
from datetime import datetime
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session

from loguru import logger

from backend.database import SessionLocal
from backend.models import User, Work, Comment, Task
from backend.services.task_state_machine import (
    TaskStateMachine, TaskState, TaskEvent, get_state_machine
)


class CollectorService:
    """采集服务 - 支持异步并发和状态机"""

    def __init__(self, cookie_str: str = ""):
        self.cookie_str = cookie_str
        self._douyin = None
        self._running_tasks: dict[int, asyncio.Task] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._semaphore = asyncio.Semaphore(3)
        self.state_machine = get_state_machine()

    @property
    def douyin(self):
        if self._douyin is None:
            from backend.services.douyin import DouyinService
            self._douyin = DouyinService(self.cookie_str)
        return self._douyin

    def _get_db(self) -> Session:
        return SessionLocal()

    async def _update_db_task(self, task_id: int, state: TaskState, 
                               progress: int, result_count: int):
        """更新数据库中的任务状态"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            self._sync_update_db_task,
            task_id, state, progress, result_count
        )

    def _sync_update_db_task(self, task_id: int, state: TaskState,
                              progress: int, result_count: int):
        """同步更新数据库任务"""
        db = self._get_db()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = state.value
                task.progress = progress
                task.result_count = result_count
                if state == TaskState.RUNNING:
                    task.started_at = datetime.now()
                elif state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]:
                    task.completed_at = datetime.now()
                db.commit()
        finally:
            db.close()

    def _save_user(self, db: Session, user_data: dict) -> User:
        """保存用户到数据库"""
        if not user_data or not user_data.get("uid"):
            return None
        
        user = db.query(User).filter(User.uid == user_data.get("uid")).first()
        user_dict = {
            "uid": user_data.get("uid"),
            "sec_uid": user_data.get("sec_uid"),
            "unique_id": user_data.get("unique_id"),
            "nickname": user_data.get("nickname"),
            "avatar": user_data.get("avatar"),
            "signature": user_data.get("signature"),
            "gender": user_data.get("gender", 0),
            "age": user_data.get("age"),
            "follower_count": user_data.get("follower_count", 0),
            "following_count": user_data.get("following_count", 0),
            "aweme_count": user_data.get("aweme_count", 0),
            "total_favorited": user_data.get("total_favorited", 0),
            "ip_location": user_data.get("ip_location"),
            "user_url": user_data.get("user_url"),
        }
        if user:
            for key, value in user_dict.items():
                if value is not None and hasattr(user, key):
                    setattr(user, key, value)
        else:
            user = User(**{k: v for k, v in user_dict.items() if v is not None})
            db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def _save_work(self, db: Session, work_data: dict, user_id: int = None) -> Optional[Work]:
        """保存作品到数据库"""
        if not work_data:
            return None
        
        work_id = work_data.get("work_id")
        if not work_id:
            return None
        
        work = db.query(Work).filter(Work.work_id == work_id).first()
        if work:
            return work

        title = work_data.get("title", "")
        video_url = work_data.get("video_url", "")
        cover_url = work_data.get("cover_url", "")
        images = work_data.get("images", [])
        
        if not title and not video_url and not cover_url and not images:
            return None

        work_dict = {
            "work_id": work_id,
            "work_url": work_data.get("work_url", ""),
            "title": title,
            "description": work_data.get("description", ""),
            "work_type": work_data.get("work_type", "video"),
            "video_url": video_url,
            "cover_url": cover_url,
            "images": images,
            "digg_count": work_data.get("digg_count", 0),
            "comment_count": work_data.get("comment_count", 0),
            "collect_count": work_data.get("collect_count", 0),
            "share_count": work_data.get("share_count", 0),
            "admire_count": work_data.get("admire_count", 0),
            "topics": work_data.get("topics", []),
            "create_time": work_data.get("create_time"),
        }
        if user_id:
            work_dict["user_id"] = user_id

        work = Work(**work_dict)
        db.add(work)
        db.commit()
        db.refresh(work)
        return work

    def _save_comment(self, db: Session, comment_data: dict,
                      work_id: int, user_id: int = None,
                      parent_id: int = None) -> Comment:
        """保存评论到数据库"""
        if not comment_data or not comment_data.get("comment_id"):
            return None
        
        comment = db.query(Comment).filter(
            Comment.comment_id == comment_data["comment_id"]
        ).first()
        if comment:
            return comment

        comment_dict = {
            "comment_id": comment_data["comment_id"],
            "work_id": work_id,
            "content": comment_data.get("content", ""),
            "digg_count": comment_data.get("digg_count", 0),
            "create_time": comment_data.get("create_time"),
            "parent_id": parent_id,
        }
        if user_id:
            comment_dict["user_id"] = user_id

        comment = Comment(**comment_dict)
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    async def _run_sync(self, func, *args):
        """在线程池中运行同步函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, func, *args)

    async def collect_work(self, task_id: int, work_id: str):
        """采集单个作品"""
        context = await self.state_machine.create_task(
            task_id, "work", {"work_id": work_id},
            on_state_change=self._update_db_task
        )
        
        try:
            await self.state_machine.transition(task_id, TaskEvent.START)
            await self.state_machine.transition(task_id, TaskEvent.START)
            
            await self.state_machine.update_progress(task_id, 10)

            work_data = await self._run_sync(self.douyin.get_work_info, work_id)
            if not work_data:
                await self.state_machine.transition(task_id, TaskEvent.FAIL, "获取作品信息失败")
                return

            await self.state_machine.update_progress(task_id, 30)

            db = self._get_db()
            try:
                author = work_data.get("author", {})
                user = self._save_user(db, {
                    "uid": author.get("uid"),
                    "sec_uid": author.get("sec_uid"),
                    "nickname": author.get("nickname"),
                    "avatar": author.get("avatar"),
                })

                await self.state_machine.update_progress(task_id, 50)

                work = self._save_work(db, work_data, user.id if user else None)

                await self.state_machine.update_progress(task_id, 100, 1)
                await self.state_machine.transition(task_id, TaskEvent.COMPLETE)
                logger.info(f"[采集完成] 作品: {work_id}")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"[采集失败] 作品 {work_id}: {e}")
            await self.state_machine.transition(task_id, TaskEvent.FAIL, str(e))

    async def collect_user_by_url(self, task_id: int, sec_uid: str):
        """采集用户信息"""
        context = await self.state_machine.create_task(
            task_id, "user_by_url", {"sec_uid": sec_uid},
            on_state_change=self._update_db_task
        )

        try:
            await self.state_machine.transition(task_id, TaskEvent.START)
            await self.state_machine.transition(task_id, TaskEvent.START)

            await self.state_machine.update_progress(task_id, 10)

            user_data = await self._run_sync(self.douyin.get_user_info, sec_uid)
            if not user_data:
                await self.state_machine.transition(task_id, TaskEvent.FAIL, "获取用户信息失败")
                return

            await self.state_machine.update_progress(task_id, 50)

            db = self._get_db()
            try:
                user = self._save_user(db, user_data)
                await self.state_machine.update_progress(task_id, 100, 1)
                await self.state_machine.transition(task_id, TaskEvent.COMPLETE)
                logger.info(f"[采集完成] 用户: {user.nickname if user else sec_uid}")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"[采集失败] 用户 {sec_uid}: {e}")
            await self.state_machine.transition(task_id, TaskEvent.FAIL, str(e))

    async def collect_user_works(self, task_id: int, sec_uid: str, max_count: int = 100):
        """采集用户作品"""
        context = await self.state_machine.create_task(
            task_id, "user_works", {"sec_uid": sec_uid, "max_count": max_count},
            total_count=max_count, on_state_change=self._update_db_task
        )

        try:
            await self.state_machine.transition(task_id, TaskEvent.START)
            await self.state_machine.transition(task_id, TaskEvent.START)

            await self.state_machine.update_progress(task_id, 5)

            user_data = await self._run_sync(self.douyin.get_user_info, sec_uid)
            if not user_data:
                await self.state_machine.transition(task_id, TaskEvent.FAIL, "获取用户信息失败")
                return

            db = self._get_db()
            try:
                user = self._save_user(db, user_data)
                await self.state_machine.update_progress(task_id, 10)

                max_cursor = 0
                collected = 0
                has_more = True

                while has_more and collected < max_count:
                    result = await self._run_sync(
                        self.douyin.get_user_works, sec_uid, max_cursor, 20
                    )
                    if not result:
                        break

                    for work_data in result["works"]:
                        if collected >= max_count:
                            break
                        self._save_work(db, work_data, user.id if user else None)
                        collected += 1

                        progress = int(10 + (collected / max_count) * 85)
                        await self.state_machine.update_progress(task_id, progress, collected)

                    has_more = result["has_more"]
                    max_cursor = result["max_cursor"]
                    await asyncio.sleep(0.3)

                await self.state_machine.update_progress(task_id, 100, collected)
                await self.state_machine.transition(task_id, TaskEvent.COMPLETE)
                logger.info(f"[采集完成] 用户作品: {sec_uid}, 共 {collected} 个")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"[采集失败] 用户作品 {sec_uid}: {e}")
            await self.state_machine.transition(task_id, TaskEvent.FAIL, str(e))

    async def collect_search_works(self, task_id: int, keyword: str, max_count: int = 50,
                                    sort_type: str = "0", publish_time: str = "0",
                                    filter_duration: str = "", search_range: str = "0",
                                    content_type: str = "0"):
        """搜索采集作品"""
        context = await self.state_machine.create_task(
            task_id, "search", 
            {"keyword": keyword, "max_count": max_count},
            total_count=max_count, on_state_change=self._update_db_task
        )

        try:
            await self.state_machine.transition(task_id, TaskEvent.START)
            await self.state_machine.transition(task_id, TaskEvent.START)

            await self.state_machine.update_progress(task_id, 5)

            result = await self._run_sync(
                self.douyin.search_works, keyword, max_count, sort_type,
                publish_time, filter_duration, search_range, content_type
            )
            if not result:
                await self.state_machine.transition(task_id, TaskEvent.FAIL, "搜索返回空结果")
                return

            works = result.get("works", [])
            db = self._get_db()
            try:
                collected = 0
                for work_data in works:
                    if collected >= max_count:
                        break

                    author = work_data.get("author", {})
                    user = None
                    if author.get("uid"):
                        user = self._save_user(db, author)
                    
                    self._save_work(db, work_data, user.id if user else None)
                    collected += 1

                    progress = int(5 + (collected / max_count) * 90)
                    await self.state_machine.update_progress(task_id, progress, collected)
                    await asyncio.sleep(0.2)

                await self.state_machine.update_progress(task_id, 100, collected)
                await self.state_machine.transition(task_id, TaskEvent.COMPLETE)
                logger.info(f"[采集完成] 搜索: {keyword}, 共 {collected} 个")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"[采集失败] 搜索 {keyword}: {e}")
            await self.state_machine.transition(task_id, TaskEvent.FAIL, str(e))

    async def collect_work_comments(self, task_id: int, work_id: str, max_count: int = 100):
        """采集作品评论"""
        context = await self.state_machine.create_task(
            task_id, "comment", {"work_id": work_id, "max_count": max_count},
            total_count=max_count, on_state_change=self._update_db_task
        )

        try:
            await self.state_machine.transition(task_id, TaskEvent.START)
            await self.state_machine.transition(task_id, TaskEvent.START)

            await self.state_machine.update_progress(task_id, 5)

            work_data = await self._run_sync(self.douyin.get_work_info, work_id)
            if not work_data:
                await self.state_machine.transition(task_id, TaskEvent.FAIL, "获取作品信息失败")
                return

            db = self._get_db()
            try:
                author = work_data.get("author", {})
                user = None
                if author.get("uid"):
                    user = self._save_user(db, {
                        "uid": author.get("uid"),
                        "sec_uid": author.get("sec_uid"),
                        "nickname": author.get("nickname"),
                        "avatar": author.get("avatar"),
                    })
                work = self._save_work(db, work_data, user.id if user else None)

                await self.state_machine.update_progress(task_id, 10)

                cursor = 0
                collected = 0
                has_more = True

                while has_more and collected < max_count:
                    result = await self._run_sync(
                        self.douyin.get_work_comments, work_id, cursor, 20
                    )
                    if not result:
                        break

                    for comment_data in result.get("comments", []):
                        if collected >= max_count:
                            break

                        comment_user_data = comment_data.get("user", {})
                        comment_user = None
                        if comment_user_data.get("uid"):
                            comment_user = self._save_user(db, {
                                "uid": comment_user_data.get("uid"),
                                "nickname": comment_user_data.get("nickname"),
                                "avatar": comment_user_data.get("avatar"),
                            })

                        self._save_comment(
                            db, comment_data, work.id if work else 0,
                            comment_user.id if comment_user else None
                        )
                        collected += 1

                    has_more = result.get("has_more", False)
                    cursor = result.get("cursor", 0)

                    progress = int(10 + (collected / max_count) * 85)
                    await self.state_machine.update_progress(task_id, progress, collected)
                    await asyncio.sleep(0.3)

                await self.state_machine.update_progress(task_id, 100, collected)
                await self.state_machine.transition(task_id, TaskEvent.COMPLETE)
                logger.info(f"[采集完成] 评论: {work_id}, 共 {collected} 条")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"[采集失败] 评论 {work_id}: {e}")
            await self.state_machine.transition(task_id, TaskEvent.FAIL, str(e))

    async def collect_user_followers(self, task_id: int, uid: str, sec_uid: str, max_count: int = 100):
        """采集用户粉丝"""
        context = await self.state_machine.create_task(
            task_id, "collect_followers", 
            {"uid": uid, "sec_uid": sec_uid, "max_count": max_count},
            total_count=max_count, on_state_change=self._update_db_task
        )

        try:
            await self.state_machine.transition(task_id, TaskEvent.START)
            await self.state_machine.transition(task_id, TaskEvent.START)

            await self.state_machine.update_progress(task_id, 5)

            result = await self._run_sync(
                self.douyin.get_user_followers, uid, sec_uid, max_count
            )
            if not result:
                await self.state_machine.transition(task_id, TaskEvent.FAIL, "获取粉丝列表失败")
                return

            followers = result.get("followers", [])
            db = self._get_db()
            try:
                collected = 0
                for follower_data in followers:
                    if collected >= max_count:
                        break

                    if follower_data.get("uid"):
                        self._save_user(db, {
                            "uid": follower_data.get("uid"),
                            "sec_uid": follower_data.get("sec_uid"),
                            "nickname": follower_data.get("nickname"),
                            "avatar": follower_data.get("avatar_thumb", {}).get("url_list", [""])[0] if follower_data.get("avatar_thumb") else "",
                            "signature": follower_data.get("signature"),
                            "follower_count": follower_data.get("follower_count", 0),
                            "following_count": follower_data.get("following_count", 0),
                            "aweme_count": follower_data.get("aweme_count", 0),
                        })
                        collected += 1

                    progress = int(5 + (collected / max_count) * 90)
                    await self.state_machine.update_progress(task_id, progress, collected)

                await self.state_machine.update_progress(task_id, 100, collected)
                await self.state_machine.transition(task_id, TaskEvent.COMPLETE)
                logger.info(f"[采集完成] 粉丝: {sec_uid}, 共 {collected} 个")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"[采集失败] 粉丝 {sec_uid}: {e}")
            await self.state_machine.transition(task_id, TaskEvent.FAIL, str(e))

    async def collect_user_followings(self, task_id: int, uid: str, sec_uid: str, max_count: int = 100):
        """采集用户关注"""
        context = await self.state_machine.create_task(
            task_id, "collect_followings",
            {"uid": uid, "sec_uid": sec_uid, "max_count": max_count},
            total_count=max_count, on_state_change=self._update_db_task
        )

        try:
            await self.state_machine.transition(task_id, TaskEvent.START)
            await self.state_machine.transition(task_id, TaskEvent.START)

            await self.state_machine.update_progress(task_id, 5)

            result = await self._run_sync(
                self.douyin.get_user_followings, uid, sec_uid, max_count
            )
            if not result:
                await self.state_machine.transition(task_id, TaskEvent.FAIL, "获取关注列表失败")
                return

            followings = result.get("followings", [])
            db = self._get_db()
            try:
                collected = 0
                for following_data in followings:
                    if collected >= max_count:
                        break

                    if following_data.get("uid"):
                        self._save_user(db, {
                            "uid": following_data.get("uid"),
                            "sec_uid": following_data.get("sec_uid"),
                            "nickname": following_data.get("nickname"),
                            "avatar": following_data.get("avatar_thumb", {}).get("url_list", [""])[0] if following_data.get("avatar_thumb") else "",
                            "signature": following_data.get("signature"),
                            "follower_count": following_data.get("follower_count", 0),
                            "following_count": following_data.get("following_count", 0),
                            "aweme_count": following_data.get("aweme_count", 0),
                        })
                        collected += 1

                    progress = int(5 + (collected / max_count) * 90)
                    await self.state_machine.update_progress(task_id, progress, collected)

                await self.state_machine.update_progress(task_id, 100, collected)
                await self.state_machine.transition(task_id, TaskEvent.COMPLETE)
                logger.info(f"[采集完成] 关注: {sec_uid}, 共 {collected} 个")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"[采集失败] 关注 {sec_uid}: {e}")
            await self.state_machine.transition(task_id, TaskEvent.FAIL, str(e))

    def start_task(self, task_id: int, task_type: str, params: dict) -> asyncio.Task:
        """启动采集任务"""
        async def run_task():
            async with self._semaphore:
                if task_type == "work":
                    await self.collect_work(task_id, params.get("work_id"))
                elif task_type == "user_works":
                    await self.collect_user_works(
                        task_id, params.get("sec_uid"), params.get("max_count", 100)
                    )
                elif task_type == "user_by_url":
                    await self.collect_user_by_url(task_id, params.get("sec_uid"))
                elif task_type == "search":
                    await self.collect_search_works(
                        task_id, params.get("keyword"), params.get("max_count", 50),
                        params.get("sort_type", "0"), params.get("publish_time", "0"),
                        params.get("filter_duration", ""), params.get("search_range", "0"),
                        params.get("content_type", "0")
                    )
                elif task_type == "comment":
                    await self.collect_work_comments(
                        task_id, params.get("work_id"), params.get("max_count", 100)
                    )
                elif task_type == "collect_followers":
                    await self.collect_user_followers(
                        task_id, params.get("uid"), params.get("sec_uid"),
                        params.get("max_count", 100)
                    )
                elif task_type == "collect_followings":
                    await self.collect_user_followings(
                        task_id, params.get("uid"), params.get("sec_uid"),
                        params.get("max_count", 100)
                    )

        task = asyncio.create_task(run_task())
        self._running_tasks[task_id] = task
        return task

    async def cancel_task(self, task_id: int):
        """取消任务"""
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]
        await self.state_machine.transition(task_id, TaskEvent.CANCEL)

    def get_running_count(self) -> int:
        """获取运行中的任务数量"""
        return len([t for t in self._running_tasks.values() if not t.done()])


collector = CollectorService()


def get_collector() -> CollectorService:
    return collector
