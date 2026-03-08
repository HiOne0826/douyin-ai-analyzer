'use client';

import { useState, useRef, useEffect } from 'react';

export default function Home() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [rawData, setRawData] = useState<any>(null);
  const [result, setResult] = useState('');
  const [mediaUrls, setMediaUrls] = useState<string[]>([]);
  const [customPrompt, setCustomPrompt] = useState('');
  const [userUuid, setUserUuid] = useState('');
  const resultRef = useRef<HTMLDivElement>(null);

  // 初始化用户UUID
  useEffect(() => {
    let uuid = localStorage.getItem('user_uuid');
    if (!uuid) {
      uuid = crypto.randomUUID();
      localStorage.setItem('user_uuid', uuid);
    }
    setUserUuid(uuid);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const inputText = url.trim();
    if (!inputText) return;
    
    // 从文本中提取URL
    const urlMatch = inputText.match(/https?:\/\/[^\s\n\r]+/);
    const extractUrl = urlMatch ? urlMatch[0] : inputText;
    
    if (!extractUrl) {
      setResult('❌ 未检测到有效链接，请输入包含抖音/小红书链接的内容');
      return;
    }

    setLoading(true);
    setResult('');
    setRawData(null);
    setMediaUrls([]);

    try {
      const response = await fetch('/api/fetch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: inputText,
          user_uuid: userUuid,
        }),
      });

      if (!response.ok) {
        throw new Error('请求失败');
      }

      const data = await response.json();
      setRawData(data);
      
      // 格式化显示内容
      let displayText = '✅ 内容获取成功！\n\n';
      displayText += '📝 基础信息：\n';
      if (data.type === 'douyin_video') {
        const video = data.data;
        const stats = video.statistics || {};
        displayText += `- 作品ID: ${video.aweme_id || '未知'}\n`;
        displayText += `- 作者: ${video.author?.nickname || '未知'}\n`;
        displayText += `- 文案: ${video.desc || '无'}\n`;
        displayText += `- 获赞: ${stats.digg_count || 0}\n`;
        displayText += `- 评论: ${stats.comment_count || 0}\n`;
        displayText += `- 收藏: ${stats.collect_count || 0}\n`;
        displayText += `- 转发: ${stats.share_count || 0}\n`;
        // 媒体信息
        const images = video.images;
        const coverUrl = video.video?.cover?.url_list?.[0] || video.video?.origin_cover?.url_list?.[0];
        const urls: string[] = [];
        if (images && images.length > 0) {
          images.forEach((img: any) => {
            const u = img.url_list?.[0];
            if (u) urls.push(u);
          });
        } else if (coverUrl) {
          urls.push(coverUrl);
        }
        setMediaUrls(urls);
      } else if (data.type === 'xiaohongshu_note') {
        const note = data.data;
        const stats = note.interact_info || note.statistics || {};
        displayText += `- 笔记ID: ${note.note_id || '未知'}\n`;
        displayText += `- 作者: ${note.user?.nickname || note.author?.nickname || '未知'}\n`;
        displayText += `- 标题: ${note.title || '无'}\n`;
        displayText += `- 内容: ${note.desc || '无'}\n`;
        displayText += `- 获赞: ${stats.liked_count || stats.digg_count || 0}\n`;
        displayText += `- 收藏: ${stats.collected_count || stats.collect_count || 0}\n`;
        displayText += `- 评论: ${stats.comment_count || 0}\n`;
        const imageList = note.image_list || note.images || [];
        if (imageList.length > 0) {
          const urls: string[] = [];
          imageList.forEach((img: any) => {
            const u = img.url_list?.[0] || img.url;
            if (u) urls.push(u);
          });
          setMediaUrls(urls);
        }
      }
      
      displayText += '\n👉 点击"AI分析"按钮进行深度分析';
      setResult(displayText);
      
    } catch (error) {
      setResult('❌ 内容获取失败，请稍后重试');
      console.error('获取错误:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!rawData) return;

    setAnalyzing(true);
    setResult('');

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          raw_data: rawData,
          user_uuid: userUuid,
          task_type: 'single_content',
          prompt: customPrompt.trim() || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error('请求失败');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          setResult(prev => prev + chunk);
          
          // 自动滚动到底部
          if (resultRef.current) {
            resultRef.current.scrollTop = resultRef.current.scrollHeight;
          }
        }
      }
    } catch (error) {
      setResult('分析失败，请稍后重试');
      console.error('分析错误:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="brutalist-card mb-12">
        <h2 className="text-3xl font-bold mb-6">输入抖音/小红书链接</h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://v.douyin.com/xxxxxx/ 或 https://www.xiaohongshu.com/discovery/item/xxxxxx"
              className="brutalist-input"
              disabled={loading}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="brutalist-button text-xl"
            >
              {loading ? '获取中...' : '获取内容'}
            </button>
            <button
              type="button"
              disabled={analyzing || !rawData}
              className="brutalist-button text-xl bg-gray-700 hover:bg-gray-600"
              onClick={handleAnalyze}
            >
              {analyzing ? '分析中...' : 'AI分析'}
            </button>
          </div>
          <div>
            <textarea
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="自定义提示词（可选）：例如「请重点分析封面构图和配色」「从运营角度给出改进建议」"
              className="brutalist-input min-h-[80px] resize-y"
              rows={3}
            />
          </div>
        </form>
      </div>

      {(result || mediaUrls.length > 0) && (
        <div className="brutalist-card">
          <h3 className="text-2xl font-bold mb-4">分析结果</h3>
          <div
            ref={resultRef}
            className="prose max-w-none max-h-[600px] overflow-y-auto p-4 bg-gray-50 border-2 border-black"
            dangerouslySetInnerHTML={{ __html: result.replace(/\n/g, '<br>') }}
          />
          {mediaUrls.length > 0 && (
            <div className="mt-4">
              <p className="font-bold mb-2">🖼️ 媒体预览 ({mediaUrls.length})</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {mediaUrls.map((src, i) => (
                  <img
                    key={i}
                    src={src}
                    alt={`媒体 ${i + 1}`}
                    className="w-full h-auto border-2 border-black object-cover"
                    referrerPolicy="no-referrer"
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-12">
        <div className="brutalist-card">
          <h3 className="text-xl font-bold mb-4">功能特点</h3>
          <ul className="space-y-2 list-disc pl-5">
            <li>支持抖音和小红书内容分析</li>
            <li>AI深度解读内容亮点与不足</li>
            <li>提供专业的优化建议</li>
            <li>实时流式输出，打字机效果</li>
          </ul>
        </div>
        <div className="brutalist-card">
          <h3 className="text-xl font-bold mb-4">即将上线</h3>
          <ul className="space-y-2 list-disc pl-5">
            <li>账号对标分析功能</li>
            <li>批量内容分析</li>
            <li>行业数据报告</li>
            <li>竞品动态监控</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
