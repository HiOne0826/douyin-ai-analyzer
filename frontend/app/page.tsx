'use client'

import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// API 基础地址：开发环境直连后端，生产环境走 Nginx 代理（不经过 Next.js rewrite）
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || ''

// 预置提示词
const DEFAULT_PROMPT = `# Role: 高级人像摄影账号策略专家

## Task:
对指定的人像摄影图文帖进行深度解构，输出一份可复现、可落地的拆解报告。

## Constraints:
1. 严禁使用“构图精美”、“氛围感强”等虚词，必须细化到具体的摄影技术指标和文案逻辑。
2. 必须以“视觉传达”为核心，分析图片如何通过技术手段转化为用户情绪。

## Analysis Dimensions:

### 1. 视觉技术解构 (重点分析)
- 构图分析：使用了哪种构图法则（中心、三分、引导线等）？主体与环境的关系如何？
- 光影分析：主光方向（逆光、侧光、硬光/柔光）？如何通过光影塑造人物立体感或氛围？
- 色彩分析：色调分析（冷暖色调分布）、关键色彩（HSL）、胶片模拟/调色方向（如：日系、电影感、复古感）。
- 人物表现：模特的姿态（Pose）、情绪传达点、妆造与背景的匹配度。

### 2. 文案与运营逻辑
- 钩子分析：首图的哪一个视觉元素最吸粉？标题的前5个字如何建立“点击价值”？
- 内容结构：文案属于“攻略型”、“情绪型”还是“纯分享型”？
- 互动诱导：评论区是否有针对性的QA引导？

### 3. 第一性原理推导
- 核心竞争力：如果剥离模特颜值，该帖子的技术壁垒在哪里？
- 可复制路径：普通摄影师如何低成本复现该风格？（给出具体器材、场地、调色建议）

## Output Format:
[结构化Markdown输出，包含“核心亮点”、“技术参数推测”、“避坑建议”、“我的落地行动点”]`

export default function Home() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [rawData, setRawData] = useState<any>(null)
  const [fetchInfo, setFetchInfo] = useState('')
  const [analysisResult, setAnalysisResult] = useState('')
  const [mediaUrls, setMediaUrls] = useState<string[]>([])
  const [customPrompt, setCustomPrompt] = useState(DEFAULT_PROMPT)
  const [userUuid, setUserUuid] = useState('')
  const [activeTab, setActiveTab] = useState('result')
  const [selectedImageIndexes, setSelectedImageIndexes] = useState<number[]>([])
  const [step, setStep] = useState<'input' | 'fetched' | 'analyzing' | 'done'>('input')
  const resultRef = useRef<HTMLDivElement>(null)

  // 初始化用户UUID
  useEffect(() => {
    let uuid = localStorage.getItem('user_uuid')
    if (!uuid) {
      uuid = crypto.randomUUID()
      localStorage.setItem('user_uuid', uuid)
    }
    setUserUuid(uuid)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const inputText = url.trim()
    if (!inputText) return
    
    // 从文本中提取URL
    const urlMatch = inputText.match(/https?:\/\/[^\s\n\r]+/)
    const extractUrl = urlMatch ? urlMatch[0] : inputText
    
    if (!extractUrl) {
      setFetchInfo('❌ 未检测到有效链接，请输入包含抖音/小红书链接的内容')
      return
    }

    setLoading(true)
    setFetchInfo('')
    setAnalysisResult('')
    setRawData(null)
    setMediaUrls([])
    setSelectedImageIndexes([])
    setStep('input')

    try {
      const response = await fetch(`${API_BASE}/api/fetch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: inputText,
          user_uuid: userUuid,
        }),
      })

      if (!response.ok) {
        throw new Error('请求失败')
      }

      const data = await response.json()
      setRawData(data)
      
      // 格式化显示内容
      let displayText = '✅ 内容获取成功！\n\n'
      displayText += '📝 基础信息：\n'
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
      
      displayText += '\n👉 选择图片后点击"AI分析"按钮进行深度分析';
      setFetchInfo(displayText);
      setStep('fetched');
      
    } catch (error) {
      setFetchInfo('❌ 内容获取失败，请稍后重试');
      console.error('获取错误:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!rawData) return;

    setAnalyzing(true);
    setAnalysisResult('');
    setStep('analyzing');

    try {
      const response = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          raw_data: rawData,
          user_uuid: userUuid,
          task_type: 'single_content',
          prompt: customPrompt.trim() || undefined,
          selected_image_indexes: selectedImageIndexes,
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: '请求失败' }));
        setResult(`❌ ${err.detail || '分析失败'}`);
        return;
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // 按换行符分割，逐行解析 SSE 协议
          const lines = buffer.split('\n');
          // 最后一个元素可能是不完整的行，保留在 buffer
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.trim() === 'data: [DONE]') continue;  // 结束标记跳过
            if (line.startsWith('data: ')) {
              const content = line.slice(6) + '\n';         // 去掉 "data: " 前缀，保留换行符
              setAnalysisResult(prev => prev + content);
            }
          }

          // 自动滚动到底部
          if (resultRef.current) {
            resultRef.current.scrollTop = resultRef.current.scrollHeight;
          }
        }
      }
    } catch (error) {
      setAnalysisResult('❌ 分析失败，请稍后重试');
      console.error('分析错误:', error);
    } finally {
      setAnalyzing(false);
      setStep('done');
    }
  };

  return (
    <main className="bg-gray-50 text-dark min-h-screen">
      {/* Hero 区域 - 极简打底 + 野兽点睛 */}
      <section className="min-h-screen flex flex-col justify-center items-center px-6 py-20 bg-grid">
        <div className="max-w-3xl w-full text-center">
          <h1 className="font-mono text-5xl md:text-6xl font-bold mb-6">
            AI 内容分析工具
          </h1>
          <p className="text-xl text-gray-600 mb-12 leading-relaxed">
            输入抖音/小红书链接，AI 自动分析 8 个维度的数据，提供专业优化建议
          </p>

          {/* 输入表单 - 野兽风格卡片 */}
          <div className="card-neo p-8 text-left">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="font-mono font-bold block mb-3">作品链接</label>
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://v.douyin.com/xxxxxx/ 或 https://www.xiaohongshu.com/discovery/item/xxxxxx"
                  className="input-neo text-lg"
                  disabled={loading}
                />
              </div>

              <div className="grid grid-cols-1 gap-4">
                <button
                  type="submit"
                  disabled={loading || !url.trim()}
                  className="btn-neo btn-neo-primary disabled:opacity-50 disabled:hover:transform-none disabled:hover:shadow-none w-full"
                >
                  {loading ? '获取中...' : '获取内容'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </section>

      {/* 结果展示区域 */}
      {(fetchInfo || analysisResult || mediaUrls.length > 0) && (
        <section className="px-6 py-20 bg-white">
          <div className="max-w-5xl mx-auto space-y-8">
            {/* 基础信息模块 */}
            {fetchInfo && (
              <div className="card-neo p-6">
                <h3 className="font-mono text-2xl font-bold mb-4 flex items-center">
                  <span className="inline-block w-8 h-8 bg-blue-600 text-white text-center mr-3">📋</span>
                  基础信息
                </h3>
                <div className="font-mono text-sm leading-relaxed p-6 bg-gray-50 border-3 border-dark whitespace-pre-wrap">
                  {fetchInfo}
                </div>
              </div>
            )}

            {/* 媒体预览模块 */}
            {mediaUrls.length > 0 && (
              <div className="card-neo p-6">
                <h3 className="font-mono text-2xl font-bold mb-4 flex items-center">
                  <span className="inline-block w-8 h-8 bg-blue-600 text-white text-center mr-3">🖼️</span>
                  媒体预览 <span className="text-sm font-normal text-gray-600 ml-2">（已选中 {selectedImageIndexes.length}/3 张，点击选择分析用图）</span>
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
                  {mediaUrls.map((src, i) => {
                    const isSelected = selectedImageIndexes.includes(i);
                    return (
                    <div
                      key={i}
                      className={`cursor-pointer transition-all ${isSelected ? 'scale-105' : 'hover:scale-105'}`}
                      onClick={() => {
                        if (isSelected) {
                          // 取消选中
                          setSelectedImageIndexes(selectedImageIndexes.filter(idx => idx !== i))
                        } else {
                          // 新选中，最多3张
                          if (selectedImageIndexes.length < 3) {
                            setSelectedImageIndexes([...selectedImageIndexes, i])
                          }
                        }
                      }}
                    >
                      <img
                        src={src}
                        alt={`媒体 ${i + 1}`}
                        className={`w-full h-auto border-3 object-cover aspect-square ${isSelected ? 'border-blue-600 shadow-[0_0_0_4px_rgba(37,99,235,0.3)]' : 'border-dark'}`}
                        referrerPolicy="no-referrer"
                      />
                      {isSelected && (
                        <div className="text-center mt-1 text-xs font-mono font-bold text-blue-600">✓ 已选中</div>
                      )}
                    </div>
                  )})}
                </div>
              </div>
            )}

            {/* AI分析模块（获取成功后显示） */}
            {step === 'fetched' && (
              <div className="card-neo p-6">
                <h3 className="font-mono text-2xl font-bold mb-4 flex items-center">
                  <span className="inline-block w-8 h-8 bg-blue-600 text-white text-center mr-3">🤖</span>
                  AI分析设置
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="font-mono font-bold block mb-3">分析提示词</label>
                    <textarea
                      value={customPrompt}
                      onChange={(e) => setCustomPrompt(e.target.value)}
                      className="input-neo min-h-[200px] resize-y text-sm"
                      rows={8}
                    />
                  </div>
                  <button
                    type="button"
                    disabled={analyzing || selectedImageIndexes.length === 0}
                    className="btn-neo btn-neo-primary disabled:opacity-50 disabled:hover:transform-none disabled:hover:shadow-none w-full"
                    onClick={handleAnalyze}
                  >
                    {analyzing ? '分析中...' : `开始AI分析 (已选${selectedImageIndexes.length}张图)`}
                  </button>
                </div>
              </div>
            )}

            {/* AI分析中提示 */}
            {step === 'analyzing' && (
              <div className="card-neo p-6">
                <h3 className="font-mono text-2xl font-bold mb-4 flex items-center">
                  <span className="inline-block w-8 h-8 bg-blue-600 text-white text-center mr-3">🤖</span>
                  AI分析中
                </h3>
                <div className="p-12 bg-gray-50 border-3 border-dark text-center">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mb-4"></div>
                  <p className="font-mono text-lg">正在分析内容，请稍候...</p>
                  <p className="text-sm text-gray-600 mt-2">分析结果将逐字显示，请不要关闭页面</p>
                </div>
              </div>
            )}

            {/* AI分析结果模块 */}
            {analysisResult && step !== 'analyzing' && (
              <div className="card-neo p-6">
                <h3 className="font-mono text-2xl font-bold mb-4 flex items-center">
                  <span className="inline-block w-8 h-8 bg-blue-600 text-white text-center mr-3">📊</span>
                  AI分析结果
                </h3>
                <div
                  ref={resultRef}
                  className="prose prose-lg max-w-none p-6 bg-gray-50 border-3 border-dark max-h-[800px] overflow-y-auto"
                >
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    disallowedElements={[]}
                    unwrapDisallowed={false}
                    components={{
                      h1: ({children}) => <h1 className="text-2xl font-mono font-bold mt-6 mb-4 border-b-3 border-dark pb-2">{children}</h1>,
                      h2: ({children}) => <h2 className="text-xl font-mono font-bold mt-5 mb-3">{children}</h2>,
                      h3: ({children}) => <h3 className="text-lg font-mono font-bold mt-4 mb-2">{children}</h3>,
                      h4: ({children}) => <h4 className="text-base font-mono font-bold mt-3 mb-2">{children}</h4>,
                      p: ({children}) => <p className="mb-3 leading-relaxed">{children}</p>,
                      ul: ({children}) => <ul className="list-disc pl-8 mb-4 space-y-1" style={{listStyleType: 'disc'}}>{children}</ul>,
                      ol: ({children}) => <ol className="list-decimal pl-8 mb-4 space-y-1" style={{listStyleType: 'decimal'}}>{children}</ol>,
                      li: ({children}) => <li className="mb-1 pl-1">{children}</li>,
                      strong: ({children}) => <strong className="font-bold text-blue-600">{children}</strong>,
                      em: ({children}) => <em className="italic">{children}</em>,
                      del: ({children}) => <del className="line-through text-gray-500">{children}</del>,
                      code: ({inline, children}) => inline ?
                        <code className="bg-gray-200 px-2 py-0.5 rounded font-mono text-sm border border-gray-400">{children}</code> :
                        <pre className="bg-gray-900 text-white p-4 rounded overflow-x-auto font-mono text-sm mb-4 border-3 border-dark">{children}</pre>,
                      pre: ({children}) => <pre className="bg-gray-900 text-white p-4 rounded overflow-x-auto font-mono text-sm mb-4 border-3 border-dark">{children}</pre>,
                      blockquote: ({children}) => <blockquote className="border-l-4 border-blue-600 pl-4 bg-blue-50 py-2 pr-2 italic text-gray-700 mb-4 border-2 border-r-0 border-t-0 border-b-0 border-dark">{children}</blockquote>,
                      table: ({children}) => <div className="overflow-x-auto mb-4"><table className="w-full border-collapse border-3 border-dark">{children}</table></div>,
                      thead: ({children}) => <thead className="bg-gray-100">{children}</thead>,
                      tbody: ({children}) => <tbody>{children}</tbody>,
                      tr: ({children}) => <tr className="border-b-2 border-dark">{children}</tr>,
                      th: ({children}) => <th className="border-2 border-dark p-3 font-bold text-left">{children}</th>,
                      td: ({children}) => <td className="border-2 border-dark p-3">{children}</td>,
                      hr: () => <hr className="my-6 border-t-3 border-dark" />,
                      a: ({href, children}) => <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline font-bold">{children}</a>
                    }}
                  >
                    {analysisResult}
                  </ReactMarkdown>
                </div>
              </div>
            )}

            <div className="mt-8 flex justify-center">
              <button
                onClick={() => {
                  setUrl('')
                  setFetchInfo('')
                  setAnalysisResult('')
                  setRawData(null)
                  setMediaUrls([])
                  setSelectedImageIndexes([])
                  setStep('input')
                  setCustomPrompt(DEFAULT_PROMPT)
                }}
                className="btn-neo"
              >
                重新分析
              </button>
            </div>
          </div>
        </section>
      )}

      {/* 功能介绍区域 - 极简布局 + 野兽卡片 */}
      <section className="px-6 py-20 bg-gray-100">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-12 gap-4">
            <h2 className="font-mono text-3xl font-bold">功能特性</h2>
            <a 
              href="https://hione.one" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="btn-neo"
            >
              回到官网 →
            </a>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card-neo">
              <h3 className="font-mono text-xl font-bold mb-4">🤖 AI 深度分析</h3>
              <ul className="list-neo text-gray-600 font-mono text-sm">
                <li>8个维度数据拆解</li>
                <li>受众画像分析</li>
                <li>评论关键词提取</li>
                <li>情绪倾向分析</li>
                <li>爆文潜质评分</li>
              </ul>
            </div>
            <div className="card-neo">
              <h3 className="font-mono text-xl font-bold mb-4">💡 优化建议</h3>
              <ul className="list-neo text-gray-600 font-mono text-sm">
                <li>标题文案优化</li>
                <li>标签组合策略</li>
                <li>内容结构调整</li>
                <li>发布时间建议</li>
                <li>封面优化方向</li>
              </ul>
            </div>
            <div className="card-neo">
              <h3 className="font-mono text-xl font-bold mb-4">📊 数据支持</h3>
              <ul className="list-neo text-gray-600 font-mono text-sm">
                <li>抖音全量数据</li>
                <li>小红书图文/视频</li>
                <li>历史数据对比</li>
                <li>竞品账号分析</li>
                <li>趋势热点追踪</li>
              </ul>
            </div>
            <div className="card-neo">
              <h3 className="font-mono text-xl font-bold mb-4">⚡ 使用场景</h3>
              <ul className="list-neo text-gray-600 font-mono text-sm">
                <li>内容创作者</li>
                <li>新媒体运营</li>
                <li>MCN机构</li>
                <li>品牌方市场部</li>
                <li>电商直播运营</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 使用流程区域 */}
      <section className="px-6 py-20 bg-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="font-mono text-3xl font-bold mb-12">三步完成分析</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-blue-600 text-white font-mono font-bold text-2xl flex items-center justify-center border-3 border-dark shadow-neo">
                1
              </div>
              <h3 className="font-mono font-bold mb-2">粘贴链接</h3>
              <p className="text-gray-600 text-sm">复制抖音/小红书作品链接，粘贴到输入框</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-blue-600 text-white font-mono font-bold text-2xl flex items-center justify-center border-3 border-dark shadow-neo">
                2
              </div>
              <h3 className="font-mono font-bold mb-2">获取数据</h3>
              <p className="text-gray-600 text-sm">点击获取内容，系统自动爬取公开数据</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-blue-600 text-white font-mono font-bold text-2xl flex items-center justify-center border-3 border-dark shadow-neo">
                3
              </div>
              <h3 className="font-mono font-bold mb-2">AI分析</h3>
              <p className="text-gray-600 text-sm">一键生成专业分析报告和优化建议</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA 区域 */}
      <section className="px-6 py-20 bg-gray-100 bg-grid">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="font-mono text-3xl font-bold mb-6">开始提升你的内容数据</h2>
          <p className="text-xl text-gray-600 mb-8">
            已帮助 1000+ 创作者提升内容曝光率平均 300%
          </p>
          <a href="#" className="btn-neo btn-neo-primary text-lg px-8 py-4">
            免费试用 →
          </a>
        </div>
      </section>

      {/* 页脚 */}
      <footer className="px-6 py-10 bg-dark text-white text-center">
        <p className="font-mono">© 2026 hione.one</p>
        <p className="text-gray-400 text-sm mt-2">Made with vibe coding 🦞</p>
      </footer>
    </main>
  )
}
