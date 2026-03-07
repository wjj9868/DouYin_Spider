"""
采集服务 - 负责执行采集任务
"""
import asyncio
import json
from datetime import datetime
from typing import Optional, Callable
from sqlalchemy.orm import Session

from loguru import logger

from backend.database import SessionLocal
from backend.models import User, Work, Comment, Task


class CollectorService:
    """采集服务"""

    def __init__(self, cookie_str: str = ""):
        self.cookie_str = cookie_str
        self._douyin = None
        self._running_tasks: dict[int, asyncio.Task] = {}

    @property
    def douyin(self):
        if self._douyin is None:
            from backend.services.douyin import DouyinService
            self._douyin = DouyinService(self.cookie_str)
        return self._douyin

    def _get_db(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()

    def _save_user(self, db: Session, user_data: dict) -> User:
        """保存用户到数据库"""
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

    def _save_work(self, db: Session, work_data: dict, user_id: int = None) -> Work:
        """保存作品到数据库"""
        work = db.query(Work).filter(Work.work_id == work_data["work_id"]).first()
        if work:
            return work

        work_dict = {
            "work_id": work_data["work_id"],
            "work_url": work_data.get("work_url", ""),
            "title": work_data.get("title", ""),
            "description": work_data.get("description", ""),
            "work_type": work_data.get("work_type", "video"),
            "video_url": work_data.get("video_url", ""),
            "cover_url": work_data.get("cover_url", ""),
            "images": work_data.get("images", []),
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

    def _update_task_progress(self, task_id: int, progress: int,
                               result_count: int = None, status: str = None):
        """更新任务进度"""
        db = self._get_db()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.progress = progress
                if result_count is not None:
                    task.result_count = result_count
                if status:
                    task.status = status
                    if status == "running":
                        task.started_at = datetime.now()
                    elif status in ["completed", "failed"]:
                        task.completed_at = datetime.now()
                db.commit()
        finally:
            db.close()

    async def collect_work(self, task_id: int, work_id: str):
        """采集单个作品"""
        db = self._get_db()
        try:
            self._update_task_progress(task_id, 10, status="running")

            work_data = self.douyin.get_work_info(work_id)
            if not work_data:
                self._update_task_progress(task_id, 100, status="failed")
                return

            self._update_task_progress(task_id, 30)

            author = work_data.get("author", {})
            user = self._save_user(db, {
                "uid": author.get("uid"),
                "sec_uid": author.get("sec_uid"),
                "nickname": author.get("nickname"),
                "avatar": author.get("avatar"),
            })

            self._update_task_progress(task_id, 50)

            work = self._save_work(db, work_data, user.id)

            self._update_task_progress(task_id, 100, result_count=1, status="completed")
            logger.info(f"采集作品完成: {work_id}")

        except Exception as e:
            logger.error(f"采集作品失败: {e}")
            self._update_task_progress(task_id, 100, status="failed")
        finally:
            db.close()

    async def collect_user_by_url(self, task_id: int, sec_uid: str):
        """通过主页URL采集用户信息"""
        db = self._get_db()
        try:
            self._update_task_progress(task_id, 10, status="running")

            user_data = self.douyin.get_user_info(sec_uid)
            if not user_data:
                self._update_task_progress(task_id, 100, status="failed")
                logger.error(f"获取用户信息失败: {sec_uid}")
                return

            self._update_task_progress(task_id, 50)

            user = self._save_user(db, user_data)

            self._update_task_progress(task_id, 100, result_count=1, status="completed")
            logger.info(f"采集用户信息完成: {user.nickname} (uid={user.uid})")

        except Exception as e:
            logger.error(f"采集用户信息失败: {e}")
            self._update_task_progress(task_id, 100, status="failed")
        finally:
            db.close()

    async def collect_user_works(self, task_id: int, sec_uid: str,
                                  max_count: int = 100):
        """采集用户作品"""
        db = self._get_db()
        try:
            self._update_task_progress(task_id, 5, status="running")

            user_data = self.douyin.get_user_info(sec_uid)
            if not user_data:
                self._update_task_progress(task_id, 100, status="failed")
                return

            user = self._save_user(db, user_data)
            self._update_task_progress(task_id, 10)

            max_cursor = 0
            collected = 0
            has_more = True

            while has_more and collected < max_count:
                result = self.douyin.get_user_works(sec_uid, max_cursor, 20)
                if not result:
                    break

                for work_data in result["works"]:
                    if collected >= max_count:
                        break
                    self._save_work(db, work_data, user.id)
                    collected += 1

                    progress = int(10 + (collected / max_count) * 85)
                    self._update_task_progress(task_id, progress, result_count=collected)

                has_more = result["has_more"]
                max_cursor = result["max_cursor"]

                await asyncio.sleep(0.5)

            self._update_task_progress(task_id, 100, result_count=collected, status="completed")
            logger.info(f"采集用户作品完成: {sec_uid}, 共 {collected} 个")

        except Exception as e:
            logger.error(f"采集用户作品失败: {e}")
            self._update_task_progress(task_id, 100, status="failed")
        finally:
            db.close()

    async def collect_search_works(self, task_id: int, keyword: str,
                                    max_count: int = 50, sort_type: str = "0",
                                    publish_time: str = "0", filter_duration: str = "",
                                    search_range: str = "0", content_type: str = "0"):
        """搜索采集作品

        Args:
            task_id: 任务ID
            keyword: 搜索关键词
            max_count: 最大采集数量
            sort_type: 排序方式 - 0综合排序, 1最多点赞, 2最新发布
            publish_time: 发布时间 - 0不限, 1一天内, 7一周内, 180半年内
            filter_duration: 视频时长 - 空不限, 0-1一分钟内, 1-5 1-5分钟, 5-10000 5分钟以上
            search_range: 搜索范围 - 0不限, 1最近看过, 2还未看过, 3关注的人
            content_type: 内容形式 - 0不限, 1视频, 2图文
        """
        db = self._get_db()
        try:
            logger.info(f"[采集任务] 开始搜索采集: task_id={task_id}, keyword='{keyword}', max_count={max_count}")
            self._update_task_progress(task_id, 5, status="running")

            result = self.douyin.search_works(
                keyword, max_count, sort_type, publish_time,
                filter_duration, search_range, content_type
            )
            if not result:
                logger.error(f"[采集任务] 搜索返回空结果: task_id={task_id}")
                self._update_task_progress(task_id, 100, status="failed")
                return

            works_count = len(result.get("works", []))
            logger.info(f"[采集任务] 搜索返回 {works_count} 条作品数据")

            collected = 0
            for work_data in result["works"]:
                if collected >= max_count:
                    break

                author = work_data.get("author", {})
                if author.get("uid"):
                    sec_uid = author.get("sec_uid")
                    if sec_uid:
                        existing_user = db.query(User).filter(User.sec_uid == sec_uid).first()
                        if existing_user and existing_user.follower_count > 0:
                            user = existing_user
                        else:
                            try:
                                full_user = self.douyin.get_user_info(sec_uid)
                                if full_user:
                                    user = self._save_user(db, full_user)
                                else:
                                    user = self._save_user(db, author)
                            except Exception as e:
                                logger.warning(f"获取用户完整信息失败: {e}")
                                user = self._save_user(db, author)
                    else:
                        user = self._save_user(db, author)
                    self._save_work(db, work_data, user.id)
                else:
                    self._save_work(db, work_data)

                collected += 1
                progress = int(5 + (collected / max_count) * 90)
                self._update_task_progress(task_id, progress, result_count=collected)

                await asyncio.sleep(0.3)

            self._update_task_progress(task_id, 100, result_count=collected, status="completed")
            logger.info(f"搜索采集完成: {keyword}, 共 {collected} 个")

        except Exception as e:
            logger.error(f"搜索采集失败: {e}")
            self._update_task_progress(task_id, 100, status="failed")
        finally:
            db.close()

    async def collect_work_comments(self, task_id: int, work_id: str,
                                     max_count: int = 100):
        """采集作品评论"""
        db = self._get_db()
        try:
            self._update_task_progress(task_id, 5, status="running")

            work_data = self.douyin.get_work_info(work_id)
            if not work_data:
                self._update_task_progress(task_id, 100, status="failed")
                return

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

            self._update_task_progress(task_id, 10)

            cursor = 0
            collected = 0
            has_more = True

            while has_more and collected < max_count:
                result = self.douyin.get_work_comments(work_id, cursor, 20)
                if not result:
                    break

                for comment_data in result["comments"]:
                    if collected >= max_count:
                        break

                    comment_user = None
                    comment_user_data = comment_data.get("user", {})
                    if comment_user_data.get("uid"):
                        comment_user = self._save_user(db, {
                            "uid": comment_user_data.get("uid"),
                            "nickname": comment_user_data.get("nickname"),
                            "avatar": comment_user_data.get("avatar"),
                        })

                    self._save_comment(
                        db, comment_data, work.id,
                        comment_user.id if comment_user else None
                    )
                    collected += 1

                has_more = result["has_more"]
                cursor = result["cursor"]

                progress = int(10 + (collected / max_count) * 85)
                self._update_task_progress(task_id, progress, result_count=collected)

                await asyncio.sleep(0.3)

            self._update_task_progress(task_id, 100, result_count=collected, status="completed")
            logger.info(f"采集评论完成: {work_id}, 共 {collected} 条")

        except Exception as e:
            logger.error(f"采集评论失败: {e}")
            self._update_task_progress(task_id, 100, status="failed")
        finally:
            db.close()

    def start_task(self, task_id: int, task_type: str, params: dict) -> asyncio.Task:
        """启动采集任务"""
        async def run_task():
            if task_type == "work":
                await self.collect_work(task_id, params.get("work_id"))
            elif task_type == "user_works":
                await self.collect_user_works(
                    task_id, params.get("sec_uid"), params.get("max_count", 100)
                )
            elif task_type == "user_by_url":
                await self.collect_user_by_url(
                    task_id, params.get("sec_uid")
                )
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

        task = asyncio.create_task(run_task())
        self._running_tasks[task_id] = task
        return task

    def cancel_task(self, task_id: int):
        """取消任务"""
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]
            self._update_task_progress(task_id, 100, status="failed")


collector = CollectorService()


def get_collector() -> CollectorService:
    """获取采集服务实例"""
    return collector
