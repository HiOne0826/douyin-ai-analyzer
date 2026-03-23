# 前端优化与 SSE 修复 — 执行文档

> 本文档包含 4 个优化任务，严格按顺序执行。每个任务标注了精确的文件、行号、要替换的代码和新代码。

---

## 诊断总结

| # | 问题 | 根因 | 严重度 |
|---|------|------|--------|
| 1 | 获取内容后结果显示在下方，缺乏引导 | 获取结果和 AI 分析结果共用同一个展示区域，用户不知道下一步该做什么 | 体验 |
| 2 | AI 分析按钮/自定义提示词不应在获取前就显示 | 所有控件始终可见，没有按流程分步展示 | 体验 |
| 3 | AI 分析结果和获取数据抢占同一个文本框 | `result` 状态变量被两个功能复用，`setResult('')` 清空了获取结果 | 体验 |
| 4 | 点击 AI 分析后没有流式输出 | 后端 `call_doubao_api()` 返回的不是 SSE 格式；前端也没有解析 SSE 协议；Next.js rewrite 代理缓冲了流式响应 | **功能阻断** |

---

## OPT-1：修复后端 SSE 流式输出（功能阻断，最高优先级）

**文件：** `backend/main.py`

### 问题分析

当前第 189-191 行的 `call_doubao_api()` 函数：
```python
def call_doubao_api(prompt: str, image_base64_list: Optional[list] = None) -> StreamingResponse:
    return StreamingResponse(doubao_client.chat_stream(prompt, image_base64_list), media_type="text/event-stream")
```

`doubao_client.chat_stream()` yield 的是纯文本 chunk（如 `"## 一、基础数据"`），但 `media_type` 声称是 `text/event-stream`（SSE 协议）。SSE 协议要求每条消息格式为 `data: 内容\n\n`。这个不匹配导致：
- Next.js rewrite 代理看到 `text/event-stream` 但内容不符合 SSE 格式，可能缓冲整个响应
- 前端 `reader.read()` 收到的要么是空的（被缓冲），要么是一次性全部内容

### 操作步骤

**步骤 A — 替换 `call_doubao_api` 函数（第 189-191 行）为 SSE 包装生成器：**

将：
```python
def call_doubao_api(prompt: str, image_base64_list: Optional[list] = None) -> StreamingResponse:
    """调用豆包API进行分析，支持多图，流式返回结果"""
    return StreamingResponse(doubao_client.chat_stream(prompt, image_base64_list), media_type="text/event-stream")
```

替换为：
```python
def call_doubao_api(prompt: str, image_base64_list: Optional[list] = None) -> StreamingResponse:
    """调用豆包API进行分析，支持多图，SSE 流式返回结果"""
    def sse_generator():
        for chunk in doubao_client.chat_stream(prompt, image_base64_list):
            # 按 SSE 协议格式包装每个 chunk
            yield f"data: {chunk}\n\n"
        # 发送结束标记
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
```

**关键变化说明：**
1. 新增 `sse_generator()` 内部函数，将每个纯文本 chunk 包装为 `data: {chunk}\n\n` 格式
2. 流结束后发送 `data: [DONE]\n\n` 标记，前端据此判断流结束
3. 添加 `Cache-Control: no-cache` 防止代理缓存
4. 添加 `X-Accel-Buffering: no` 告诉 Nginx 不要缓冲此响应（生产环境关键）
5. 添加 `Connection: keep-alive` 保持长连接

**步骤 B — 同时修改 `/api/analyze` 路由的返回方式（第 286 行）：**

当前第 286 行：
```python
        return call_doubao_api(prompt, image_base64_list or None)
```

这行不需要改，因为 `call_doubao_api` 已经修复。但需要确认第 244-247 行的图片校验逻辑不会误拦截：

当前代码强制要求 `selected_image_indexes` 非空，否则返回 400 错误。如果内容没有图片（比如纯文字抖音视频），用户无法选择图片，就永远无法触发分析。

**将第 244-247 行：**
```python
        # 验证选中的图片
        if not selected_indexes or len(selected_indexes) == 0:
            raise HTTPException(status_code=400, detail="请至少选择1张图片进行分析")
```

**替换为：**
```python
        # 图片为可选项，没有图片也可以进行纯文本分析
```

**同时将第 260-262 行：**
```python
        if not image_urls:
            raise HTTPException(status_code=400, detail="选中的图片无效，请重新选择")
```

**替换为：**
```python
        # image_urls 可能为空（纯文本内容），不阻断分析流程
```

### 验证方式

1. 启动后端：`cd backend && uvicorn main:app --reload`
2. 用 curl 测试 SSE 输出：
```bash
curl -N -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"raw_data": {"type": "douyin_video", "data": {"desc": "测试内容", "statistics": {"digg_count": 100}}}, "selected_image_indexes": []}'
```
3. 确认输出逐行出现，每行格式为 `data: 文本内容`，最后一行为 `data: [DONE]`

---

## OPT-2：前端 SSE 解析修复 + Next.js 代理流式透传

**涉及文件：**
- `frontend/app/page.tsx`（SSE 读取逻辑）
- `frontend/next.config.js`（rewrite 代理配置）

### 问题分析

两个问题叠加导致前端收不到流式数据：

**问题 A — 前端没有解析 SSE 协议：**
当前 `page.tsx` 第 150-165 行直接将 `reader.read()` 的原始 chunk 拼接到 `result`：
```typescript
const chunk = decoder.decode(value);
setResult(prev => prev + chunk);
```
OPT-1 修复后，后端发送的是 `data: 文本内容\n\n` 格式。如果前端不去掉 `data: ` 前缀，用户会看到 `data: ## 📊 一、基础数据概览` 这样的原始协议文本。

**问题 B — Next.js rewrite 代理默认缓冲响应：**
当前 `next.config.js` 的 rewrite 规则将 `/api/*` 代理到 `localhost:8000`。Next.js 的内置代理默认会缓冲响应体，等全部接收完毕后才转发给浏览器，导致流式效果完全丧失。需要在 fetch 请求中直接使用后端地址绕过 Next.js 代理，或者改用浏览器原生 `EventSource`。

**选择方案：** 改用浏览器直连后端的方式发起 SSE 请求（开发环境 `localhost:8000`，生产环境通过 Nginx `/api/` 路径）。这样绕过 Next.js rewrite 的缓冲问题，同时 Nginx 已配置 `proxy_buffering off`，天然支持 SSE 透传。

### 操作步骤

**步骤 A — 在 `frontend/app/page.tsx` 顶部（第 3 行 import 之后）添加 API 基础地址常量：**

在第 3 行之后插入：
```typescript
// API 基础地址：开发环境直连后端，生产环境走 Nginx 代理（不经过 Next.js rewrite）
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || ''
```

> 说明：
> - 开发环境在 `.env.local` 中设置 `NEXT_PUBLIC_API_BASE=http://localhost:8000`，直连后端
> - 生产环境不设置此变量（或设为空），请求走相对路径 `/api/...`，由 Nginx 代理到后端（Nginx 已配置 `proxy_buffering off`）

**步骤 B — 创建 `frontend/.env.local` 文件（如果不存在）：**

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

**步骤 C — 修改 `handleSubmit` 函数中的 fetch URL（第 48 行）：**

将：
```typescript
      const response = await fetch('/api/fetch', {
```

替换为：
```typescript
      const response = await fetch(`${API_BASE}/api/fetch`, {
```

**步骤 D — 重写 `handleAnalyze` 函数的 SSE 读取逻辑（替换第 124-173 行整个函数）：**

将当前的 `handleAnalyze` 函数：
```typescript
  const handleAnalyze = async () => {
    if (!rawData) return;

    setAnalyzing(true);
    setResult('');
    setActiveTab('result');

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
          selected_image_indexes: selectedImageIndexes,
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
```

替换为：
```typescript
  const handleAnalyze = async () => {
    if (!rawData) return;

    setAnalyzing(true);
    setAnalysisResult('');
    setActiveTab('analysis');

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
        setAnalysisResult(`❌ ${err.detail || '分析失败'}`);
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
            const trimmed = line.trim();
            if (!trimmed) continue;                    // 空行跳过
            if (trimmed === 'data: [DONE]') continue;  // 结束标记跳过
            if (trimmed.startsWith('data: ')) {
              const content = trimmed.slice(6);         // 去掉 "data: " 前缀
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
    }
  };
```

**关键变化说明：**
1. fetch URL 改用 `${API_BASE}/api/analyze`，绕过 Next.js rewrite 缓冲
2. 引入 `buffer` 变量处理跨 chunk 的不完整行（TCP 分包可能把一行 SSE 数据拆成两个 chunk）
3. 按 `\n` 分割后逐行解析，只提取 `data: ` 前缀后的实际内容
4. 忽略空行和 `data: [DONE]` 结束标记
5. 使用 `decoder.decode(value, { stream: true })` 确保多字节 UTF-8 字符不被截断
6. 错误响应尝试解析 JSON 获取 `detail` 字段，给用户更有用的错误信息
7. 使用 `setAnalysisResult` 而非 `setResult`（这是 OPT-3 将引入的独立状态变量，用于分离获取结果和分析结果。**如果先执行 OPT-2 再执行 OPT-3，此处暂时保持 `setResult`，等 OPT-3 再统一改名**）

> **⚠️ 执行顺序提示：** 如果你先执行 OPT-2，上面代码中的 `setAnalysisResult` 和 `setActiveTab('analysis')` 暂时改为 `setResult` 和 `setActiveTab('result')`。等 OPT-3 执行时会统一重命名。或者先执行 OPT-3 再执行 OPT-2，则直接使用上面的代码。

### 验证方式

1. 启动后端：`cd backend && uvicorn main:app --reload`
2. 启动前端：`cd frontend && npm run dev`
3. 在页面中输入一个抖音链接，点击"获取内容"
4. 选择图片后点击"AI 分析"
5. **预期效果：** 分析结果区域应逐字/逐句出现文本，而非等待数秒后一次性显示全部内容
6. 打开浏览器 DevTools → Network → 找到 `/api/analyze` 请求 → 查看 Response 标签，应看到 `data: ` 前缀的逐行数据

### 如果仍然不流式，排查清单

| 检查项 | 排查方法 |
|--------|----------|
| 后端是否真的在流式输出？ | 用 `curl -N` 直接请求后端 `http://localhost:8000/api/analyze`，观察是否逐行输出 |
| Next.js rewrite 是否在缓冲？ | 确认 `NEXT_PUBLIC_API_BASE` 已设置为 `http://localhost:8000`，前端直连后端 |
| Nginx 是否在缓冲？（生产环境） | 确认 nginx.conf 中 `location /api/` 包含 `proxy_buffering off;` |
| 豆包 API 是否在流式返回？ | 在 `doubao_client.py` 的 `chat_stream` 方法中加 `print(f"chunk: {content}")` 调试 |

---

## OPT-3A：状态分离 + 分步流程逻辑

**文件：** `frontend/app/page.tsx`

### 问题分析

当前 `result` 状态变量被"获取内容"和"AI 分析"两个功能共用：
- `handleSubmit` 成功后将格式化的获取信息写入 `setResult(displayText)`（第 114 行）
- `handleAnalyze` 开始时执行 `setResult('')`（第 128 行），清空了获取结果
- 用户点击 AI 分析后，获取到的基础信息消失，体验割裂

**解决方案：** 将 `result` 拆分为 `fetchInfo`（获取结果）和 `analysisResult`（AI 分析结果），并引入 `step` 状态控制 UI 流程。

### 操作步骤

**步骤 A — 替换状态声明（第 6-16 行）：**

将：
```typescript
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [rawData, setRawData] = useState<any>(null)
  const [result, setResult] = useState('')
  const [mediaUrls, setMediaUrls] = useState<string[]>([])
  const [customPrompt, setCustomPrompt] = useState('')
  const [userUuid, setUserUuid] = useState('')
  const [activeTab, setActiveTab] = useState('result')
  const [selectedImageIndexes, setSelectedImageIndexes] = useState<number[]>([])
  const resultRef = useRef<HTMLDivElement>(null)
```

替换为：
```typescript
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [rawData, setRawData] = useState<any>(null)
  const [fetchInfo, setFetchInfo] = useState('')
  const [analysisResult, setAnalysisResult] = useState('')
  const [mediaUrls, setMediaUrls] = useState<string[]>([])
  const [customPrompt, setCustomPrompt] = useState('')
  const [userUuid, setUserUuid] = useState('')
  const [activeTab, setActiveTab] = useState('result')
  const [selectedImageIndexes, setSelectedImageIndexes] = useState<number[]>([])
  const [step, setStep] = useState<'input' | 'fetched' | 'analyzing' | 'done'>('input')
  const resultRef = useRef<HTMLDivElement>(null)
```

**关键变化说明：**
1. `result` → 拆分为 `fetchInfo`（存储获取结果文本）和 `analysisResult`（存储 AI 分析文本）
2. 新增 `step` 状态，控制 UI 分步展示：
   - `'input'`：初始状态，只显示输入区域
   - `'fetched'`：获取成功，显示获取结果 + 图片选择 + AI 分析按钮
   - `'analyzing'`：AI 分析中，显示流式输出区域
   - `'done'`：分析完成

---

**步骤 B — 修改 `handleSubmit` 函数（第 28-122 行）：**

在函数内部，将所有 `setResult` 替换为 `setFetchInfo`，并在成功/失败时设置 `step`。

**B-1：将第 38-39 行：**
```typescript
      setResult('❌ 未检测到有效链接，请输入包含抖音/小红书链接的内容')
      return
```

替换为：
```typescript
      setFetchInfo('❌ 未检测到有效链接，请输入包含抖音/小红书链接的内容')
      return
```

**B-2：将第 42-45 行：**
```typescript
    setLoading(true)
    setResult('')
    setRawData(null)
    setMediaUrls([])
```

替换为：
```typescript
    setLoading(true)
    setFetchInfo('')
    setAnalysisResult('')
    setRawData(null)
    setMediaUrls([])
    setSelectedImageIndexes([])
    setStep('input')
```

**B-3：将第 113-114 行：**
```typescript
      displayText += '\n👉 点击"AI分析"按钮进行深度分析';
      setResult(displayText);
```

替换为：
```typescript
      displayText += '\n👉 选择图片后点击"AI分析"按钮进行深度分析';
      setFetchInfo(displayText);
      setStep('fetched');
```

**B-4：将第 117 行：**
```typescript
      setResult('❌ 内容获取失败，请稍后重试');
```

替换为：
```typescript
      setFetchInfo('❌ 内容获取失败，请稍后重试');
```

---

**步骤 C — 修改 `handleAnalyze` 函数（第 124-173 行）：**

> **⚠️ 注意：** 如果已经执行了 OPT-2，`handleAnalyze` 已经被替换为 SSE 解析版本。以下修改基于 OPT-2 之后的代码。如果尚未执行 OPT-2，请先执行 OPT-2。

将 `handleAnalyze` 函数中的状态操作替换：

**C-1：将函数开头的状态设置：**
```typescript
    setAnalyzing(true);
    setResult('');
    setActiveTab('result');
```

替换为：
```typescript
    setAnalyzing(true);
    setAnalysisResult('');
    setStep('analyzing');
```

> 如果已执行 OPT-2，这几行可能已经是 `setAnalysisResult('')` 和 `setActiveTab('analysis')`，则只需将 `setActiveTab('analysis')` 改为 `setStep('analyzing')`。

**C-2：将流式读取中的 `setResult` 替换为 `setAnalysisResult`：**

如果尚未执行 OPT-2，将：
```typescript
          setResult(prev => prev + chunk);
```

替换为：
```typescript
          setAnalysisResult(prev => prev + chunk);
```

> 如果已执行 OPT-2，此处应该已经是 `setAnalysisResult`，无需修改。

**C-3：将 catch 中的错误提示：**
```typescript
      setResult('分析失败，请稍后重试');
```

替换为：
```typescript
      setAnalysisResult('❌ 分析失败，请稍后重试');
```

> 如果已执行 OPT-2，此处应该已经是 `setAnalysisResult('❌ 分析失败，请稍后重试')`，无需修改。

**C-4：在 `finally` 块中添加 step 更新：**

将：
```typescript
    } finally {
      setAnalyzing(false);
    }
```

替换为：
```typescript
    } finally {
      setAnalyzing(false);
      setStep('done');
    }
```

---

**步骤 D — 修改"重新分析"按钮的重置逻辑（第 321-328 行）：**

将：
```typescript
              <button
                onClick={() => {
                  setUrl('')
                  setResult('')
                  setRawData(null)
                  setMediaUrls([])
                  setSelectedImageIndexes([])
                  setActiveTab('result')
                }}
```

替换为：
```typescript
              <button
                onClick={() => {
                  setUrl('')
                  setFetchInfo('')
                  setAnalysisResult('')
                  setRawData(null)
                  setMediaUrls([])
                  setSelectedImageIndexes([])
                  setStep('input')
                }}
```

---

**步骤 E — 在结果展示区域中，将 `result` 引用替换为对应的新状态变量：**

**E-1：将第 236 行的条件渲染：**
```typescript
      {(result || mediaUrls.length > 0) && (
```

替换为：
```typescript
      {(fetchInfo || analysisResult || mediaUrls.length > 0) && (
```

**E-2：将第 270 行的结果显示：**
```typescript
                  {result}
```

替换为：
```typescript
                  {analysisResult || fetchInfo}
```

> 说明：优先显示 AI 分析结果，如果没有则显示获取信息。这是临时方案，OPT-3B 会将两者放到独立区域。

### 验证方式

1. 启动前后端
2. 输入链接点击"获取内容" → 应显示获取结果，`step` 变为 `'fetched'`
3. 点击"AI 分析" → 分析结果应逐步出现，获取结果不会被清空（虽然当前 UI 暂时只显示一个，但状态已分离）
4. 点击"重新分析" → 所有状态清空，回到初始状态

### 状态流转图

```
[input] --获取成功--> [fetched] --点击AI分析--> [analyzing] --分析完成--> [done]
   ^                                                                        |
   |__________________________ 点击"重新分析" ______________________________|
```

---

## OPT-4：UI/体验深度优化 + Markdown渲染 + 预置提示词
### 问题清单
| # | 问题 | 优化方向 |
|---|------|----------|
| 1 | 基础数据和AI分析结果共用同一个文本框，互相覆盖 | 拆分为两个独立模块，分步骤展示 |
| 2 | 获取内容和AI分析模块同时显示，流程不清晰 | 按步骤切换显示，获取成功后才显示分析模块 |
| 3 | AI分析结果不支持Markdown渲染，阅读体验差 | 引入Markdown渲染组件，支持格式、代码块、列表等 |
| 4 | 缺少默认提示词，每次都需要手动输入 | 预置人像摄影分析专用提示词，支持自定义修改 |

### 最佳实践
1. **分步UI设计**：采用卡片式分步导航，每个步骤只显示当前需要的操作区域，降低认知负担
2. **Markdown渲染**：使用`react-markdown`组件，配合语法高亮，支持所有标准Markdown格式
3. **提示词模板**：预置常用行业提示词模板，支持用户保存自定义模板，提升使用效率
4. **内容分区**：基础数据区和分析结果区采用不同背景色/边框区分，视觉层次清晰

---

## OPT-4 执行步骤
### 步骤1：安装Markdown渲染依赖
```bash
cd frontend
npm install react-markdown remark-gfm
```

### 步骤2：UI布局重构，分步骤显示
- 步骤1（初始状态）：只显示链接输入区域
- 步骤2（获取成功）：显示「基础信息」模块（包含获取到的基础数据、媒体预览），同时显示「AI分析」模块（包含提示词输入框、分析按钮）
- 步骤3（分析中/完成）：显示「AI分析结果」模块，基础信息模块折叠或保留在上方

### 步骤3：实现Markdown渲染功能
- 替换原纯文本展示为`react-markdown`组件
- 配置GFM（GitHub Flavored Markdown）支持，包括表格、任务列表、删除线等
- 添加自定义样式，适配新野兽派设计风格

### 步骤4：添加预置提示词
- 将人像摄影专用提示词预置到提示词输入框中
- 支持用户修改自定义提示词
