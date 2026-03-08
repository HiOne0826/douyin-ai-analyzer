import os
import re
import uuid
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
import sqlite3
from PIL import Image
import io
import base64

# 导入自定义模块
from tikhub_client import tikhub_client
from doubao_client import doubao_client

# 加载环境变量
load_dotenv()

# 初始化配置
app = FastAPI(title="AI社交媒体内容分析系统API")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局配置
TEMP_MEDIA_DIR = os.getenv("TEMP_MEDIA_DIR", "./temp_media")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 20))
RATE_LIMIT = f"{os.getenv('RATE_LIMIT_PER_MINUTE', 5)}/minute"
VOLC_ACCESS_KEY = os.getenv("VOLC_ACCESS_KEY")
VOLC_SECRET_KEY = os.getenv("VOLC_SECRET_KEY")

# 创建必要目录
os.makedirs(TEMP_MEDIA_DIR, exist_ok=True)
os.makedirs("./data", exist_ok=True)

# 数据库初始化
def init_db():
    conn = sqlite3.connect('./data/analysis_records.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS analysis_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_uuid TEXT,
            task_type TEXT,
            source_url TEXT,
            raw_data_json TEXT,
            ai_analysis TEXT,
            geo_blog_md TEXT,
            slug TEXT,
            seo_title TEXT,
            seo_desc TEXT,
            candidate_for_blog BOOLEAN DEFAULT 0,
            is_public BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 请求模型
class AnalysisRequest(BaseModel):
    url: str
    user_uuid: Optional[str] = None
    prompt: Optional[str] = None
    task_type: str = "single_content"

# 工具函数
def download_media(url: str, task_id: str) -> Optional[str]:
    """下载媒体文件并处理，返回base64编码图片。仅支持图片格式。"""
    try:
        response = requests.get(url, stream=True, timeout=30, headers={
            "Referer": "https://www.douyin.com/",
            "User-Agent": "Mozilla/5.0"
        })
        response.raise_for_status()

        # 检查文件大小
        content_length = int(response.headers.get('content-length', 0))
        if content_length > MAX_FILE_SIZE_MB * 1024 * 1024:
            return None

        content_type = response.headers.get('content-type', '')

        # 仅处理图片，不支持视频
        if 'image' in content_type or not content_type:
            img = Image.open(io.BytesIO(response.content))
            img.thumbnail((1024, 1024))
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            return f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode()}"

        return None

    except Exception as e:
        print(f"下载媒体文件失败: {e}")
        return None

def fetch_tikhub_data(url: str) -> Dict[str, Any]:
    """从TikHub API获取抖音/小红书数据"""
    try:
        result = tikhub_client.parse_url(url)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取第三方数据失败: {str(e)}")

def slim_raw_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """精简原始数据，只保留分析所需的关键字段"""
    data = raw_data.get('data', {})
    result = {"type": raw_data.get("type")}

    if raw_data.get('type') == 'douyin_video':
        stats = data.get('statistics', {})
        result["data"] = {
            "aweme_id": data.get("aweme_id"),
            "desc": data.get("desc"),
            "author": data.get("author", {}).get("nickname"),
            "digg_count": stats.get("digg_count", 0),
            "comment_count": stats.get("comment_count", 0),
            "collect_count": stats.get("collect_count", 0),
            "share_count": stats.get("share_count", 0),
            "image_count": len(data.get("images") or []),
        }
    elif raw_data.get('type') == 'xiaohongshu_note':
        interact = data.get('interact_info', data.get('statistics', {}))
        result["data"] = {
            "note_id": data.get("note_id"),
            "title": data.get("title"),
            "desc": data.get("desc"),
            "author": (data.get("user") or data.get("author", {})).get("nickname") if isinstance(data.get("user") or data.get("author"), dict) else None,
            "liked_count": interact.get("liked_count", interact.get("digg_count", 0)),
            "collected_count": interact.get("collected_count", interact.get("collect_count", 0)),
            "comment_count": interact.get("comment_count", 0),
        }
    else:
        result["data"] = str(data)[:2000]

    return result


def extract_image_urls(raw_data: Dict[str, Any], max_images: int = 3) -> list:
    """从原始数据中提取图片URL，最多 max_images 张，不处理视频"""
    data = raw_data.get('data', {})
    urls = []

    if raw_data.get('type') == 'douyin_video':
        images = data.get('images')
        if images and isinstance(images, list):
            for img in images[:max_images]:
                u = img.get('url_list', [None])[0]
                if u:
                    urls.append(u)
        # 没有图片时用封面（图文作品没有封面需求，视频不处理）
        if not urls:
            cover = data.get('video', {}).get('cover', {}).get('url_list', [])
            if cover:
                urls.append(cover[0])
    elif raw_data.get('type') == 'xiaohongshu_note':
        image_list = data.get('image_list', data.get('images', []))
        for img in (image_list or [])[:max_images]:
            u = img.get('url_list', [None])[0] or img.get('url', '')
            if u:
                urls.append(u)

    return urls


def call_doubao_api(prompt: str, image_base64_list: Optional[list] = None) -> StreamingResponse:
    """调用豆包API进行分析，支持多图，流式返回结果"""
    return StreamingResponse(doubao_client.chat_stream(prompt, image_base64_list), media_type="text/event-stream")

# 新增请求模型
class FetchRequest(BaseModel):
    url: str
    user_uuid: Optional[str] = None

class AnalyzeRequest(BaseModel):
    raw_data: Dict[str, Any]
    user_uuid: Optional[str] = None
    prompt: Optional[str] = None
    task_type: str = "single_content"

# API接口
@app.get("/")
async def root():
    return {"status": "ok", "message": "AI社交媒体内容分析系统API"}

@app.post("/api/fetch")
@limiter.limit(RATE_LIMIT)
async def fetch_content(request: Request, fetch_request: FetchRequest):
    """获取抖音/小红书内容数据"""
    try:
        # 验证并提取URL
        input_text = fetch_request.url.strip()
        url_match = re.search(r'https?://[^\s\n\r]+', input_text)
        if not url_match:
            raise HTTPException(status_code=400, detail="未检测到有效链接，请输入包含抖音/小红书链接的内容")
        
        extract_url = url_match.group(0)
        
        # 验证是否为抖音或小红书链接
        if not ('douyin.com' in extract_url or 'xiaohongshu.com' in extract_url or 'xhslink.com' in extract_url):
            raise HTTPException(status_code=400, detail="不支持的URL类型，仅支持抖音和小红书链接")
        
        # 获取第三方数据
        raw_data = fetch_tikhub_data(input_text)
        return raw_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取内容失败: {str(e)}")

@app.post("/api/analyze")
@limiter.limit(RATE_LIMIT)
async def analyze_content(request: Request, analyze_request: AnalyzeRequest):
    """分析已获取的内容"""
    task_id = str(uuid.uuid4())

    try:
        raw_data = analyze_request.raw_data

        # 下载前3张图片
        image_urls = extract_image_urls(raw_data, max_images=3)
        image_base64_list = []
        for img_url in image_urls:
            b64 = download_media(img_url, task_id)
            if b64:
                image_base64_list.append(b64)

        # 精简数据构造 prompt
        slim = slim_raw_data(raw_data)
        base_prompt = """请分析以下社交媒体内容，给出结构化的分析报告，包括：
1. 基础数据总结
2. 内容亮点分析
3. 受众画像推测
4. 可优化建议
5. 同类内容对标参考

内容数据：
{raw_data}
"""
        prompt = base_prompt.format(raw_data=json.dumps(slim, indent=2, ensure_ascii=False))
        if analyze_request.prompt:
            prompt += f"\n用户补充要求：\n{analyze_request.prompt}\n"

        return call_doubao_api(prompt, image_base64_list or None)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@app.post("/api/analyze/account")
@limiter.limit(RATE_LIMIT)
async def analyze_account(request: Request, analysis_request: AnalysisRequest):
    """分析账号"""
    # TODO: 实现账号对标分析逻辑
    return {"status": "pending", "message": "账号分析功能开发中"}

@app.get("/api/public/cases")
async def get_public_cases(page: int = 1, limit: int = 10):
    """获取公开的案例列表"""
    offset = (page - 1) * limit
    conn = sqlite3.connect('./data/analysis_records.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, slug, seo_title, seo_desc, created_at 
        FROM analysis_records 
        WHERE is_public = 1 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    records = c.fetchall()
    conn.close()
    
    cases = []
    for record in records:
        cases.append({
            "id": record[0],
            "slug": record[1],
            "title": record[2],
            "description": record[3],
            "created_at": record[4]
        })
    
    return cases

@app.get("/api/public/cases/{slug}")
async def get_case_detail(slug: str):
    """获取公开案例详情"""
    conn = sqlite3.connect('./data/analysis_records.db')
    c = conn.cursor()
    c.execute('''
        SELECT seo_title, seo_desc, geo_blog_md, created_at 
        FROM analysis_records 
        WHERE slug = ? AND is_public = 1
    ''', (slug,))
    record = c.fetchone()
    conn.close()
    
    if not record:
        raise HTTPException(status_code=404, detail="案例不存在")
    
    return {
        "title": record[0],
        "description": record[1],
        "content": record[2],
        "created_at": record[3]
    }

@app.get("/api/sitemap.xml")
async def get_sitemap():
    """生成sitemap.xml"""
    conn = sqlite3.connect('./data/analysis_records.db')
    c = conn.cursor()
    c.execute('''
        SELECT slug, updated_at 
        FROM analysis_records 
        WHERE is_public = 1
    ''')
    records = c.fetchall()
    conn.close()
    
    # 构造sitemap
    base_url = "https://your-domain.com"
    urls = [f"{base_url}/cases/{record[0]}" for record in records]
    
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
'''
    for url in urls:
        xml += f'''
    <url>
        <loc>{url}</loc>
        <lastmod>{datetime.now().isoformat()}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
'''
    xml += '</urlset>'
    
    return StreamingResponse(io.BytesIO(xml.encode()), media_type="application/xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
