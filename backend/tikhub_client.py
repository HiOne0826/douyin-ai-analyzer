"""
TikHub API 客户端
封装抖音和小红书内容获取接口
"""
import os
import re
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()

class TikHubClient:
    def __init__(self):
        self.api_key = os.getenv("TIKHUB_API_KEY")
        self.base_url = os.getenv("TIKHUB_BASE_URL", "https://api.tikhub.io")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = 30

    def _extract_douyin_id(self, url: str) -> Optional[str]:
        """从抖音链接提取作品ID"""
        # 首先从文本中提取URL
        url_match = re.search(r'https?://[^\s]+', url)
        if url_match:
            url = url_match.group(0)
        
        # 处理搜索页modal_id格式
        modal_match = re.search(r'modal_id=(\d+)', url)
        if modal_match:
            return modal_match.group(1)
            
        # 处理短链接
        if 'v.douyin.com' in url or 'douyin.com/video/' in url or 'douyin.com/search/' in url:
            # 先尝试获取重定向后的真实链接
            try:
                response = requests.get(url, allow_redirects=True, timeout=10)
                url = response.url
            except Exception as e:
                print(f"链接解析失败: {e}")
        
        # 匹配作品ID
        patterns = [
            r'douyin\.com/video/(\d+)',
            r'iesdouyin\.com/item/(\d+)',
            r'aweme_id=(\d+)',
            r'/share/video/(\d+)',
            r'modal_id=(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    def _extract_xiaohongshu_id(self, url: str) -> Optional[str]:
        """从小红书链接提取笔记ID"""
        patterns = [
            r'xiaohongshu\.com/discovery/item/([a-zA-Z0-9]+)',
            r'xiaohongshu\.com/item/([a-zA-Z0-9]+)',
            r'xhslink\.com/([a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    def _extract_aweme_detail(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从 TikHub 响应中提取 aweme_detail，兼容不同接口的返回结构"""
        inner = data.get('data', {})
        if not isinstance(inner, dict):
            return None
        # web 接口: data.aweme_detail (dict)
        detail = inner.get('aweme_detail')
        if detail and isinstance(detail, dict):
            return detail
        # app v3 接口: data.aweme_details (list)
        details = inner.get('aweme_details')
        if details and isinstance(details, list) and len(details) > 0:
            return details[0]
        return None

    def get_douyin_video(self, url: str, need_anchor_info: bool = False) -> Dict[str, Any]:
        """获取抖音单个作品数据，返回已提取的 aweme_detail"""
        aweme_id = self._extract_douyin_id(url)

        # 按优先级尝试多个接口，统一提取 aweme_detail 后返回
        endpoints_to_try = []

        if aweme_id:
            endpoints_to_try.append(("/api/v1/douyin/web/fetch_one_video", {"aweme_id": aweme_id}))
            endpoints_to_try.append(("/api/v1/douyin/app/v3/fetch_one_video", {"aweme_id": aweme_id}))

        # 分享链接接口作为兜底
        endpoints_to_try.append(("/api/v1/douyin/web/fetch_one_video_by_share_url", {"share_url": url}))

        last_error = None
        for endpoint, params in endpoints_to_try:
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                detail = self._extract_aweme_detail(data)
                if detail:
                    return detail
            except Exception as e:
                last_error = e
                continue

        raise Exception(f"获取抖音数据失败: 所有接口均未返回有效数据 (last error: {last_error})")

    def get_xiaohongshu_note(self, url: str) -> Dict[str, Any]:
        """获取小红书笔记数据，返回已提取的笔记详情"""
        note_id = self._extract_xiaohongshu_id(url)
        if not note_id:
            raise ValueError(f"无法解析小红书链接: {url}")

        endpoints_to_try = [
            "/api/v1/xiaohongshu/web/note/detail",
            "/api/v1/xiaohongshu/app/note/detail",
            "/api/v1/xiaohongshu/web/v2/note/detail",
        ]

        last_error = None
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    params={"note_id": note_id},
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                # 小红书接口通常返回 data.data.items[0] 或 data.data.note_detail
                inner = data.get('data', {})
                if isinstance(inner, dict):
                    # 尝试多种嵌套结构
                    for key in ['note_detail', 'items', 'data']:
                        val = inner.get(key)
                        if val and isinstance(val, dict):
                            return val
                        if val and isinstance(val, list) and len(val) > 0:
                            return val[0]
                    # 如果 inner 本身就有 note_id，说明已经是详情
                    if inner.get('note_id') or inner.get('title'):
                        return inner
                # 如果顶层 data 直接就是详情
                if data.get('note_id') or data.get('title'):
                    return data
            except Exception as e:
                last_error = e
                continue

        raise Exception(f"获取小红书数据失败: {last_error}")

    def get_douyin_user_videos(self, user_url: str, limit: int = 5) -> Dict[str, Any]:
        """获取抖音用户最近作品"""
        # 提取用户sec_uid
        if 'douyin.com/user/' in user_url:
            match = re.search(r'douyin\.com/user/([a-zA-Z0-9_-]+)', user_url)
            if match:
                sec_uid = match.group(1)
            else:
                raise ValueError(f"无法解析抖音用户链接: {user_url}")
        else:
            # 处理短链接
            try:
                response = requests.head(user_url, allow_redirects=True, timeout=10)
                user_url = response.url
                match = re.search(r'douyin\.com/user/([a-zA-Z0-9_-]+)', user_url)
                if not match:
                    raise ValueError(f"无法解析抖音用户链接: {user_url}")
                sec_uid = match.group(1)
            except Exception as e:
                raise ValueError(f"无法解析抖音用户链接: {str(e)}")

        endpoint = "/api/v1/douyin/web/fetch_user_posts"
        params = {
            "sec_uid": sec_uid,
            "count": limit
        }

        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"获取抖音用户作品失败: {str(e)}")

    def get_xiaohongshu_user_notes(self, user_url: str, limit: int = 5) -> Dict[str, Any]:
        """获取小红书用户最近笔记"""
        # 提取用户ID
        patterns = [
            r'xiaohongshu\.com/user/profile/([a-zA-Z0-9]+)',
            r'xiaohongshu\.com/user/([a-zA-Z0-9]+)',
        ]
        
        user_id = None
        for pattern in patterns:
            match = re.search(pattern, user_url)
            if match:
                user_id = match.group(1)
                break
        
        if not user_id:
            # 处理短链接
            try:
                response = requests.head(user_url, allow_redirects=True, timeout=10)
                user_url = response.url
                for pattern in patterns:
                    match = re.search(pattern, user_url)
                    if match:
                        user_id = match.group(1)
                        break
            except Exception as e:
                pass
        
        if not user_id:
            raise ValueError(f"无法解析小红书用户链接: {user_url}")

        endpoint = "/api/v1/xiaohongshu/web/v2/user/notes"
        params = {
            "user_id": user_id,
            "page_size": limit
        }

        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"获取小红书用户笔记失败: {str(e)}")

    def parse_url(self, url: str) -> Dict[str, Any]:
        """自动解析链接类型并获取数据"""
        if 'douyin.com' in url or 'iesdouyin.com' in url or 'v.douyin.com' in url:
            # 判断是作品链接还是用户链接
            if '/user/' in url or '/profile/' in url:
                return {
                    "type": "douyin_user",
                    "data": self.get_douyin_user_videos(url)
                }
            else:
                return {
                    "type": "douyin_video",
                    "data": self.get_douyin_video(url)
                }
        elif 'xiaohongshu.com' in url or 'xhslink.com' in url:
            # 判断是笔记链接还是用户链接
            if '/user/' in url or '/profile/' in url:
                return {
                    "type": "xiaohongshu_user",
                    "data": self.get_xiaohongshu_user_notes(url)
                }
            else:
                return {
                    "type": "xiaohongshu_note",
                    "data": self.get_xiaohongshu_note(url)
                }
        else:
            raise ValueError("不支持的URL类型，仅支持抖音和小红书链接")

# 单例实例
tikhub_client = TikHubClient()
