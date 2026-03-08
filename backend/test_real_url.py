"""
测试真实抖音链接
"""
from tikhub_client import tikhub_client

def test_real_douyin_url():
    """测试真实抖音链接"""
    url = "https://v.douyin.com/B7Awe6wuTAg/"
    
    print(f"测试链接: {url}")
    print("=" * 80)
    
    try:
        # 提取ID
        aweme_id = tikhub_client._extract_douyin_id(url)
        print(f"提取到的作品ID: {aweme_id}")
        
        # 获取数据
        result = tikhub_client.get_douyin_video(url)
        print(f"\n✅ 获取成功!")
        print(f"状态码: {result.get('code')}")
        print(f"请求ID: {result.get('request_id')}")
        
        if 'data' in result and result['data']:
            data = result['data']
            print(f"\n📝 作品信息:")
            print(f"作品ID: {data.get('aweme_id')}")
            print(f"发布时间: {data.get('create_time')}")
            print(f"作品描述: {data.get('desc', '')[:100]}...")
            print(f"\n📊 数据统计:")
            print(f"获赞: {data.get('digg_count', 0)}")
            print(f"评论: {data.get('comment_count', 0)}")
            print(f"收藏: {data.get('collect_count', 0)}")
            print(f"转发: {data.get('share_count', 0)}")
            
            if 'author' in data:
                author = data['author']
                print(f"\n👤 作者信息:")
                print(f"昵称: {author.get('nickname')}")
                print(f"抖音号: {author.get('unique_id')}")
                print(f"粉丝数: {author.get('follower_count', 0)}")
            
            if 'video' in data:
                video = data['video']
                print(f"\n🎥 视频信息:")
                print(f"时长: {video.get('duration', 0)}秒")
                print(f"分辨率: {video.get('width')}x{video.get('height')}")
                if 'cover' in video:
                    print(f"封面链接: {video['cover'].get('url_list', [''])[0][:100]}...")
        
        # 保存完整响应到文件
        with open("test_response.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 完整响应已保存到 test_response.json")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 获取失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import json
    test_real_douyin_url()
