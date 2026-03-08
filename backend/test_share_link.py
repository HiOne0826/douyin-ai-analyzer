"""
测试分享链接解析
"""
from tikhub_client import tikhub_client
import re

def test_link_extraction():
    """测试不同格式的链接提取"""
    test_cases = [
        # 带文案的分享链接
        "5.84 GvS:/ s@e.Bt 03/17 胶片感拉满，每一帧都是故事# 夜景写真# 发光发丝# 氛围感美女# 写真分享# 摄影 https://v.douyin.com/vVffsVkLWbs/ 复制此链接，打开Dou音搜索，直接观看视频！",
        # 带换行的分享链接
        """5.84 GvS:/ s@e.Bt 03/17 胶片感拉满，每一帧都是故事# 夜景写真# 
发光发丝# 氛围感美女# 写真分享# 摄影 https://v.douyin.com/vVffsVkLWbs/ 
复制此链接，打开Dou音搜索，直接观看视频！""",
        # 纯链接
        "https://v.douyin.com/vVffsVkLWbs/",
        # 长链接
        "https://www.douyin.com/video/7337689275976431907",
        # 搜索页链接
        "https://www.douyin.com/search/%E7%BE%8E%E5%A5%B3%20%E5%9B%BE%E6%96%87?aid=9c600bdb-053d-4025-a64e-1a38bd49d1e5&modal_id=7530842093288590627&type=general"
    ]
    
    print("测试链接提取功能...")
    print("=" * 80)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"输入: {text[:100]}..." if len(text) > 100 else f"输入: {text}")
        
        # 提取URL
        url_match = re.search(r'https?://[^\s\n\r]+', text)
        if url_match:
            url = url_match.group(0)
            print(f"提取到URL: {url}")
            
            # 提取ID
            aweme_id = tikhub_client._extract_douyin_id(text)
            print(f"提取到ID: {aweme_id}")
        else:
            print("❌ 未提取到URL")
    
    print("\n" + "=" * 80)
    print("测试真实API调用...")
    
    # 测试真实API调用
    share_text = "5.84 GvS:/ s@e.Bt 03/17 胶片感拉满，每一帧都是故事# 夜景写真# 发光发丝# 氛围感美女# 写真分享# 摄影 https://v.douyin.com/vVffsVkLWbs/ 复制此链接，打开Dou音搜索，直接观看视频！"
    
    try:
        result = tikhub_client.get_douyin_video(share_text)
        print(f"✅ API调用成功")
        print(f"状态码: {result.get('code')}")
        if 'data' in result and result['data']:
            data = result['data']
            print(f"作品ID: {data.get('aweme_id')}")
            print(f"文案: {data.get('desc', '')[:50]}...")
            print(f"获赞: {data.get('digg_count', 0)}")
    except Exception as e:
        print(f"❌ API调用失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_link_extraction()
