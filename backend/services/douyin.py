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

    def _parse_work_info(self, work: dict) -> dict:
        """解析作品信息"""
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
            "work_id": work.get("aweme_id", ""),
            "work_url": f"https://www.douyin.com/video/{work.get('aweme_id', '')}",
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
        搜索作品
        
        :param keyword: 搜索关键字
        :param num: 搜索结果数量
        :param sort_type: 排序方式 0 综合排序, 1 最多点赞, 2 最新发布
        :param publish_time: 发布时间 0 不限, 1 一天内, 7 一周内, 180 半年内
        :param filter_duration: 视频时长 空字符串 不限, 0-1 一分钟内, 1-5 1-5分钟内, 5-10000 5分钟以上
        :param search_range: 搜索范围 0 不限, 1 最近看过, 2 还未看过, 3 关注的人
        :param content_type: 内容形式 0 不限, 1 视频, 2 图文
        """
        if not self.auth:
            logger.error("未初始化认证信息")
            return None
        try:
            logger.info(f"[搜索服务] 开始搜索: keyword='{keyword}', num={num}, sort_type={sort_type}, publish_time={publish_time}, filter_duration={filter_duration}, search_range={search_range}, content_type={content_type}")
            
            work_list = DouyinAPI.search_some_general_work(
                self.auth, keyword, num, sort_type, publish_time,
                filter_duration, search_range, content_type
            )
            
            if work_list:
                logger.info(f"[搜索服务] API返回原始数据: {len(work_list)} 条")
                
                valid_count = sum(1 for w in work_list if w.get("aweme_info"))
                logger.info(f"[搜索服务] 包含aweme_info的有效数据: {valid_count} 条")
                
                if work_list:
                    first_item = work_list[0]
                    logger.debug(f"[搜索服务] 第一条数据结构: aweme_info存在={bool(first_item.get('aweme_info'))}")
                    if first_item.get("aweme_info"):
                        aweme_info = first_item["aweme_info"]
                        author = aweme_info.get("author", {})
                        logger.debug(f"[搜索服务] 作者数据: uid={author.get('uid')}, nickname={author.get('nickname')}")
                
                parsed_works = [self._parse_work_info(w.get("aweme_info", {}))
                             for w in work_list if w.get("aweme_info")]
                logger.info(f"[搜索服务] 解析后作品数量: {len(parsed_works)} 条")
                
                return {
                    "works": parsed_works,
                    "total": len(work_list),
                }
            else:
                logger.warning(f"[搜索服务] API返回空数据: keyword='{keyword}'")
        except Exception as e:
            logger.error(f"[搜索服务] 搜索作品失败: {e}")
        return None

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
