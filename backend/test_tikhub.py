"""
测试TikHub API连接
"""
from tikhub_client import tikhub_client

def test_douyin_video():
    """测试抖音视频获取"""
    print("测试抖音视频获取...")
    try:
        # 测试抖音链接
        url = "https://v.douyin.com/i8nFAf6q/"
        result = tikhub_client.get_douyin_video(url)
        print(f"✅ 抖音视频获取成功")
        print(f"  状态码: {result.get('code')}")
        print(f"  请求ID: {result.get('request_id')}")
        if 'data' in result and result['data']:
            video_data = result['data']
            print(f"  作品ID: {video_data.get('aweme_id')}")
            print(f"  作品描述: {video_data.get('desc', '')[:50]}...")
            print(f"  获赞数: {video_data.get('digg_count', 0)}")
            print(f"  评论数: {video_data.get('comment_count', 0)}")
        return True
    except Exception as e:
        print(f"❌ 抖音视频获取失败: {e}")
        return False

def test_xiaohongshu_note():
    """测试小红书笔记获取"""
    print("\n测试小红书笔记获取...")
    try:
        # 测试小红书链接
        url = "https://www.xiaohongshu.com/discovery/item/67d2a93b000000001b033b73"
        result = tikhub_client.get_xiaohongshu_note(url)
        print(f"✅ 小红书笔记获取成功")
        print(f"  状态码: {result.get('code')}")
        print(f"  请求ID: {result.get('request_id')}")
        if 'data' in result and result['data']:
            note_data = result['data']
            print(f"  笔记ID: {note_data.get('note_id')}")
            print(f"  笔记标题: {note_data.get('title', '')[:50]}...")
            print(f"  获赞数: {note_data.get('liked_count', 0)}")
            print(f"  收藏数: {note_data.get('collected_count', 0)}")
        return True
    except Exception as e:
        print(f"❌ 小红书笔记获取失败: {e}")
        return False

def test_url_parser():
    """测试URL自动解析"""
    print("\n测试URL自动解析...")
    test_cases = [
        "https://v.douyin.com/i8nFAf6q/",
        "https://www.douyin.com/video/7337689275976431907",
        "https://www.xiaohongshu.com/discovery/item/67d2a93b000000001b033b73",
        "https://xhslink.com/abc123",
    ]
    
    for url in test_cases:
        try:
            result = tikhub_client.parse_url(url)
            print(f"✅ {url} -> {result['type']}")
        except Exception as e:
            print(f"❌ {url} -> 解析失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("TikHub API 连接测试")
    print("=" * 60)
    
    # 测试API Key是否配置
    if not tikhub_client.api_key or tikhub_client.api_key == "your_tikhub_api_key":
        print("❌ 请先在 .env 文件中配置 TIKHUB_API_KEY")
        exit(1)
    
    print(f"API Key 已配置: {'*' * 20}{tikhub_client.api_key[-8:]}")
    print(f"API 地址: {tikhub_client.base_url}")
    
    # 运行测试
    test_url_parser()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
