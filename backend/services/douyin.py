"""
抖音 API 服务封装
"""
import json
import uuid
import urllib
from typing import Optional, List, Dict, Any
from datetime import datetime

from loguru import logger

import requests
requests.packages.urllib3.disable_warnings()

from backend.core.dy_apis.douyin_api import DouyinAPI
from backend.core.builder.auth import DouyinAuth
from backend.core.utils.dy_util import trans_cookies


class DouyinService:
    """抖音 API 服务 - 封装原始 DouyinAPI"""

    def __init__(self, cookie_str: str = ""):
        self.cookie_str = cookie_str
        self.cookie = trans_cookies(cookie_str) if cookie_str else {}
        self.auth = None
        if cookie_str:
            self.auth = DouyinAuth()
            self.auth.perepare_auth(cookie_str)

    def get_user_info(self, sec_uid: str) -> Optional[dict]:
        """获取用户信息"""
        if not self.auth:
            logger.error("未初始化认证信息")
            return None
        try:
            user_url = f"https://www.douyin.com/user/{sec_uid}"
            result = DouyinAPI.get_user_info(self.auth, user_url)
            if result and result.get("user"):
                return self._parse_user_info(result["user"])
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
        return None

    def _parse_user_info(self, user: dict) -> dict:
        """解析用户信息"""
        sec_uid = user.get("sec_uid", "")
        return {
            "uid": user.get("uid", ""),
            "sec_uid": sec_uid,
            "unique_id": user.get("unique_id", ""),
            "nickname": user.get("nickname", ""),
            "avatar": user.get("avatar_thumb", {}).get("url_list", [""])[0],
            "signature": user.get("signature", ""),
            "gender": user.get("gender", 0),
            "age": user.get("user_age"),
            "follower_count": user.get("follower_count", 0),
            "following_count": user.get("following_count", 0),
            "aweme_count": user.get("aweme_count", 0),
            "total_favorited": user.get("total_favorited", 0),
            "ip_location": user.get("ip_label", ""),
            "user_url": f"https://www.douyin.com/user/{sec_uid}" if sec_uid else "",
        }

    def get_user_works(self, sec_uid: str, max_cursor: int = 0,
                       count: int = 20) -> Optional[dict]:
        """获取用户作品列表"""
        if not self.auth:
            logger.error("未初始化认证信息")
            return None
        try:
            user_url = f"https://www.douyin.com/user/{sec_uid}"
            result = DouyinAPI.get_user_work_info(self.auth, user_url, str(max_cursor))
            if result:
                return {
                    "works": [self._parse_work_info(w) for w in result.get("aweme_list", [])],
                    "has_more": result.get("has_more", False),
                    "max_cursor": result.get("max_cursor", 0),
                }
        except Exception as e:
            logger.error(f"获取用户作品失败: {e}")
        return None

    def get_work_info(self, work_url: str) -> Optional[dict]:
        """获取作品详情"""
        if not self.auth:
            logger.error("未初始化认证信息")
            return None
        try:
            result = DouyinAPI.get_work_info(self.auth, work_url)
            if result and result.get("aweme_detail"):
                return self._parse_work_info(result["aweme_detail"])
        except Exception as e:
            logger.error(f"获取作品详情失败: {e}")
        return None

    def _parse_work_info(self, work: dict) -> Optional[dict]:
        """解析作品信息"""
        if not work:
            return None
        
        aweme_id = work.get("aweme_id", "")
        if not aweme_id:
            logger.warning("[解析作品] 缺少aweme_id，跳过")
            return None
        
        video_url = ""
        cover_url = ""
        if work.get("video"):
            video_data = work["video"]
            play_addr = video_data.get("play_addr", {})
            url_list = play_addr.get("url_list", [])
            if url_list:
                video_url = url_list[0]
            cover = video_data.get("cover", {})
            cover_url_list = cover.get("url_list", [])
            if cover_url_list:
                cover_url = cover_url_list[0]
            logger.debug(f"解析视频: video_url={video_url[:50] if video_url else 'None'}...")

        images = []
        if work.get("images"):
            for img in work["images"]:
                url_list = img.get("url_list", [])
                if url_list:
                    images.append(url_list[0])
            if images and not cover_url:
                cover_url = images[0]
            logger.debug(f"解析图集: 共{len(images)}张图片")

        topics = []
        if work.get("text_extra"):
            for tag in work["text_extra"]:
                if tag.get("hashtag_name"):
                    topics.append(tag["hashtag_name"])

        author = work.get("author", {})
        statistics = work.get("statistics", {})

        if not author.get("uid"):
            logger.warning(f"[解析作品] 作品 {aweme_id} 缺少作者信息，跳过")
            return None

        logger.debug(f"作者信息: uid={author.get('uid')}, nickname={author.get('nickname')}, follower_count={author.get('follower_count')}")

        aweme_type = work.get("aweme_type", 0)
        work_type = "video"
        if aweme_type == 68:
            work_type = "image"
        elif aweme_type == 0:
            work_type = "video"

        sec_uid = author.get("sec_uid", "")
        user_url = f"https://www.douyin.com/user/{sec_uid}" if sec_uid else ""

        ip_location = ""
        if work.get("user"):
            ip_location = work["user"].get("ip_location", "") or work["user"].get("ip_label", "")

        return {
            "work_id": aweme_id,
            "work_url": f"https://www.douyin.com/video/{aweme_id}",
            "work_type": work_type,
            "title": work.get("desc", ""),
            "description": work.get("desc", ""),
            "video_url": video_url,
            "cover_url": cover_url,
            "images": images,
            "digg_count": statistics.get("digg_count", 0),
            "comment_count": statistics.get("comment_count", 0),
            "collect_count": statistics.get("collect_count", 0),
            "share_count": statistics.get("share_count", 0),
            "admire_count": statistics.get("admire_count", 0),
            "topics": topics,
            "create_time": datetime.fromtimestamp(work.get("create_time", 0)),
            "author": {
                "uid": author.get("uid", ""),
                "sec_uid": sec_uid,
                "unique_id": author.get("unique_id", ""),
                "nickname": author.get("nickname", ""),
                "avatar": author.get("avatar_thumb", {}).get("url_list", [""])[0],
                "signature": author.get("signature", ""),
                "gender": author.get("gender", 0),
                "age": author.get("user_age"),
                "follower_count": author.get("follower_count", 0),
                "following_count": author.get("following_count", 0),
                "aweme_count": author.get("aweme_count", 0),
                "total_favorited": author.get("total_favorited", 0),
                "ip_location": ip_location,
                "user_url": user_url,
            }
        }

    def get_work_comments(self, work_id: str, cursor: int = 0,
                          count: int = 20) -> Optional[dict]:
        """获取作品评论"""
        if not self.auth:
            logger.error("未初始化认证信息")
            return None
        try:
            result = DouyinAPI.get_work_comments(self.auth, work_id, cursor, count)
            if result:
                return {
                    "comments": [self._parse_comment(c) for c in result.get("comments", [])],
                    "has_more": result.get("has_more", False),
                    "cursor": result.get("cursor", 0),
                    "total": result.get("total", 0),
                }
        except Exception as e:
            logger.error(f"获取评论失败: {e}")
        return None

    def _parse_comment(self, comment: dict) -> dict:
        """解析评论"""
        user = comment.get("user", {})
        return {
            "comment_id": comment.get("cid", ""),
            "content": comment.get("text", ""),
            "digg_count": comment.get("digg_count", 0),
            "create_time": datetime.fromtimestamp(comment.get("create_time", 0)),
            "user": {
                "uid": user.get("uid", ""),
                "nickname": user.get("nickname", ""),
                "avatar": user.get("avatar_thumb", {}).get("url_list", [""])[0],
            }
        }

    def search_works(self, keyword: str, num: int = 20,
                     sort_type: str = '0', publish_time: str = '0',
                     filter_duration: str = "", search_range: str = "",
                     content_type: str = "") -> Optional[dict]:
        """
        搜索作品 - 保证返回指定数量的有效数据
        
        :param keyword: 搜索关键字
        :param num: 目标有效作品数量（保证采集到这么多条有效数据）
        :param sort_type: 排序方式 0 综合排序, 1 最多点赞, 2 最新发布
        :param publish_time: 发布时间 0 不限, 1 一天内, 7 一周内, 180 半年内
        :param filter_duration: 视频时长 空字符串 不限, 0-1 一分钟内, 1-5 1-5分钟内, 5-10000 5分钟以上
        :param search_range: 搜索范围 0 不限, 1 最近看过, 2 还未看过, 3 关注的人
        :param content_type: 内容形式 0 不限, 1 视频, 2 图文
        """
        if not self.auth:
            logger.error("未初始化认证信息")
            return None
        
        from backend.core.dy_apis.douyin_api import DouyinAPI
        from backend.core.utils.dy_util import generate_uifid, generate_search_id
        import time
        import random
        
        offset = "0"
        cursor = 0
        parsed_works = []
        raw_work_list = []
        request_count = 0
        max_requests = 50
        max_retry = 3
        retry_count = 0
        consecutive_empty = 0
        max_consecutive_empty = 3
        
        search_id = generate_search_id()
        uifid = generate_uifid()
        
        logger.info(f"[搜索服务] 开始搜索: keyword='{keyword}', 目标有效数量: {num}")
        
        while len(parsed_works) < num and request_count < max_requests:
            request_count += 1
            
            try:
                res_json = DouyinAPI.search_general_work(
                    self.auth, keyword, sort_type, publish_time, offset,
                    filter_duration, search_range, content_type, cursor,
                    search_id=search_id, uifid=uifid
                )
            except Exception as e:
                logger.error(f"[搜索服务] 第{request_count}次请求失败: {e}")
                retry_count += 1
                if retry_count <= max_retry:
                    time.sleep(random.uniform(2, 4))
                    continue
                else:
                    break
            
            works = res_json.get("data", [])
            has_more = res_json.get("has_more", 0)
            search_nil_info = res_json.get("search_nil_info", {})
            
            if res_json.get("search_id"):
                search_id = res_json.get("search_id")
            
            logger.debug(f"[搜索服务] 第{request_count}次请求: offset={offset}, 返回{len(works)}条原始数据")
            
            if len(works) == 0:
                if search_nil_info.get("search_nil_type") == "verify_check":
                    retry_count += 1
                    if retry_count <= max_retry:
                        wait_time = random.uniform(3, 6)
                        logger.warning(f"[搜索服务] 触发验证，第{retry_count}次重试，等待{wait_time:.1f}秒...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.warning(f"[搜索服务] 已达最大重试次数({max_retry})，停止搜索")
                        break
                
                consecutive_empty += 1
                if consecutive_empty >= max_consecutive_empty:
                    logger.warning(f"[搜索服务] 连续{consecutive_empty}次返回空数据，停止搜索")
                    break
                
                if has_more != 1:
                    logger.info(f"[搜索服务] 无更多数据，停止搜索")
                    break
                
                cursor = res_json.get("cursor", cursor + 10)
                offset = str(len(raw_work_list))
                time.sleep(random.uniform(1, 2))
                continue
            
            retry_count = 0
            consecutive_empty = 0
            raw_work_list.extend(works)
            
            valid_count_this_round = 0
            for w in works:
                aweme_info = w.get("aweme_info", {})
                parsed = self._parse_work_info(aweme_info)
                if parsed:
                    parsed_works.append(parsed)
                    valid_count_this_round += 1
                else:
                    logger.debug(f"[搜索服务] 跳过无效作品: aweme_id={aweme_info.get('aweme_id', 'unknown')}")
            
            logger.info(f"[搜索服务] 第{request_count}次请求: 原始{len(works)}条 -> 有效{valid_count_this_round}条, 累计有效{len(parsed_works)}条")
            
            if has_more != 1:
                logger.info(f"[搜索服务] 无更多数据(has_more={has_more})，当前有效{len(parsed_works)}条")
                break
            
            if len(parsed_works) >= num:
                break
            
            cursor = res_json.get("cursor", cursor + 10)
            offset = str(len(raw_work_list))
            
            wait_time = random.uniform(1.5, 3)
            logger.debug(f"[搜索服务] 等待{wait_time:.1f}秒后继续翻页...")
            time.sleep(wait_time)
        
        if len(parsed_works) > num:
            parsed_works = parsed_works[:num]
        
        logger.info(f"[搜索服务] 搜索完成: 关键词='{keyword}', 共请求{request_count}次, 原始数据{len(raw_work_list)}条, 有效作品{len(parsed_works)}条")
        
        return {
            "works": parsed_works,
            "total": len(parsed_works),
            "raw_total": len(raw_work_list),
            "requests": request_count,
        }

    def search_users(self, keyword: str, num: int = 20,
                     douyin_user_fans: str = "", douyin_user_type: str = "") -> Optional[dict]:
        """搜索用户

        Args:
            keyword: 搜索关键词
            num: 搜索数量
            douyin_user_fans: 粉丝数量筛选 - 空不限, 0_1k(1k以下), 1k_1w(1k-1w), 1w_10w(1w-10w), 10w_100w(10w-100w), 100w_(100w以上)
            douyin_user_type: 用户类型筛选 - 空不限, common_user(普通用户), enterprise_user(企业用户), personal_user(个人认证用户)
        """
        if not self.auth:
            logger.error("未初始化认证信息")
            return None
        try:
            user_list = DouyinAPI.search_some_user(
                self.auth, keyword, num,
                douyin_user_fans=douyin_user_fans,
                douyin_user_type=douyin_user_type
            )
            if user_list:
                return {
                    "users": [self._parse_search_user(u) for u in user_list],
                    "total": len(user_list),
                }
        except Exception as e:
            logger.error(f"搜索用户失败: {e}")
        return None

    def _parse_search_user(self, user_data: dict) -> dict:
        """解析搜索结果中的用户信息"""
        user = user_data.get("user_info", {})
        return {
            "uid": user.get("uid", ""),
            "sec_uid": user.get("sec_uid", ""),
            "nickname": user.get("nickname", ""),
            "avatar": user.get("avatar_thumb", {}).get("url_list", [""])[0],
            "signature": user.get("signature", ""),
            "follower_count": user.get("follower_count", 0),
            "aweme_count": user.get("aweme_count", 0),
            "ip_location": user.get("ip_label", ""),
        }

    def get_user_followers(self, uid: str, sec_uid: str, num: int = 50) -> Optional[dict]:
        """获取用户粉丝列表"""
        if not self.auth:
            logger.error("未初始化认证信息")
            return None
        try:
            logger.info(f"[粉丝列表] 开始获取: uid={uid}, sec_uid={sec_uid}, num={num}")
            result = DouyinAPI.get_some_user_follower_list(self.auth, uid, sec_uid, num)
            if result:
                return {
                    "followers": result,
                    "total": len(result),
                    "has_more": len(result) >= num,
                }
        except Exception as e:
            logger.error(f"获取粉丝列表失败: {e}")
        return None

    def get_user_followings(self, uid: str, sec_uid: str, num: int = 50) -> Optional[dict]:
        """获取用户关注列表"""
        if not self.auth:
            logger.error("未初始化认证信息")
            return None
        try:
            logger.info(f"[关注列表] 开始获取: uid={uid}, sec_uid={sec_uid}, num={num}")
            result = DouyinAPI.get_some_user_following_list(self.auth, uid, sec_uid, num)
            if result:
                return {
                    "followings": result,
                    "total": len(result),
                    "has_more": len(result) >= num,
                }
        except Exception as e:
            logger.error(f"获取关注列表失败: {e}")
        return None

    def get_work_comments_full(self, work_id: str, cursor: int = 0, count: int = 20) -> Optional[dict]:
        """获取作品评论（完整版，包含回复）"""
        if not self.auth:
            logger.error("未初始化认证信息")
            return None
        try:
            logger.info(f"[评论采集] 开始获取: work_id={work_id}, cursor={cursor}, count={count}")
            result = DouyinAPI.get_work_comments(self.auth, work_id, cursor, count)
            if result:
                comments = []
                for c in result.get("comments", []):
                    comment_data = self._parse_comment(c)
                    reply_count = c.get("reply_comment_total", 0)
                    comment_data["reply_count"] = reply_count
                    comments.append(comment_data)
                
                return {
                    "comments": comments,
                    "has_more": result.get("has_more", False),
                    "cursor": result.get("cursor", 0),
                    "total": result.get("total", 0),
                }
        except Exception as e:
            logger.error(f"获取评论失败: {e}")
        return None

    def get_comment_replies(self, work_id: str, comment_id: str, cursor: int = 0, count: int = 20) -> Optional[dict]:
        """获取评论回复"""
        if not self.auth:
            logger.error("未初始化认证信息")
            return None
        try:
            logger.info(f"[评论回复] 开始获取: work_id={work_id}, comment_id={comment_id}")
            comment = {"aweme_id": work_id, "cid": comment_id}
            result = DouyinAPI.get_work_inner_comment(self.auth, comment, str(cursor), str(count))
            if result:
                replies = [self._parse_comment(r) for r in result.get("comments", [])]
                return {
                    "replies": replies,
                    "has_more": result.get("has_more", False),
                    "cursor": result.get("cursor", 0),
                }
        except Exception as e:
            logger.error(f"获取评论回复失败: {e}")
        return None
