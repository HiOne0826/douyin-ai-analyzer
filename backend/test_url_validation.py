"""
测试URL验证
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re

app = FastAPI()

class FetchRequest(BaseModel):
    url: str
    user_uuid: str | None = None

def validate_url(url: str) -> str:
    """验证并提取URL"""
    # 从文本中提取URL
    url_match = re.search(r'https?://[^\s\n\r]+', url)
    if not url_match:
        raise HTTPException(status_code=400, detail="未检测到有效链接，请输入包含抖音/小红书链接的内容")
    
    extract_url = url_match.group(0)
    
    # 验证是否为抖音或小红书链接
    if not ('douyin.com' in extract_url or 'xiaohongshu.com' in extract_url or 'xhslink.com' in extract_url):
        raise HTTPException(status_code=400, detail="不支持的URL类型，仅支持抖音和小红书链接")
    
    return extract_url

# 测试用例
test_cases = [
    "5.84 GvS:/ s@e.Bt 03/17 胶片感拉满，每一帧都是故事# 夜景写真# 发光发丝# 氛围感美女# 写真分享# 摄影 https://v.douyin.com/vVffsVkLWbs/ 复制此链接，打开Dou音搜索，直接观看视频！",
    "https://v.douyin.com/vVffsVkLWbs/",
    "https://www.xiaohongshu.com/discovery/item/123456",
    "这是一段没有链接的文本",
    "https://www.baidu.com"
]

print("测试URL验证功能...")
print("=" * 80)

for text in test_cases:
    print(f"\n输入: {text[:100]}...")
    try:
        url = validate_url(text)
        print(f"✅ 验证通过: {url}")
    except HTTPException as e:
        print(f"❌ 验证失败: {e.detail}")
