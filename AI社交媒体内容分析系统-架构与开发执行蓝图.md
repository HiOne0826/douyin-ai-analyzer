# AI 社交媒体内容分析系统 — 精细化实施蓝图 v2.0

> ⚠️ **致接手此文档的 AI 开发者 (Agent Instructions):**
> 本文档是该项目的**最高执行准则**。请严格按照任务编号顺序执行，每完成一个任务后向用户确认再继续。
> 项目运行于资源受限的个人轻量级云服务器（腾讯云轻量应用服务器）。
>
> **核心原则：** 极简主义、零冗余依赖、第一性原理驱动。
> - 绝对禁止引入重量级数据库（MySQL/PostgreSQL）
> - 绝对禁止引入外部云存储 SDK（AWS S3/阿里云 OSS）
> - 绝对禁止开发复杂的账号鉴权系统
> - 绝对禁止引入 UI 组件库（shadcn/ui、Ant Design、Material UI 等）
> - 所有前端组件必须手写，遵循新野兽派设计风格

---

## 目录

- [一、项目现状审计](#一项目现状审计)
- [二、技术栈与约束](#二技术栈与约束)
- [三、UI/UX 设计规范](#三uiux-设计规范)
- [四、数据库设计](#四数据库设计)
- [五、API 接口规范](#五api-接口规范)
- [六、Phase 2 实施任务清单](#六phase-2-实施任务清单)
- [七、Phase 3 实施任务清单](#七phase-3-实施任务清单)
- [八、Phase 4 生产部署与上线](#八phase-4-生产部署与上线)
- [九、基础设施安全机制](#九基础设施安全机制)

---

## 一、项目现状审计

### 1.1 已完成功能 ✅
- TikHub API 集成（抖音/小红书单条内容获取）
- 火山引擎豆包 API 客户端（流式 + 非流式）
- FastAPI 框架搭建（含限流中间件）
- 前端 Next.js 页面（新野兽派风格）
- SSE 流式输出接口
- SQLite 数据库表结构
- Docker + Docker Compose + Nginx 部署配置
- 媒体文件下载与 base64 压缩处理

### 1.2 已知缺陷（必须修复） 🔴

| # | 文件 | 问题 | 影响 |
|---|------|------|------|
| BUG-1 | `backend/requirements.txt` | 包含 `sqlite3`（Python 内置模块），pip install 会报错 | 部署失败 |
| BUG-2 | `backend/main.py` 第 235-271 行 | `/api/analyze` 接口分析完成后**没有将结果写入 SQLite** | 数据丢失，Workflow C 无数据可用 |
| BUG-3 | `backend/main.py` 第 336-339 行 | `/api/sitemap.xml` 查询了不存在的 `updated_at` 字段 | 接口 500 报错 |
| BUG-4 | `frontend/app/page.tsx` 第 148-163 行 | SSE 读取使用 `reader.read()` 直接拼接，没有解析 `data:` 前缀 | 流式输出内容包含 SSE 协议字符 |
| BUG-5 | `frontend/next.config.js` 第 14 行 | rewrite 目标是 `localhost:8000`，Docker 容器间应为 `backend:8000` | Docker 部署后前端 API 请求全部失败 |
| BUG-6 | `backend/Dockerfile` 第 24-28 行 | cron 守护进程未安装（slim 镜像不含 cron），且 `cron &&` 启动方式不可靠 | 定时清理和备份任务不执行 |
| BUG-7 | `frontend/app/page.tsx` | AI 分析结果是 Markdown 格式，但前端用 `whitespace-pre-wrap` 纯文本渲染 | 用户看到原始 Markdown 标记符号 |

### 1.3 未实现功能（按优先级排列）
1. 分析结果落库（Phase 2 前置条件）
2. 前端 Markdown 渲染
3. 账号对标分析（Workflow B）
4. 用户历史记录查看
5. `/cases/[slug]` 动态路由页面（GEO/SEO）
6. 后台管理接口（标记候选内容、发布 GEO 文章）
7. 高潜内容报告自动生成
8. Sitemap 自动更新
9. GitHub 同步与 CI/CD
10. HTTPS 证书配置

---

## 二、技术栈与约束

### 2.1 技术栈（锁定版本，禁止升级）

| 层 | 技术 | 版本 | 备注 |
|----|------|------|------|
| 前端框架 | Next.js (App Router) | 14.1.0 | 必须使用 SSR |
| 前端语言 | TypeScript + React | 18.x | |
| 样式 | Tailwind CSS | 3.3.x | 禁止引入组件库 |
| 后端框架 | FastAPI | 0.110.0 | |
| 后端语言 | Python | 3.11 | |
| 数据库 | SQLite 3 | 内置 | 单文件，禁止 MySQL/PG |
| 限流 | slowapi | 0.1.9 | |
| AI 模型 | 火山引擎豆包 | doubao-seed-2-0-lite | ARK API Key 直连 |
| 数据源 | TikHub API | v1 | |
| 容器 | Docker + Compose | 3.8 | |
| 反向代理 | Nginx | alpine | |

### 2.2 新增依赖（仅允许以下）

**前端新增：**
- `react-markdown` — Markdown 渲染（轻量，无重依赖）
- `remark-gfm` — 支持 GFM 表格/任务列表

**后端新增：**
- 无新增依赖

### 2.3 禁止事项清单
- ❌ 禁止使用 Redis、MongoDB、MySQL、PostgreSQL
- ❌ 禁止使用 AWS/阿里云/腾讯云 SDK
- ❌ 禁止使用 shadcn/ui、Ant Design、Material UI、Chakra UI
- ❌ 禁止使用 NextAuth、Passport 等认证库
- ❌ 禁止使用 Prisma、TypeORM、SQLAlchemy 等 ORM
- ❌ 禁止使用 WebSocket（用 SSE 替代）
- ❌ 禁止在前端直接调用第三方 API（所有外部请求必须经过后端中转）

---

## 三、UI/UX 设计规范

### 3.1 设计风格：极简主义 + 新野兽派 (Neo-Brutalism)

**核心视觉特征：**
- 高对比度：纯白背景 `#f9fafb` + 纯黑文字 `#1a1a1a`
- 粗黑边框：所有交互元素使用 `border: 3px solid #1a1a1a`
- 零圆角：所有元素 `border-radius: 0`
- 硬阴影：`box-shadow: 4px 4px 0px #1a1a1a`（静态），`6px 6px 0px #1a1a1a`（悬停）
- 字体：标题和代码用 `JetBrains Mono`，正文用 `Inter`
- 主色调：蓝色 `#2563eb` 用于主按钮和强调元素

### 3.2 已定义的 CSS 组件类（在 `globals.css` 中）

| 类名 | 用途 | 关键样式 |
|------|------|----------|
| `.btn-neo` | 基础按钮 | 白底黑框，hover 上移+阴影 |
| `.btn-neo-primary` | 主按钮 | 蓝底白字 |
| `.card-neo` | 卡片容器 | 灰底黑框+小阴影 |
| `.input-neo` | 输入框 | 白底黑框，focus 蓝色光环 |
| `.tag-neo` | 标签 | 蓝底白字小标签 |
| `.list-neo` | 列表 | 蓝色三角符号前缀 |
| `.tab-btn` | 标签页按钮 | 白底黑框，active 蓝底 |
| `.bg-grid` | 网格背景 | 20px 间距的浅灰网格线 |

### 3.3 新增页面/组件的设计要求

所有新增的 UI 元素必须复用上述 CSS 类。如果需要新组件，必须在 `globals.css` 的 `@layer components` 中定义，风格与现有组件保持一致。

**新增组件需求：**
1. **Markdown 渲染容器** — 用于展示 AI 分析结果，需要为 h1-h4、ul/ol、table、code、blockquote 定义新野兽派样式
2. **历史记录卡片** — 展示用户过去的分析记录
3. **Loading 骨架屏** — 分析等待时的占位动画（使用 CSS animation，禁止引入动画库）

---

## 四、数据库设计

### 4.1 表结构（当前版本，需要迁移）

**表名：`analysis_records`**

```sql
CREATE TABLE IF NOT EXISTS analysis_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_uuid TEXT NOT NULL,
    task_type TEXT NOT NULL DEFAULT 'single_content',
    source_url TEXT NOT NULL,
    platform TEXT DEFAULT '',           -- 新增：'douyin' 或 'xiaohongshu'
    content_title TEXT DEFAULT '',      -- 新增：内容标题/文案前50字
    raw_data_json TEXT,
    ai_analysis TEXT,
    geo_blog_md TEXT,
    slug TEXT UNIQUE,
    seo_title TEXT,
    seo_desc TEXT,
    candidate_for_blog BOOLEAN DEFAULT 0,
    is_public BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP  -- 新增：更新时间
);
```

**迁移脚本（在 `main.py` 的 `init_db()` 中追加）：**
```python
# 安全地添加新列（SQLite 不支持 IF NOT EXISTS 对列）
try:
    c.execute("ALTER TABLE analysis_records ADD COLUMN platform TEXT DEFAULT ''")
except sqlite3.OperationalError:
    pass  # 列已存在
try:
    c.execute("ALTER TABLE analysis_records ADD COLUMN content_title TEXT DEFAULT ''")
except sqlite3.OperationalError:
    pass
try:
    c.execute("ALTER TABLE analysis_records ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
except sqlite3.OperationalError:
    pass
```

### 4.2 索引
```sql
CREATE INDEX IF NOT EXISTS idx_user_uuid ON analysis_records(user_uuid);
CREATE INDEX IF NOT EXISTS idx_is_public ON analysis_records(is_public);
CREATE INDEX IF NOT EXISTS idx_slug ON analysis_records(slug);
CREATE INDEX IF NOT EXISTS idx_created_at ON analysis_records(created_at);
```

---

## 五、API 接口规范

### 5.1 完整接口清单

#### 公开接口（无需认证）

| 方法 | 路径 | 功能 | 限流 |
|------|------|------|------|
| POST | `/api/fetch` | 获取抖音/小红书内容数据 | 5次/分钟/IP |
| POST | `/api/analyze` | AI 分析单条内容（SSE 流式） | 5次/分钟/IP |
| POST | `/api/analyze/account` | AI 账号对标分析（SSE 流式） | 5次/分钟/IP |
| GET | `/api/history` | 获取用户历史分析记录 | 10次/分钟/IP |
| GET | `/api/public/cases` | 获取公开案例列表 | 无限流 |
| GET | `/api/public/cases/{slug}` | 获取案例详情 | 无限流 |
| GET | `/api/sitemap.xml` | 站点地图 | 无限流 |

#### 管理接口（需要 Admin Token）

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/admin/records` | 查看所有分析记录（分页） |
| PUT | `/api/admin/records/{id}/candidate` | 标记/取消候选内容 |
| PUT | `/api/admin/records/{id}/publish` | 发布 GEO 文章 |
| DELETE | `/api/admin/records/{id}` | 删除记录 |
| GET | `/api/admin/stats` | 系统统计数据 |

### 5.2 接口详细规范

#### `POST /api/fetch` — 获取内容数据

**请求体：**
```json
{
  "url": "https://v.douyin.com/xxxxxx/",
  "user_uuid": "浏览器生成的UUID"
}
```

**成功响应 (200)：**
```json
{
  "type": "douyin_video",
  "data": {
    "aweme_id": "7xxxxxxxxx",
    "desc": "作品文案...",
    "author": { "nickname": "作者昵称" },
    "statistics": { "digg_count": 1000, "comment_count": 50, "collect_count": 200, "share_count": 30 },
    "images": [{ "url_list": ["https://..."] }],
    "video": { "cover": { "url_list": ["https://..."] } }
  }
}
```

**错误响应：**
- `400`：`{"detail": "未检测到有效链接"}` 或 `{"detail": "不支持的URL类型"}`
- `429`：`{"detail": "请求过于频繁，请稍后再试"}`
- `500`：`{"detail": "获取内容失败: ..."}`

#### `POST /api/analyze` — AI 分析内容（SSE 流式）

**请求体：**
```json
{
  "raw_data": { "type": "douyin_video", "data": { ... } },
  "user_uuid": "UUID",
  "task_type": "single_content",
  "prompt": "用户自定义提示词（可选）"
}
```

**成功响应 (200, Content-Type: text/event-stream)：**
```
data: ## 📊 一、基础数据概览\n\n
data: - **发布信息**：...
data: [DONE]
```

**关键实现要求：**
1. 流式输出过程中，后端必须在内存中累积完整的分析文本
2. 流式结束后（`[DONE]`），后端必须将完整文本写入 SQLite 的 `ai_analysis` 字段
3. 同时提取 `platform` 和 `content_title` 字段一并写入

#### `POST /api/analyze/account` — 账号对标分析（SSE 流式）

**请求体：**
```json
{
  "url": "https://www.douyin.com/user/MS4wLjABAAAA...",
  "user_uuid": "UUID"
}
```

**后端处理流程：**
1. 调用 `tikhub_client.parse_url(url)` 获取用户主页数据（含最近 5 条作品）
2. 对每条作品提取：标题/文案、获赞数、评论数、收藏数
3. 拼接为紧凑文本，填入 `account_analysis_prompt.md` 模板
4. 调用豆包 API 流式输出
5. 落库（task_type = 'account_analysis'）

**成功响应：** 同 `/api/analyze`，SSE 流式

#### `GET /api/history` — 用户历史记录

**查询参数：**
- `user_uuid` (必填)：用户 UUID
- `page` (可选，默认 1)：页码
- `limit` (可选，默认 10，最大 50)：每页条数

**成功响应 (200)：**
```json
{
  "total": 25,
  "page": 1,
  "limit": 10,
  "records": [
    {
      "id": 1,
      "task_type": "single_content",
      "source_url": "https://v.douyin.com/...",
      "platform": "douyin",
      "content_title": "作品文案前50字...",
      "ai_analysis": "## 📊 一、基础数据概览\n...",
      "created_at": "2026-03-16 10:30:00"
    }
  ]
}
```

#### `GET /api/public/cases` — 公开案例列表

**查询参数：** `page`（默认 1）、`limit`（默认 10）

**成功响应 (200)：**
```json
[
  {
    "id": 1,
    "slug": "analyze-douyin-beauty-xxx",
    "title": "SEO 标题",
    "description": "Meta Description",
    "platform": "douyin",
    "created_at": "2026-03-16 10:30:00"
  }
]
```

#### `GET /api/public/cases/{slug}` — 案例详情

**成功响应 (200)：**
```json
{
  "title": "SEO 标题",
  "description": "Meta Description",
  "content": "GEO 博客 Markdown 正文...",
  "platform": "douyin",
  "created_at": "2026-03-16 10:30:00"
}
```

#### 管理接口认证方式

**认证方式：** 在 `.env` 中配置 `ADMIN_TOKEN=一个随机字符串`，请求时通过 Header 传递：
```
Authorization: Bearer <ADMIN_TOKEN>
```

**后端校验逻辑（在 `main.py` 中添加依赖函数）：**
```python
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

def verify_admin(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth[7:] != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="未授权")
```

#### `PUT /api/admin/records/{id}/publish` — 发布 GEO 文章

**请求体：**
```json
{
  "geo_blog_md": "人工撰写的 GEO 文章 Markdown 正文",
  "slug": "analyze-douyin-beauty-xxx",
  "seo_title": "抖音美妆内容分析：如何打造爆款笔记",
  "seo_desc": "深度拆解抖音美妆赛道爆款内容的8个核心维度..."
}
```

**后端处理：** 更新对应记录的 `geo_blog_md`、`slug`、`seo_title`、`seo_desc`、`is_public=1`、`updated_at=当前时间`

---

## 六、Phase 2 实施任务清单

> **Phase 2 目标：** 修复所有已知 BUG，补全核心功能（分析结果落库、SSE 解析、Markdown 渲染、历史记录、账号对标分析）。
> **预计任务数：** 12 个
> **执行顺序：** 严格按 TASK 编号顺序执行，每个任务完成后测试通过再继续。

---

### TASK-2.01：修复 BUG-1 — 清理 requirements.txt

**文件：** `backend/requirements.txt`
**问题：** 第 8 行包含 `sqlite3`，这是 Python 内置模块，pip install 会报错 `No matching distribution found`。同时 `opencv-python` 和 `pandas` 在当前代码中未使用，属于冗余依赖，会显著增大 Docker 镜像体积。
**操作：**

1. 删除第 8 行的 `sqlite3`
2. 删除第 10 行的 `opencv-python==4.9.0.80`（当前代码仅用 Pillow 处理图片）
3. 删除第 13 行的 `pandas==2.2.0`（report_generator.py 暂未启用）

**修改后的完整 `requirements.txt`：**
```
fastapi==0.110.0
uvicorn==0.27.1
python-multipart==0.0.9
requests==2.31.0
slowapi==0.1.9
limits==3.10.0
python-dotenv==1.0.1
Pillow==10.2.0
pydantic==2.6.1
sse-starlette==2.0.0
```

**验证方式：** 在 backend 目录下执行 `pip install -r requirements.txt`，确认无报错。

---

### TASK-2.02：修复 BUG-3 — Sitemap 查询字段修复 + 数据库迁移

**文件：** `backend/main.py`
**问题 1（BUG-3）：** 第 336-339 行 `/api/sitemap.xml` 查询了 `updated_at` 字段，但当前数据库表没有该列，导致 500 错误。
**问题 2：** 数据库缺少 `platform`、`content_title`、`updated_at` 三个新列。

**操作步骤：**

**步骤 A — 在 `init_db()` 函数中追加迁移逻辑（第 76 行 `conn.commit()` 之前插入）：**

在 `backend/main.py` 的 `init_db()` 函数中，找到 `conn.commit()` 那一行（当前第 76 行），在它**之前**插入以下代码：

```python
    # 安全迁移：添加新列（SQLite 不支持 IF NOT EXISTS 对列）
    for alter_sql in [
        "ALTER TABLE analysis_records ADD COLUMN platform TEXT DEFAULT ''",
        "ALTER TABLE analysis_records ADD COLUMN content_title TEXT DEFAULT ''",
        "ALTER TABLE analysis_records ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP",
    ]:
        try:
            c.execute(alter_sql)
        except sqlite3.OperationalError:
            pass  # 列已存在，忽略

    # 创建索引
    c.execute("CREATE INDEX IF NOT EXISTS idx_user_uuid ON analysis_records(user_uuid)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_is_public ON analysis_records(is_public)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_slug ON analysis_records(slug)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON analysis_records(created_at)")
```

**步骤 B — 修复 `/api/sitemap.xml` 的 SQL 查询（当前第 336-339 行）：**

将：
```python
    c.execute('''
        SELECT slug, updated_at
        FROM analysis_records
        WHERE is_public = 1
    ''')
```

替换为：
```python
    c.execute('''
        SELECT slug, COALESCE(updated_at, created_at) as last_modified
        FROM analysis_records
        WHERE is_public = 1 AND slug IS NOT NULL
    ''')
```

**验证方式：** 启动后端，访问 `GET /api/sitemap.xml`，应返回有效 XML（即使内容为空也不应 500）。

---

### TASK-2.03：修复 BUG-2 — 分析结果落库

**文件：** `backend/main.py`
**问题：** `/api/analyze` 接口（第 235-271 行）在流式输出完成后没有将 AI 分析结果写入 SQLite，导致历史记录和 GEO 功能无数据可用。
**核心改动：** 不能直接用 `call_doubao_api()` 返回 StreamingResponse，需要自己写一个生成器包装函数，在流式输出的同时累积完整文本，流结束后写入数据库。

**操作步骤：**

**步骤 A — 在 `analyze_content` 函数之前（约第 234 行），添加一个新的辅助函数：**

```python
def stream_and_save(generator, user_uuid: str, task_type: str, source_url: str,
                    raw_data_json: str, platform: str, content_title: str):
    """包装流式生成器：边输出 SSE 边累积文本，结束后写入数据库"""
    full_text = []
    for chunk in generator:
        full_text.append(chunk)
        # 按 SSE 协议格式输出
        yield f"data: {chunk}\n\n"
    # 发送结束标记
    yield "data: [DONE]\n\n"
    # 流结束，将完整分析结果写入数据库
    analysis_text = "".join(full_text)
    if analysis_text.strip():
        try:
            conn = sqlite3.connect('./data/analysis_records.db')
            c = conn.cursor()
            c.execute('''
                INSERT INTO analysis_records
                (user_uuid, task_type, source_url, platform, content_title, raw_data_json, ai_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_uuid, task_type, source_url, platform, content_title, raw_data_json, analysis_text))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"写入数据库失败: {e}")
```

**步骤 B — 重写 `analyze_content` 函数体（替换当前第 235-271 行的整个函数）：**

```python
@app.post("/api/analyze")
@limiter.limit(RATE_LIMIT)
async def analyze_content(request: Request, analyze_request: AnalyzeRequest):
    """分析已获取的内容（SSE 流式输出 + 结果落库）"""
    task_id = str(uuid.uuid4())

    try:
        raw_data = analyze_request.raw_data

        # 提取 platform 和 content_title
        data_type = raw_data.get("type", "")
        inner_data = raw_data.get("data", {})
        if "douyin" in data_type:
            platform = "douyin"
            content_title = (inner_data.get("desc") or "")[:50]
        elif "xiaohongshu" in data_type:
            platform = "xiaohongshu"
            content_title = (inner_data.get("title") or inner_data.get("desc") or "")[:50]
        else:
            platform = ""
            content_title = ""

        # 下载前3张图片用于多模态分析
        image_urls = extract_image_urls(raw_data, max_images=3)
        image_base64_list = []
        for img_url in image_urls:
            b64 = download_media(img_url, task_id)
            if b64:
                image_base64_list.append(b64)

        # 读取 prompt 模板
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "default_analysis_prompt.md")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                base_prompt = f.read()
        except FileNotFoundError:
            base_prompt = "请分析以下社交媒体内容，给出结构化的分析报告。\n\n## 待分析内容数据\n{raw_data}"

        # 精简数据构造 prompt
        slim = slim_raw_data(raw_data)
        prompt = base_prompt.replace("{raw_data}", json.dumps(slim, indent=2, ensure_ascii=False))
        if analyze_request.prompt:
            prompt += f"\n\n## 用户补充要求\n{analyze_request.prompt}\n"

        # 构造源 URL（从 raw_data 中尽量提取）
        source_url = ""
        if inner_data.get("aweme_id"):
            source_url = f"https://www.douyin.com/video/{inner_data['aweme_id']}"
        elif inner_data.get("note_id"):
            source_url = f"https://www.xiaohongshu.com/discovery/item/{inner_data['note_id']}"

        # 流式输出 + 落库
        generator = doubao_client.chat_stream(prompt, image_base64_list or None)
        return StreamingResponse(
            stream_and_save(
                generator,
                user_uuid=analyze_request.user_uuid or "",
                task_type=analyze_request.task_type,
                source_url=source_url,
                raw_data_json=json.dumps(slim, ensure_ascii=False),
                platform=platform,
                content_title=content_title,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")
```

**关键变化说明（给执行模型）：**
1. 现在使用 `stream_and_save()` 包装器替代直接调用 `call_doubao_api()`
2. 每个 chunk 都按 `data: {chunk}\n\n` 的 SSE 协议格式输出
3. 流结束后自动发送 `data: [DONE]\n\n`
4. 流结束后将完整文本 INSERT 到 `analysis_records` 表
5. 从 prompt 模板文件读取分析框架，而非硬编码在代码中
6. 自动提取 `platform` 和 `content_title` 字段

**验证方式：**
1. 调用 `POST /api/fetch` 获取一条内容
2. 调用 `POST /api/analyze` 进行分析
3. 确认 SSE 流正常输出，每行以 `data: ` 开头
4. 分析完成后，用 SQLite 客户端查询 `SELECT * FROM analysis_records ORDER BY id DESC LIMIT 1`，确认 `ai_analysis` 字段有内容

---

### TASK-2.04：修复 BUG-4 — 前端 SSE 解析修复

**文件：** `frontend/app/page.tsx`
**问题：** 第 148-163 行的 SSE 读取逻辑直接将 `reader.read()` 的原始 chunk 拼接到 result 中，没有解析 SSE 协议的 `data: ` 前缀，导致用户看到 `data: ## 📊 一、基础数据概览` 这样的原始协议文本。

**操作：** 替换 `handleAnalyze` 函数中第 148-163 行的 SSE 读取逻辑。

**将当前代码（第 148-163 行）：**
```typescript
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
```

**替换为：**
```typescript
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          // 按换行符分割，处理每一行
          const lines = buffer.split('\n');
          // 最后一个元素可能是不完整的行，保留在 buffer 中
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;
            if (trimmed === 'data: [DONE]') continue;
            if (trimmed.startsWith('data: ')) {
              const content = trimmed.slice(6); // 去掉 "data: " 前缀
              setResult(prev => prev + content);
            }
          }

          // 自动滚动到底部
          if (resultRef.current) {
            resultRef.current.scrollTop = resultRef.current.scrollHeight;
          }
        }
      }
```

**关键变化说明：**
1. 引入 `buffer` 变量处理跨 chunk 的不完整行
2. 按 `\n` 分割后逐行解析
3. 只提取 `data: ` 前缀后的实际内容
4. 忽略 `data: [DONE]` 结束标记和空行

**验证方式：** 在前端执行一次完整的获取+分析流程，确认流式输出的文本不包含 `data: ` 前缀。

---

### TASK-2.05：修复 BUG-5 — Docker 环境下 API 代理地址

**文件：** `frontend/next.config.js`
**问题：** 第 14 行 rewrite 目标是 `http://localhost:8000`，在 Docker Compose 网络中容器间通信应使用服务名 `backend`。但本地开发时又需要 `localhost`。

**操作：** 使用环境变量控制代理目标地址。

**将 `frontend/next.config.js` 完整替换为：**
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
```

**同时修改 `deploy/docker-compose.yml` 的 frontend 服务，添加环境变量：**

在 `frontend` 服务的 `environment` 部分添加：
```yaml
  frontend:
    build: ./frontend
    container_name: analysis-frontend
    restart: always
    ports:
      - "3000:3000"
    environment:
      - TZ=Asia/Shanghai
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend
```

**验证方式：**
- 本地开发：不设置 `BACKEND_URL`，默认走 `localhost:8000` ✅
- Docker 部署：通过环境变量走 `backend:8000` ✅

---

### TASK-2.06：修复 BUG-6 — Dockerfile 移除不可靠的 cron

**文件：** `backend/Dockerfile`
**问题：** python:3.11-slim 镜像不包含 cron 守护进程，`cron &&` 命令会直接失败。即使安装了 cron，在容器中运行 cron 守护进程也不可靠。

**方案：** 移除 Dockerfile 中的 cron 相关内容，改用 Docker Compose 的独立清理服务（使用轻量级 alpine + crond）。

**步骤 A — 将 `backend/Dockerfile` 完整替换为：**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要目录
RUN mkdir -p /app/data /app/temp_media /app/data/backups

# 启动服务（不再包含 cron）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**步骤 B — 在 `deploy/docker-compose.yml` 中添加清理服务：**

在 `nginx` 服务之后添加：
```yaml
  # 定时清理服务
  cron:
    image: alpine:3.19
    container_name: analysis-cron
    restart: always
    volumes:
      - ./data:/data
      - ./temp_media:/temp_media
    entrypoint: /bin/sh
    command: >
      -c "echo '0 * * * * find /temp_media -type f -mmin +1440 -delete 2>/dev/null
      0 3 * * * cp /data/analysis_records.db /data/backups/db_$$(date +\%Y\%m\%d).sqlite3 && find /data/backups -type f -mtime +7 -delete 2>/dev/null' | crontab - && crond -f"
    environment:
      - TZ=Asia/Shanghai
```

**验证方式：** `docker compose up -d` 后执行 `docker exec analysis-cron crontab -l`，确认两条定时任务已注册。

---

### TASK-2.07：修复 BUG-7 — 前端 Markdown 渲染

**文件：** `frontend/app/page.tsx`、`frontend/app/globals.css`、`frontend/package.json`
**问题：** AI 分析结果是 Markdown 格式，但前端用 `whitespace-pre-wrap` 纯文本渲染，用户看到原始 `##`、`**`、`-` 等标记符号。

**操作步骤：**

**步骤 A — 安装依赖（在 frontend 目录下执行）：**
```bash
npm install react-markdown@9.0.1 remark-gfm@4.0.0
```

**步骤 B — 在 `frontend/app/page.tsx` 顶部添加 import（第 2 行之后）：**
```typescript
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
```

**步骤 C — 替换结果展示区域的纯文本渲染（当前第 263-270 行）：**

将：
```tsx
              {activeTab === 'result' && (
                <div
                  ref={resultRef}
                  className="font-mono text-sm leading-relaxed max-h-[600px] overflow-y-auto p-6 bg-white border-3 border-dark whitespace-pre-wrap"
                >
                  {result}
                </div>
              )}
```

替换为：
```tsx
              {activeTab === 'result' && (
                <div
                  ref={resultRef}
                  className="max-h-[600px] overflow-y-auto p-6 bg-white border-3 border-dark"
                >
                  {analyzing ? (
                    <div className="neo-markdown">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {result || '⏳ AI 正在分析中...'}
                      </ReactMarkdown>
                    </div>
                  ) : result ? (
                    <div className="neo-markdown">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {result}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-gray-400 font-mono">分析结果将在这里显示</p>
                  )}
                </div>
              )}
```

**步骤 D — 在 `frontend/app/globals.css` 的 `@layer components` 块末尾（第 91 行 `}` 之前）添加 Markdown 新野兽派样式：**

```css
  /* Markdown 渲染容器 - 新野兽派风格 */
  .neo-markdown {
    @apply text-sm leading-relaxed;
    font-family: 'Inter', sans-serif;
  }

  .neo-markdown h1 {
    @apply font-mono text-2xl font-bold mt-8 mb-4 pb-2 border-b-3 border-dark;
  }

  .neo-markdown h2 {
    @apply font-mono text-xl font-bold mt-6 mb-3;
  }

  .neo-markdown h3 {
    @apply font-mono text-lg font-bold mt-5 mb-2;
  }

  .neo-markdown h4 {
    @apply font-mono text-base font-bold mt-4 mb-2;
  }

  .neo-markdown p {
    @apply mb-3;
  }

  .neo-markdown ul {
    @apply mb-4 ml-0 list-none;
  }

  .neo-markdown ul li {
    @apply flex items-start mb-2;
  }

  .neo-markdown ul li::before {
    content: "▸";
    @apply font-mono text-lg mr-3 text-blue-600 font-bold flex-shrink-0;
  }

  .neo-markdown ol {
    @apply mb-4 ml-6 list-decimal;
  }

  .neo-markdown ol li {
    @apply mb-2;
  }

  .neo-markdown strong {
    @apply font-bold text-dark;
  }

  .neo-markdown blockquote {
    @apply border-l-3 border-blue-600 pl-4 py-2 my-4 bg-blue-50 text-gray-700 italic;
  }

  .neo-markdown code {
    @apply font-mono text-xs bg-gray-100 border border-gray-300 px-1.5 py-0.5;
  }

  .neo-markdown pre {
    @apply my-4 p-4 bg-gray-900 text-green-400 border-3 border-dark overflow-x-auto;
  }

  .neo-markdown pre code {
    @apply bg-transparent border-0 p-0 text-green-400;
  }

  .neo-markdown table {
    @apply w-full my-4 border-3 border-dark;
  }

  .neo-markdown thead {
    @apply bg-dark text-white;
  }

  .neo-markdown th {
    @apply font-mono font-bold p-3 text-left border border-gray-600;
  }

  .neo-markdown td {
    @apply p-3 border border-gray-300;
  }

  .neo-markdown tbody tr:nth-child(even) {
    @apply bg-gray-50;
  }

  .neo-markdown hr {
    @apply my-6 border-t-3 border-dark;
  }

  .neo-markdown a {
    @apply text-blue-600 font-bold underline;
  }
```

**验证方式：** 执行一次完整分析，确认结果区域正确渲染 Markdown 标题、列表、表格、加粗等格式，且风格与新野兽派一致。

### TASK-2.08：Prompt 模板外部化

**文件：** `backend/main.py`
**问题：** TASK-2.03 已将单内容分析的 prompt 改为从文件读取，但 `call_doubao_api()` 辅助函数仍然存在且不再被调用，属于死代码。同时需要确认 prompt 模板文件的 `{raw_data}` 占位符与代码中的 `.replace()` 调用一致。

**操作步骤：**

**步骤 A — 删除死代码 `call_doubao_api` 函数（当前第 191-193 行）：**

删除以下三行：
```python
def call_doubao_api(prompt: str, image_base64_list: Optional[list] = None) -> StreamingResponse:
    """调用豆包API进行分析，支持多图，流式返回结果"""
    return StreamingResponse(doubao_client.chat_stream(prompt, image_base64_list), media_type="text/event-stream")
```

**步骤 B — 确认 prompt 模板文件占位符：**

检查 `backend/prompts/default_analysis_prompt.md` 末尾是否包含 `{raw_data}` 占位符（当前第 50 行）。如果存在，无需修改。代码中使用 `.replace("{raw_data}", ...)` 进行替换。

检查 `backend/prompts/account_analysis_prompt.md` 末尾是否包含 `{account_data}` 和 `{recent_posts}` 两个占位符（当前第 52、55 行）。TASK-2.11 实现账号分析时会用到。

**验证方式：** 全局搜索 `call_doubao_api`，确认无任何引用。启动后端确认无 import 错误。

---

### TASK-2.09：实现 `/api/history` 历史记录接口

**文件：** `backend/main.py`
**需求：** 用户可以查看自己的分析历史。通过 `user_uuid` 查询，支持分页。

**操作：** 在 `/api/analyze/account` 路由之前（约第 273 行前），插入以下完整接口代码：

```python
@app.get("/api/history")
@limiter.limit(RATE_LIMIT)
async def get_history(request: Request, user_uuid: str, page: int = 1, limit: int = 20):
    """获取用户的分析历史记录"""
    if not user_uuid or len(user_uuid) < 10:
        raise HTTPException(status_code=400, detail="无效的 user_uuid")
    if limit > 50:
        limit = 50
    offset = (page - 1) * limit

    conn = sqlite3.connect('./data/analysis_records.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 查询总数
    c.execute(
        "SELECT COUNT(*) FROM analysis_records WHERE user_uuid = ?",
        (user_uuid,)
    )
    total = c.fetchone()[0]

    # 查询列表（不返回 raw_data_json 和 ai_analysis 大字段）
    c.execute('''
        SELECT id, task_type, source_url, platform, content_title, created_at
        FROM analysis_records
        WHERE user_uuid = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    ''', (user_uuid, limit, offset))
    rows = c.fetchall()
    conn.close()

    records = []
    for row in rows:
        records.append({
            "id": row["id"],
            "task_type": row["task_type"],
            "source_url": row["source_url"],
            "platform": row["platform"],
            "content_title": row["content_title"],
            "created_at": row["created_at"],
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "records": records,
    }


@app.get("/api/history/{record_id}")
@limiter.limit(RATE_LIMIT)
async def get_history_detail(request: Request, record_id: int, user_uuid: str):
    """获取单条分析记录详情（含完整 AI 分析文本）"""
    if not user_uuid or len(user_uuid) < 10:
        raise HTTPException(status_code=400, detail="无效的 user_uuid")

    conn = sqlite3.connect('./data/analysis_records.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT id, task_type, source_url, platform, content_title,
               raw_data_json, ai_analysis, created_at
        FROM analysis_records
        WHERE id = ? AND user_uuid = ?
    ''', (record_id, user_uuid))
    row = c.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")

    return {
        "id": row["id"],
        "task_type": row["task_type"],
        "source_url": row["source_url"],
        "platform": row["platform"],
        "content_title": row["content_title"],
        "raw_data_json": row["raw_data_json"],
        "ai_analysis": row["ai_analysis"],
        "created_at": row["created_at"],
    }
```

**关键设计说明：**
1. 列表接口不返回 `raw_data_json` 和 `ai_analysis`，减少传输量
2. 详情接口需要同时传 `record_id` 和 `user_uuid`，防止越权访问
3. `limit` 上限 50，防止一次拉取过多数据
4. 使用 `conn.row_factory = sqlite3.Row` 使结果可按列名访问

**验证方式：**
1. 先通过 TASK-2.03 的分析接口产生几条记录（带 `user_uuid`）
2. `GET /api/history?user_uuid=xxx` 应返回记录列表
3. `GET /api/history/1?user_uuid=xxx` 应返回完整详情

---

### TASK-2.10：前端历史记录面板

**文件：** `frontend/app/page.tsx`
**需求：** 在现有页面中添加"历史记录"Tab，用户可查看过往分析、点击查看详情。

**前置条件：** TASK-2.09 已完成。

**操作步骤：**

**步骤 A — 添加状态变量（在现有 state 声明区域，约第 20-30 行附近）：**

在已有的 `useState` 声明之后添加：
```typescript
const [historyList, setHistoryList] = useState<any[]>([])
const [historyLoading, setHistoryLoading] = useState(false)
const [historyPage, setHistoryPage] = useState(1)
const [historyTotal, setHistoryTotal] = useState(0)
```

**步骤 B — 添加获取历史记录的函数（在 `handleAnalyze` 函数之后）：**

```typescript
const fetchHistory = async (page: number = 1) => {
  const uuid = localStorage.getItem('user_uuid')
  if (!uuid) return
  setHistoryLoading(true)
  try {
    const res = await fetch(`/api/history?user_uuid=${uuid}&page=${page}&limit=10`)
    if (res.ok) {
      const data = await res.json()
      setHistoryList(data.records || [])
      setHistoryTotal(data.total || 0)
      setHistoryPage(page)
    }
  } catch (e) {
    console.error('获取历史记录失败:', e)
  } finally {
    setHistoryLoading(false)
  }
}

const loadHistoryDetail = async (recordId: number) => {
  const uuid = localStorage.getItem('user_uuid')
  if (!uuid) return
  try {
    const res = await fetch(`/api/history/${recordId}?user_uuid=${uuid}`)
    if (res.ok) {
      const data = await res.json()
      setResult(data.ai_analysis || '')
      setActiveTab('result')
    }
  } catch (e) {
    console.error('获取历史详情失败:', e)
  }
}
```

**步骤 C — 在 Tab 按钮区域添加"历史记录"Tab：**

找到现有的 Tab 按钮（`result`、`rawData` 等），在最后一个 Tab 按钮之后添加：
```tsx
<button
  className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
  onClick={() => { setActiveTab('history'); fetchHistory(); }}
>
  📋 历史记录
</button>
```

**步骤 D — 在结果展示区域添加历史记录面板（在最后一个 Tab 内容块之后）：**

```tsx
{activeTab === 'history' && (
  <div className="p-6 bg-white border-3 border-dark max-h-[600px] overflow-y-auto">
    {historyLoading ? (
      <p className="text-gray-400 font-mono">加载中...</p>
    ) : historyList.length === 0 ? (
      <p className="text-gray-400 font-mono">暂无分析记录</p>
    ) : (
      <>
        <div className="space-y-3">
          {historyList.map((item: any) => (
            <div
              key={item.id}
              className="card-neo p-4 cursor-pointer hover:shadow-[6px_6px_0px_#1a1a1a] transition-shadow"
              onClick={() => loadHistoryDetail(item.id)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="tag-neo mr-2">
                    {item.platform === 'douyin' ? '抖音' : item.platform === 'xiaohongshu' ? '小红书' : item.platform}
                  </span>
                  <span className="font-mono font-bold text-sm">
                    {item.content_title || '未命名内容'}
                  </span>
                </div>
                <span className="text-xs text-gray-500 font-mono">{item.created_at}</span>
              </div>
            </div>
          ))}
        </div>
        {historyTotal > 10 && (
          <div className="flex justify-center gap-4 mt-4">
            <button
              className="btn-neo text-sm"
              disabled={historyPage <= 1}
              onClick={() => fetchHistory(historyPage - 1)}
            >
              上一页
            </button>
            <span className="font-mono text-sm leading-[40px]">
              {historyPage} / {Math.ceil(historyTotal / 10)}
            </span>
            <button
              className="btn-neo text-sm"
              disabled={historyPage >= Math.ceil(historyTotal / 10)}
              onClick={() => fetchHistory(historyPage + 1)}
            >
              下一页
            </button>
          </div>
        )}
      </>
    )}
  </div>
)}
```

**步骤 E — 确保 `user_uuid` 在页面加载时生成并存储：**

在组件的 `useEffect` 中（如果没有则新建），添加：
```typescript
useEffect(() => {
  if (!localStorage.getItem('user_uuid')) {
    localStorage.setItem('user_uuid', crypto.randomUUID())
  }
}, [])
```

同时确保 `handleAnalyze` 和 `handleFetch` 调用时传递 `user_uuid: localStorage.getItem('user_uuid')`。

**验证方式：**
1. 执行几次分析后，点击"历史记录"Tab
2. 应显示分析记录列表，包含平台标签、内容标题、时间
3. 点击某条记录，应切换到"分析结果"Tab 并显示完整 AI 分析内容

---

### TASK-2.11：实现 `/api/analyze/account` 账号对标分析

**文件：** `backend/main.py`
**需求：** 用户输入抖音/小红书用户主页链接，系统自动获取账号信息 + 最近 5 条作品数据，调用豆包 AI 进行账号级别的深度分析。

**前置条件：** TASK-2.03 已完成（`stream_and_save` 函数可复用）。

**操作：** 替换当前第 273-278 行的 TODO 桩代码，写入完整实现。

**将当前代码：**
```python
@app.post("/api/analyze/account")
@limiter.limit(RATE_LIMIT)
async def analyze_account(request: Request, analysis_request: AnalysisRequest):
    """分析账号"""
    # TODO: 实现账号对标分析逻辑
    return {"status": "pending", "message": "账号分析功能开发中"}
```

**替换为：**
```python
class AccountAnalyzeRequest(BaseModel):
    user_url: str
    user_uuid: Optional[str] = None
    prompt: Optional[str] = None


@app.post("/api/analyze/account")
@limiter.limit(RATE_LIMIT)
async def analyze_account(request: Request, req: AccountAnalyzeRequest):
    """账号对标分析：获取用户信息 + 最近作品 → AI 深度分析"""
    try:
        user_url = req.user_url.strip()

        # 1. 判断平台并获取用户作品列表
        if 'douyin.com' in user_url:
            platform = "douyin"
            user_data = tikhub_client.get_douyin_user_videos(user_url, limit=5)
        elif 'xiaohongshu.com' in user_url or 'xhslink.com' in user_url:
            platform = "xiaohongshu"
            user_data = tikhub_client.get_xiaohongshu_user_notes(user_url, limit=5)
        else:
            raise HTTPException(status_code=400, detail="仅支持抖音/小红书用户主页链接")

        # 2. 提取账号基础信息和作品列表
        inner = user_data.get('data', {})
        # 抖音返回结构: data.aweme_list / data.aweme_details
        # 小红书返回结构: data.notes / data.items
        posts_raw = (
            inner.get('aweme_list')
            or inner.get('aweme_details')
            or inner.get('notes')
            or inner.get('items')
            or []
        )

        # 精简每条作品数据
        posts_slim = []
        for i, post in enumerate(posts_raw[:5]):
            stats = post.get('statistics', post.get('interact_info', {}))
            posts_slim.append({
                "index": i + 1,
                "desc": (post.get('desc') or post.get('title') or '')[:100],
                "digg_count": stats.get('digg_count', stats.get('liked_count', 0)),
                "comment_count": stats.get('comment_count', 0),
                "collect_count": stats.get('collect_count', stats.get('collected_count', 0)),
                "share_count": stats.get('share_count', 0),
            })

        # 3. 读取账号分析 prompt 模板
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "account_analysis_prompt.md")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                base_prompt = f.read()
        except FileNotFoundError:
            base_prompt = "请分析以下账号数据。\n\n## 账号基础数据\n{account_data}\n\n## 最近5条作品数据\n{recent_posts}"

        # 4. 填充 prompt
        account_summary = {
            "platform": platform,
            "user_url": user_url,
            "total_posts_fetched": len(posts_slim),
        }
        prompt = base_prompt.replace(
            "{account_data}", json.dumps(account_summary, indent=2, ensure_ascii=False)
        ).replace(
            "{recent_posts}", json.dumps(posts_slim, indent=2, ensure_ascii=False)
        )
        if req.prompt:
            prompt += f"\n\n## 用户补充要求\n{req.prompt}\n"

        # 5. 流式输出 + 落库
        generator = doubao_client.chat_stream(prompt, None)
        return StreamingResponse(
            stream_and_save(
                generator,
                user_uuid=req.user_uuid or "",
                task_type="account_analysis",
                source_url=user_url,
                raw_data_json=json.dumps(account_summary, ensure_ascii=False),
                platform=platform,
                content_title=f"账号分析-{platform}",
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"账号分析失败: {str(e)}")
```

**关键设计说明：**
1. 新增 `AccountAnalyzeRequest` 模型，字段为 `user_url`（区别于单内容的 `raw_data`）
2. 复用 `tikhub_client` 已有的 `get_douyin_user_videos()` 和 `get_xiaohongshu_user_notes()` 方法
3. 精简每条作品数据，只保留描述和核心互动指标
4. 复用 `stream_and_save()` 实现流式输出 + 自动落库
5. `task_type` 设为 `"account_analysis"`，与单内容的 `"single_content"` 区分

**验证方式：**
1. `POST /api/analyze/account` 传入 `{"user_url": "https://www.douyin.com/user/xxx"}`
2. 确认 SSE 流正常输出账号分析报告
3. 查询数据库确认 `task_type = 'account_analysis'` 的记录已写入

---

### TASK-2.12：前端账号分析入口

**文件：** `frontend/app/page.tsx`
**需求：** 在现有页面中添加"账号分析"模式切换，用户可以输入用户主页链接进行账号级分析。

**前置条件：** TASK-2.11 已完成。

**操作步骤：**

**步骤 A — 添加状态变量（在已有 state 区域）：**

```typescript
const [analysisMode, setAnalysisMode] = useState<'content' | 'account'>('content')
```

**步骤 B — 在 URL 输入框上方添加模式切换按钮：**

找到 URL 输入区域（`<input>` 或 `<textarea>` 所在的 card），在其上方添加：
```tsx
<div className="flex gap-3 mb-4">
  <button
    className={`btn-neo flex-1 ${analysisMode === 'content' ? 'btn-neo-primary' : ''}`}
    onClick={() => setAnalysisMode('content')}
  >
    🔍 单内容分析
  </button>
  <button
    className={`btn-neo flex-1 ${analysisMode === 'account' ? 'btn-neo-primary' : ''}`}
    onClick={() => setAnalysisMode('account')}
  >
    👤 账号对标分析
  </button>
</div>
```

**步骤 C — 修改输入框 placeholder 文案：**

根据 `analysisMode` 动态切换：
```tsx
placeholder={
  analysisMode === 'content'
    ? '粘贴抖音/小红书内容链接...'
    : '粘贴抖音/小红书用户主页链接...'
}
```

**步骤 D — 添加账号分析处理函数（在 `handleAnalyze` 之后）：**

```typescript
const handleAccountAnalyze = async () => {
  if (!url.trim()) return
  setAnalyzing(true)
  setResult('')
  setActiveTab('result')

  try {
    const response = await fetch('/api/analyze/account', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_url: url.trim(),
        user_uuid: localStorage.getItem('user_uuid') || '',
      }),
    })

    if (!response.ok) {
      const err = await response.json()
      setResult(`❌ ${err.detail || '账号分析失败'}`)
      return
    }

    // SSE 解析逻辑（与 handleAnalyze 中相同）
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (reader) {
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) continue
          if (trimmed === 'data: [DONE]') continue
          if (trimmed.startsWith('data: ')) {
            const content = trimmed.slice(6)
            setResult(prev => prev + content)
          }
        }

        if (resultRef.current) {
          resultRef.current.scrollTop = resultRef.current.scrollHeight
        }
      }
    }
  } catch (e: any) {
    setResult(`❌ 请求失败: ${e.message}`)
  } finally {
    setAnalyzing(false)
  }
}
```

**步骤 E — 修改主操作按钮的 onClick 逻辑：**

找到"开始分析"按钮，将其 `onClick` 改为根据模式分发：
```tsx
onClick={() => {
  if (analysisMode === 'account') {
    handleAccountAnalyze()
  } else {
    handleFetch()  // 单内容模式：先获取数据再分析
  }
}}
```

按钮文案也可以动态切换：
```tsx
{analyzing
  ? '分析中...'
  : analysisMode === 'content'
    ? '🚀 获取并分析'
    : '🚀 分析账号'
}
```

**验证方式：**
1. 切换到"账号对标分析"模式
2. 输入抖音用户主页链接
3. 点击"分析账号"，确认 SSE 流式输出账号分析报告
4. 切回"单内容分析"模式，确认原有功能不受影响

---

> **Phase 2 完成标志：** 12 个 TASK 全部执行并验证通过。此时系统具备：
> - ✅ 无已知 BUG
> - ✅ 单内容分析（SSE 流式 + Markdown 渲染 + 自动落库）
> - ✅ 账号对标分析（SSE 流式 + 自动落库）
> - ✅ 历史记录查看（列表 + 详情）
> - ✅ Prompt 模板外部化
> - ✅ Docker 环境兼容

---

## 七、Phase 3 实施任务清单

> **Phase 3 目标：** 构建 GEO（Generative Engine Optimization）内容管道——公开案例页面、动态路由、JSON-LD 结构化数据、管理后台、Sitemap、高潜内容报告。让系统从"工具"升级为"可被搜索引擎收录的内容平台"。
> **预计任务数：** 8 个
> **前置条件：** Phase 2 全部 12 个 TASK 已完成并验证通过。

---

### TASK-3.01：GEO 博客动态路由 — `/cases/[slug]` 页面

**新建文件：** `frontend/app/cases/[slug]/page.tsx`
**需求：** 为每篇已发布的 GEO 文章创建独立的 SEO 友好页面，路径格式 `/cases/analyze-douyin-beauty-xxx`。

**操作步骤：**

**步骤 A — 创建目录和文件：**

创建 `frontend/app/cases/[slug]/page.tsx`，完整内容如下：

```tsx
import { notFound } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// 关闭客户端缓存，每次请求都从后端拉取最新数据
export const dynamic = 'force-dynamic'

interface CaseData {
  title: string
  description: string
  content: string
  created_at: string
}

async function getCaseData(slug: string): Promise<CaseData | null> {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
  try {
    const res = await fetch(`${backendUrl}/api/public/cases/${slug}`, {
      cache: 'no-store',
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

// 动态生成页面 metadata（SEO 关键）
export async function generateMetadata({ params }: { params: { slug: string } }) {
  const data = await getCaseData(params.slug)
  if (!data) return { title: '案例不存在' }
  return {
    title: data.title,
    description: data.description,
    openGraph: {
      title: data.title,
      description: data.description,
      type: 'article',
    },
  }
}

export default async function CasePage({ params }: { params: { slug: string } }) {
  const data = await getCaseData(params.slug)
  if (!data) notFound()

  // JSON-LD 结构化数据
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: data.title,
    description: data.description,
    datePublished: data.created_at,
    author: {
      '@type': 'Organization',
      name: 'AI 内容分析工具',
    },
  }

  return (
    <main className="bg-gray-50 text-dark min-h-screen">
      {/* JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* 文章头部 */}
      <section className="px-6 py-16 bg-white border-b-3 border-dark">
        <div className="max-w-3xl mx-auto">
          <a href="/cases" className="font-mono text-sm text-blue-600 font-bold mb-6 inline-block">
            ← 返回案例列表
          </a>
          <h1 className="font-mono text-3xl md:text-4xl font-bold mb-4">
            {data.title}
          </h1>
          <p className="text-gray-600 text-lg mb-4">{data.description}</p>
          <time className="font-mono text-sm text-gray-400">{data.created_at}</time>
        </div>
      </section>

      {/* 文章正文 */}
      <section className="px-6 py-12">
        <div className="max-w-3xl mx-auto">
          <div className="card-neo p-8">
            <div className="neo-markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {data.content}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-12 bg-gray-100 text-center">
        <p className="font-mono text-lg font-bold mb-4">想分析你自己的内容？</p>
        <a href="/" className="btn-neo btn-neo-primary">
          免费试用 AI 分析 →
        </a>
      </section>
    </main>
  )
}
```

**关键设计说明：**
1. 这是 Next.js App Router 的 Server Component（无 `'use client'`），支持 SSR，对 SEO 友好
2. `generateMetadata` 动态生成 `<title>` 和 `<meta description>`
3. 内嵌 JSON-LD `Article` 结构化数据，帮助搜索引擎理解内容
4. 复用 Phase 2 定义的 `.neo-markdown` 样式类
5. `BACKEND_URL` 环境变量与 TASK-2.05 保持一致

**验证方式：**
1. 先通过管理接口（TASK-3.04）发布一篇案例
2. 访问 `/cases/your-slug`，确认页面正常渲染
3. 查看页面源码，确认 `<title>`、`<meta description>`、JSON-LD 均正确输出

---

### TASK-3.02：案例列表页 — `/cases`

**新建文件：** `frontend/app/cases/page.tsx`
**需求：** 展示所有已发布的 GEO 案例列表，作为 SEO 入口页。

**操作：** 创建 `frontend/app/cases/page.tsx`，完整内容如下：

```tsx
import Link from 'next/link'

export const dynamic = 'force-dynamic'

export const metadata = {
  title: '内容分析案例库 - AI 内容分析工具',
  description: '精选抖音、小红书爆款内容深度分析案例，拆解流量密码，助力内容创作。',
}

interface CaseItem {
  id: number
  slug: string
  title: string
  description: string
  created_at: string
}

async function getCases(): Promise<CaseItem[]> {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
  try {
    const res = await fetch(`${backendUrl}/api/public/cases?page=1&limit=50`, {
      cache: 'no-store',
    })
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

export default async function CasesPage() {
  const cases = await getCases()

  return (
    <main className="bg-gray-50 text-dark min-h-screen">
      {/* 页头 */}
      <section className="px-6 py-16 bg-white border-b-3 border-dark">
        <div className="max-w-4xl mx-auto">
          <a href="/" className="font-mono text-sm text-blue-600 font-bold mb-6 inline-block">
            ← 返回首页
          </a>
          <h1 className="font-mono text-3xl md:text-4xl font-bold mb-4">
            内容分析案例库
          </h1>
          <p className="text-gray-600 text-lg">
            精选爆款内容深度拆解，看看高手是怎么做内容的
          </p>
        </div>
      </section>

      {/* 案例列表 */}
      <section className="px-6 py-12">
        <div className="max-w-4xl mx-auto">
          {cases.length === 0 ? (
            <div className="card-neo p-8 text-center">
              <p className="font-mono text-gray-400">暂无公开案例，敬请期待</p>
            </div>
          ) : (
            <div className="space-y-6">
              {cases.map((item) => (
                <Link key={item.id} href={`/cases/${item.slug}`}>
                  <div className="card-neo p-6 cursor-pointer hover:shadow-neo transition-shadow">
                    <h2 className="font-mono text-xl font-bold mb-2">{item.title}</h2>
                    <p className="text-gray-600 text-sm mb-3">{item.description}</p>
                    <time className="font-mono text-xs text-gray-400">{item.created_at}</time>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  )
}
```

**验证方式：** 访问 `/cases`，确认列表正常渲染。点击某条案例，跳转到 `/cases/[slug]` 详情页。

---

### TASK-3.03：404 页面 — 新野兽派风格

**新建文件：** `frontend/app/not-found.tsx`
**需求：** 当用户访问不存在的路由或案例 slug 时，展示统一的 404 页面。

**操作：** 创建 `frontend/app/not-found.tsx`，完整内容如下：

```tsx
import Link from 'next/link'

export default function NotFound() {
  return (
    <main className="bg-gray-50 text-dark min-h-screen flex items-center justify-center px-6">
      <div className="text-center">
        <h1 className="font-mono text-8xl font-bold mb-4">404</h1>
        <p className="font-mono text-xl mb-8">页面走丢了</p>
        <div className="flex gap-4 justify-center">
          <Link href="/" className="btn-neo btn-neo-primary">
            回到首页
          </Link>
          <Link href="/cases" className="btn-neo">
            浏览案例
          </Link>
        </div>
      </div>
    </main>
  )
}
```

**验证方式：** 访问 `/cases/nonexistent-slug` 或 `/random-path`，确认显示 404 页面。

---

### TASK-3.04：管理后台接口 — 完整 CRUD

**文件：** `backend/main.py`
**需求：** 管理员可以查看所有分析记录、标记高潜内容、发布/下架 GEO 文章、删除记录。所有管理接口使用 `ADMIN_TOKEN` 鉴权（第五章已定义校验函数 `verify_admin`）。

**前置条件：** TASK-2.02 数据库迁移已完成（`updated_at` 列存在）。

**操作：** 在 `main.py` 文件末尾（`if __name__ == "__main__"` 之前）插入以下全部管理接口代码：

**步骤 A — 确保 `verify_admin` 函数和 `ADMIN_TOKEN` 已添加（如果 Phase 2 未添加，在文件顶部全局配置区域插入）：**

```python
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

def verify_admin(request: Request):
    """校验管理员 Token"""
    auth = request.headers.get("Authorization", "")
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=500, detail="ADMIN_TOKEN 未配置")
    if not auth.startswith("Bearer ") or auth[7:] != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="未授权")
```

**步骤 B — 添加管理接口请求模型（在已有的 `AnalyzeRequest` 模型之后）：**

```python
class PublishRequest(BaseModel):
    geo_blog_md: str
    slug: str
    seo_title: str
    seo_desc: str
```

**步骤 C — 插入管理接口（在 `/api/sitemap.xml` 路由之前）：**

```python
# ==================== 管理后台接口 ====================

@app.get("/api/admin/records")
async def admin_list_records(request: Request, page: int = 1, limit: int = 20,
                              task_type: Optional[str] = None,
                              is_public: Optional[int] = None):
    """管理员查看所有分析记录"""
    verify_admin(request)
    if limit > 100:
        limit = 100
    offset = (page - 1) * limit

    conn = sqlite3.connect('./data/analysis_records.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 构建动态 WHERE 条件
    conditions = []
    params = []
    if task_type:
        conditions.append("task_type = ?")
        params.append(task_type)
    if is_public is not None:
        conditions.append("is_public = ?")
        params.append(is_public)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # 查询总数
    c.execute(f"SELECT COUNT(*) FROM analysis_records {where_clause}", params)
    total = c.fetchone()[0]

    # 查询列表
    c.execute(f'''
        SELECT id, task_type, source_url, platform, content_title,
               slug, seo_title, is_public, candidate_for_blog, created_at, updated_at
        FROM analysis_records
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    ''', params + [limit, offset])
    rows = c.fetchall()
    conn.close()

    records = []
    for row in rows:
        records.append({
            "id": row["id"],
            "task_type": row["task_type"],
            "source_url": row["source_url"],
            "platform": row["platform"],
            "content_title": row["content_title"],
            "slug": row["slug"],
            "seo_title": row["seo_title"],
            "is_public": row["is_public"],
            "candidate_for_blog": row["candidate_for_blog"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        })

    return {"total": total, "page": page, "limit": limit, "records": records}


@app.get("/api/admin/records/{record_id}")
async def admin_get_record(request: Request, record_id: int):
    """管理员查看单条记录完整详情（含 raw_data_json 和 ai_analysis）"""
    verify_admin(request)

    conn = sqlite3.connect('./data/analysis_records.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM analysis_records WHERE id = ?", (record_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")

    return dict(row)


@app.put("/api/admin/records/{record_id}/publish")
async def admin_publish_record(request: Request, record_id: int, req: PublishRequest):
    """发布 GEO 文章 — 将分析记录转为公开案例"""
    verify_admin(request)

    # 校验 slug 格式：仅允许小写字母、数字、连字符
    import re as _re
    if not _re.match(r'^[a-z0-9][a-z0-9\-]{2,80}$', req.slug):
        raise HTTPException(status_code=400, detail="slug 格式无效，仅允许小写字母、数字和连字符，3-81 字符")

    conn = sqlite3.connect('./data/analysis_records.db')
    c = conn.cursor()

    # 检查 slug 是否已被其他记录占用
    c.execute("SELECT id FROM analysis_records WHERE slug = ? AND id != ?", (req.slug, record_id))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="该 slug 已被其他记录使用")

    c.execute('''
        UPDATE analysis_records
        SET geo_blog_md = ?, slug = ?, seo_title = ?, seo_desc = ?,
            is_public = 1, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (req.geo_blog_md, req.slug, req.seo_title, req.seo_desc, record_id))

    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="记录不存在")

    conn.commit()
    conn.close()
    return {"status": "ok", "message": f"已发布，访问路径: /cases/{req.slug}"}


@app.put("/api/admin/records/{record_id}/unpublish")
async def admin_unpublish_record(request: Request, record_id: int):
    """下架 GEO 文章"""
    verify_admin(request)

    conn = sqlite3.connect('./data/analysis_records.db')
    c = conn.cursor()
    c.execute('''
        UPDATE analysis_records
        SET is_public = 0, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (record_id,))

    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="记录不存在")

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "已下架"}


@app.put("/api/admin/records/{record_id}/candidate")
async def admin_toggle_candidate(request: Request, record_id: int):
    """切换高潜内容标记（candidate_for_blog 0↔1）"""
    verify_admin(request)

    conn = sqlite3.connect('./data/analysis_records.db')
    c = conn.cursor()
    c.execute('''
        UPDATE analysis_records
        SET candidate_for_blog = CASE WHEN candidate_for_blog = 1 THEN 0 ELSE 1 END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (record_id,))

    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="记录不存在")

    conn.commit()

    # 返回更新后的状态
    c.execute("SELECT candidate_for_blog FROM analysis_records WHERE id = ?", (record_id,))
    new_val = c.fetchone()[0]
    conn.close()
    return {"status": "ok", "candidate_for_blog": new_val}


@app.delete("/api/admin/records/{record_id}")
async def admin_delete_record(request: Request, record_id: int):
    """删除分析记录"""
    verify_admin(request)

    conn = sqlite3.connect('./data/analysis_records.db')
    c = conn.cursor()
    c.execute("DELETE FROM analysis_records WHERE id = ?", (record_id,))

    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="记录不存在")

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "已删除"}
```

**接口汇总表：**

| 方法 | 路径 | 功能 | 鉴权 |
|------|------|------|------|
| GET | `/api/admin/records` | 分页列表，支持 `task_type`/`is_public` 筛选 | ✅ |
| GET | `/api/admin/records/{id}` | 单条完整详情 | ✅ |
| PUT | `/api/admin/records/{id}/publish` | 发布 GEO 文章 | ✅ |
| PUT | `/api/admin/records/{id}/unpublish` | 下架文章 | ✅ |
| PUT | `/api/admin/records/{id}/candidate` | 切换高潜标记 | ✅ |
| DELETE | `/api/admin/records/{id}` | 删除记录 | ✅ |

**验证方式：**
1. 在 `.env` 中设置 `ADMIN_TOKEN=test123`
2. 不带 Token 请求 `GET /api/admin/records` → 应返回 401
3. 带 `Authorization: Bearer test123` 请求 → 应返回记录列表
4. 调用 publish 接口发布一条记录，然后访问 `/cases/{slug}` 确认页面可访问
5. 调用 unpublish 接口下架，再访问 `/cases/{slug}` 应返回 404

---

### TASK-3.05：完善 Sitemap 生成 — 包含静态页面 + 动态案例

**文件：** `backend/main.py`
**需求：** 当前 Sitemap 只包含动态案例页面，缺少首页 `/` 和案例列表页 `/cases`。同时需要使用每条记录的真实 `updated_at` 时间。

**操作：** 替换现有的 `/api/sitemap.xml` 路由（TASK-2.02 已修复过一次，现在做功能增强）。

**将当前 `/api/sitemap.xml` 整个路由函数替换为：**

```python
@app.get("/api/sitemap.xml")
async def get_sitemap():
    """生成 sitemap.xml — 包含静态页面和所有公开案例"""
    base_url = os.getenv("SITE_URL", "https://your-domain.com").rstrip("/")
    now_iso = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect('./data/analysis_records.db')
    c = conn.cursor()
    c.execute('''
        SELECT slug, COALESCE(updated_at, created_at) as last_modified
        FROM analysis_records
        WHERE is_public = 1 AND slug IS NOT NULL AND slug != ''
    ''')
    records = c.fetchall()
    conn.close()

    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        # 静态页面
        f'  <url><loc>{base_url}/</loc><lastmod>{now_iso}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>',
        f'  <url><loc>{base_url}/cases</loc><lastmod>{now_iso}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>',
    ]

    # 动态案例页面
    for slug, last_modified in records:
        mod_date = last_modified[:10] if last_modified else now_iso
        xml_parts.append(
            f'  <url><loc>{base_url}/cases/{slug}</loc><lastmod>{mod_date}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>'
        )

    xml_parts.append('</urlset>')
    xml_content = '\n'.join(xml_parts)

    return StreamingResponse(
        io.BytesIO(xml_content.encode('utf-8')),
        media_type="application/xml",
        headers={"Cache-Control": "public, max-age=3600"},
    )
```

**同时在 `.env` 模板中添加：**
```
SITE_URL=https://your-domain.com
```

**关键变化：**
1. 新增 `SITE_URL` 环境变量，替代硬编码域名
2. 包含首页和案例列表页两个静态 URL
3. 使用每条记录的真实 `updated_at` 日期
4. 添加 1 小时缓存头，减少重复生成开销
5. 过滤掉 `slug` 为空的记录

**验证方式：** `GET /api/sitemap.xml` 应返回包含 `/`、`/cases`、以及所有已发布案例 URL 的有效 XML。

---

### TASK-3.06：robots.txt + Nginx Sitemap 路由

**文件：** `backend/main.py`、`deploy/nginx.conf`
**需求：** 搜索引擎爬虫需要 `/robots.txt` 来发现 Sitemap 地址，同时 `/sitemap.xml` 需要从根路径可访问。

**步骤 A — 在 `backend/main.py` 中添加 robots.txt 接口（在 `/api/sitemap.xml` 之后）：**

```python
@app.get("/api/robots.txt")
async def get_robots():
    """生成 robots.txt"""
    base_url = os.getenv("SITE_URL", "https://your-domain.com").rstrip("/")
    content = f"""User-agent: *
Allow: /
Allow: /cases/
Disallow: /api/admin/
Disallow: /api/history/

Sitemap: {base_url}/sitemap.xml
"""
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="text/plain",
    )
```

**步骤 B — 在 `deploy/nginx.conf` 的 HTTP server 块中（`location /api/` 之前）添加两条路由：**

```nginx
    # SEO 文件路由到后端
    location = /sitemap.xml {
        proxy_pass http://backend:8000/api/sitemap.xml;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location = /robots.txt {
        proxy_pass http://backend:8000/api/robots.txt;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
```

**验证方式：**
1. 访问 `https://your-domain.com/robots.txt` → 应返回包含 Sitemap 地址的文本
2. 访问 `https://your-domain.com/sitemap.xml` → 应返回有效 XML
3. 使用 Google Search Console 的 Sitemap 测试工具验证格式

---

### TASK-3.07：高潜内容报告脚本优化

**文件：** `backend/scripts/report_generator.py`
**问题：** 现有脚本可运行但存在几个问题：
1. 第 79 行 `record[5]` 取的是 `ai_analysis` 而非 `candidate_for_blog`（SQL SELECT 顺序不匹配）
2. 缺少与管理接口联动的"自动标记高潜"功能
3. 输出目录硬编码为 `./reports`，Docker 环境下路径不一致

**操作：** 替换 `backend/scripts/report_generator.py` 完整内容：

```python
"""
高潜内容挖掘报告生成脚本
用法：
  python scripts/report_generator.py --weekly           # 生成周度 CSV 报告
  python scripts/report_generator.py --high-potential 3 # 标记查询≥3次的内容为高潜
"""
import os
import sqlite3
import csv
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "./data/analysis_records.db")
REPORT_DIR = os.getenv("REPORT_DIR", "./data/reports")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def generate_weekly_report():
    """生成周度高潜内容报告 CSV"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        SELECT id, source_url, task_type, platform, content_title,
               candidate_for_blog, is_public, created_at, ai_analysis
        FROM analysis_records
        WHERE candidate_for_blog = 1 OR created_at >= ?
        ORDER BY created_at DESC
    ''', (one_week_ago,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("没有符合条件的记录")
        return None

    report_date = datetime.now().strftime('%Y%m%d')
    csv_path = os.path.join(REPORT_DIR, f"weekly_report_{report_date}.csv")

    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', '平台', '内容标题', '原始链接', '任务类型',
            '高潜标记', '已发布', '创建时间', '分析摘要'
        ])
        for row in rows:
            analysis_summary = (row["ai_analysis"] or "")[:200] + "..."
            writer.writerow([
                row["id"],
                row["platform"],
                row["content_title"],
                row["source_url"],
                row["task_type"],
                "是" if row["candidate_for_blog"] else "否",
                "是" if row["is_public"] else "否",
                row["created_at"],
                analysis_summary,
            ])

    print(f"周度报告已生成: {csv_path}（共 {len(rows)} 条）")
    return csv_path


def mark_high_potential(threshold: int = 5):
    """自动标记高潜内容：同一 source_url 被查询 ≥ threshold 次的，自动设置 candidate_for_blog=1"""
    conn = get_conn()
    c = conn.cursor()

    # 找出高频查询的 source_url
    c.execute('''
        SELECT source_url, COUNT(*) as cnt
        FROM analysis_records
        WHERE source_url IS NOT NULL AND source_url != ''
        GROUP BY source_url
        HAVING cnt >= ?
    ''', (threshold,))
    hot_urls = c.fetchall()

    if not hot_urls:
        print(f"没有查询次数 ≥ {threshold} 的内容")
        conn.close()
        return

    marked_count = 0
    for row in hot_urls:
        url = row["source_url"]
        c.execute('''
            UPDATE analysis_records
            SET candidate_for_blog = 1, updated_at = CURRENT_TIMESTAMP
            WHERE source_url = ? AND candidate_for_blog = 0
        ''', (url,))
        marked_count += c.rowcount

    conn.commit()
    conn.close()
    print(f"发现 {len(hot_urls)} 个高频 URL，新标记 {marked_count} 条记录为高潜内容")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='高潜内容报告工具')
    parser.add_argument('--weekly', action='store_true', help='生成周度 CSV 报告')
    parser.add_argument('--high-potential', type=int, metavar='N',
                        help='自动标记查询次数 ≥ N 的内容为高潜')
    args = parser.parse_args()

    if args.weekly:
        generate_weekly_report()
    if args.high_potential is not None:
        mark_high_potential(args.high_potential)
    if not args.weekly and args.high_potential is None:
        generate_weekly_report()
        mark_high_potential()
```

**关键改进：**
1. 使用 `conn.row_factory = sqlite3.Row`，按列名访问，彻底避免索引错位
2. `mark_high_potential()` 自动将高频查询内容标记为 `candidate_for_blog=1`，与管理后台联动
3. 路径通过 `DB_PATH` 和 `REPORT_DIR` 环境变量控制，Docker 兼容
4. CSV 增加 `平台`、`内容标题`、`已发布` 列，信息更完整

**验证方式：**
```bash
cd backend
python scripts/report_generator.py --weekly
python scripts/report_generator.py --high-potential 2
```
确认 CSV 文件生成且列数据正确，高潜标记写入数据库。

---

### TASK-3.08：前端 Layout SEO 增强 — 全局 meta + 结构化数据

**文件：** `frontend/app/layout.tsx`
**需求：** 增强全局 SEO 配置：Open Graph、Twitter Card、favicon、canonical URL、全站 JSON-LD `WebSite` Schema。

**操作：** 替换 `frontend/app/layout.tsx` 完整内容：

```tsx
import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })
const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
})

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://your-domain.com'

export const metadata: Metadata = {
  title: {
    default: 'AI 内容分析工具 - 抖音/小红书数据化运营助手',
    template: '%s | AI 内容分析工具',
  },
  description: '输入抖音/小红书链接，AI 自动分析 8 个维度数据，提供专业优化建议，助力内容创作和运营增长。',
  metadataBase: new URL(siteUrl),
  openGraph: {
    type: 'website',
    locale: 'zh_CN',
    siteName: 'AI 内容分析工具',
    title: 'AI 内容分析工具 - 抖音/小红书数据化运营助手',
    description: '输入抖音/小红书链接，AI 自动分析 8 个维度数据，提供专业优化建议。',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AI 内容分析工具',
    description: '抖音/小红书内容深度分析，AI 驱动的运营增长助手。',
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // 全站 JSON-LD WebSite Schema
  const websiteJsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'AI 内容分析工具',
    url: siteUrl,
    description: '抖音/小红书内容深度分析平台',
    potentialAction: {
      '@type': 'SearchAction',
      target: `${siteUrl}/cases?q={search_term_string}`,
      'query-input': 'required name=search_term_string',
    },
  }

  return (
    <html lang="zh-CN">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteJsonLd) }}
        />
      </head>
      <body className={inter.className}>{children}</body>
    </html>
  )
}
```

**同时在 `deploy/docker-compose.yml` 的 frontend 环境变量中添加：**
```yaml
      - NEXT_PUBLIC_SITE_URL=https://your-domain.com
```

**关键变化：**
1. `title` 使用 `template` 模式，子页面自动拼接站名（如 `案例标题 | AI 内容分析工具`）
2. 添加 Open Graph 和 Twitter Card meta 标签
3. 全站注入 `WebSite` JSON-LD Schema，包含 `SearchAction`
4. `metadataBase` 确保所有相对 URL 正确解析
5. `NEXT_PUBLIC_SITE_URL` 是 Next.js 客户端可访问的环境变量

**验证方式：**
1. 查看首页源码，确认 `<title>`、`<meta property="og:*">`、`<meta name="twitter:*">` 均存在
2. 查看 `<script type="application/ld+json">`，确认 `WebSite` Schema 正确
3. 访问 `/cases/some-slug`，确认 `<title>` 格式为 `案例标题 | AI 内容分析工具`

---

> **Phase 3 完成标志：** 8 个 TASK 全部执行并验证通过。此时系统具备：
> - ✅ GEO 案例动态路由（`/cases/[slug]`）+ 列表页（`/cases`）
> - ✅ 每篇案例自带 JSON-LD Article Schema + 动态 meta
> - ✅ 管理后台完整 CRUD（发布/下架/标记/删除）
> - ✅ Sitemap + robots.txt 自动生成
> - ✅ 高潜内容自动标记 + 周度报告
> - ✅ 全站 SEO 基础设施就绪

---

## 八、Phase 4 生产部署与上线

> **Phase 4 目标：** 将项目同步到 GitHub、配置生产级 Docker 部署、启用 HTTPS、加固安全策略，使系统可作为公开服务稳定运行。
> **预计任务数：** 8 个
> **前置条件：** Phase 3 全部 8 个 TASK 已完成并验证通过。

---

### TASK-4.01：完善 `.env.example` 模板 — 包含所有新增变量

**文件：** `backend/.env.example`
**问题：** 当前模板缺少 Phase 2/3 新增的 `ADMIN_TOKEN`、`SITE_URL`、`DB_PATH`、`REPORT_DIR` 等变量。

**操作：** 替换 `backend/.env.example` 完整内容：

```env
# ========== 第三方 API 配置 ==========
TIKHUB_API_KEY=your_tikhub_api_key
# 中国大陆用户请使用 https://api.tikhub.dev 无需代理
TIKHUB_BASE_URL=https://api.tikhub.io

# ========== 火山引擎豆包 API 配置 ==========
ARK_API_KEY=your_ark_api_key
VOLC_REGION=cn-beijing
DOUBAO_MODEL=doubao-seed-2-0-lite-260215
ENDPOINT_ID=your_endpoint_id

# ========== 系统配置 ==========
TEMP_MEDIA_DIR=./temp_media
MAX_FILE_SIZE_MB=20
RATE_LIMIT_PER_MINUTE=5
DEBUG=false

# ========== 管理后台 ==========
# 生成方式: python -c "import secrets; print(secrets.token_urlsafe(32))"
ADMIN_TOKEN=your_admin_token_here

# ========== 站点配置（SEO / Sitemap） ==========
SITE_URL=https://your-domain.com

# ========== 数据库与报告（可选，有默认值） ==========
# DB_PATH=./data/analysis_records.db
# REPORT_DIR=./data/reports
```

**验证方式：** 对比 `backend/main.py` 中所有 `os.getenv()` 调用，确认每个变量在模板中都有对应条目。

---

### TASK-4.02：加固 `.gitignore` — 防止密钥泄露

**文件：** `.gitignore`（项目根目录）
**问题：** 当前 `.gitignore` 第 7 行 `.env` 只匹配根目录的 `.env`，不会匹配 `backend/.env`。同时缺少 `data/*.db`（当前只有 `data/*.sqlite3`，但实际数据库文件后缀是 `.db`）、`cert/` 目录等。

**操作：** 替换 `.gitignore` 完整内容：

```gitignore
# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
venv/
.venv/

# Environment files — 任何位置的 .env 都不提交
**/.env
!**/.env.example

# Data files
data/
temp_media/
*.csv
*.xlsx
reports/

# SSL certificates
cert/

# Build outputs
.next/
dist/
build/
*.egg-info/

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
```

**关键变化：**
1. `**/.env` 匹配所有子目录的 `.env` 文件
2. `!**/.env.example` 排除模板文件（允许提交）
3. `data/` 整个目录忽略（包含 `.db` 和 `backups/`）
4. `cert/` 忽略 SSL 证书目录
5. 添加 IDE 配置忽略

**⚠️ 重要安全提醒（给执行模型）：**
当前 `backend/.env` 包含真实 API Key。在首次 `git add` 之前，**必须**先确认 `.gitignore` 已更新且生效。执行以下命令验证：
```bash
git status --short
# 确认输出中不包含 backend/.env
```
如果 `.env` 已经被 git 跟踪过，需要先移除缓存：
```bash
git rm --cached backend/.env
```

---

### TASK-4.03：GitHub 仓库初始化与首次推送

**操作环境：** 项目根目录 `/Users/ericgao/Desktop/抖音数据获取&AI分析/`
**前置条件：** TASK-4.01 和 TASK-4.02 已完成。

**操作步骤：**

**步骤 A — 在 GitHub 上创建仓库：**

```bash
# 使用 GitHub CLI（需要先 gh auth login）
gh repo create ai-content-analyzer --public --description "AI 社交媒体内容分析系统 - 抖音/小红书数据化运营助手"
```

如果没有安装 `gh` CLI，手动在 GitHub 网页创建仓库，名称建议 `ai-content-analyzer`。

**步骤 B — 本地初始化并推送：**

```bash
cd /Users/ericgao/Desktop/抖音数据获取\&AI分析/

# 初始化 git（如果尚未初始化）
git init

# 确认 .gitignore 生效
git status --short
# ⚠️ 检查输出，确认没有 backend/.env、data/ 等敏感文件

# 添加远程仓库
git remote add origin git@github.com:YOUR_USERNAME/ai-content-analyzer.git

# 首次提交
git add .
git commit -m "feat: 初始化 AI 社交媒体内容分析系统

- FastAPI 后端 + Next.js 14 前端
- TikHub API 数据获取 + 豆包 AI 分析
- Docker Compose 部署配置
- 新野兽派 UI 设计"

# 推送
git branch -M main
git push -u origin main
```

**步骤 C — 推送后验证：**

1. 访问 GitHub 仓库页面，确认文件结构正确
2. 确认 `backend/.env` **不在**仓库中
3. 确认 `backend/.env.example` **在**仓库中
4. 确认 `data/` 目录**不在**仓库中

---

### TASK-4.04：Docker Compose 生产配置完善

**文件：** `deploy/docker-compose.yml`
**问题：** 当前配置缺少健康检查、资源限制、日志控制，且 backend 直接暴露 8000 端口到宿主机（生产环境应只通过 Nginx 访问）。

**操作：** 替换 `deploy/docker-compose.yml` 完整内容：

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: analysis-backend
    restart: always
    expose:
      - "8000"
    volumes:
      - ./data:/app/data
      - ./temp_media:/app/temp_media
      - ./backend/.env:/app/.env:ro
    environment:
      - TZ=Asia/Shanghai
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: analysis-frontend
    restart: always
    expose:
      - "3000"
    environment:
      - TZ=Asia/Shanghai
      - BACKEND_URL=http://backend:8000
      - NEXT_PUBLIC_SITE_URL=https://your-domain.com
    depends_on:
      backend:
        condition: service_healthy
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  nginx:
    image: nginx:alpine
    container_name: analysis-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./temp_media:/usr/share/nginx/html/temp:ro
      - ./cert:/etc/nginx/cert:ro
    depends_on:
      - backend
      - frontend
    environment:
      - TZ=Asia/Shanghai
    logging:
      driver: json-file
      options:
        max-size: "5m"
        max-file: "3"

  cron:
    image: alpine:3.19
    container_name: analysis-cron
    restart: always
    volumes:
      - ./data:/data
      - ./temp_media:/temp_media
    entrypoint: /bin/sh
    command: >
      -c "echo '0 * * * * find /temp_media -type f -mmin +1440 -delete 2>/dev/null
      0 3 * * * cp /data/analysis_records.db /data/backups/db_$$(date +\%Y\%m\%d).sqlite3 && find /data/backups -type f -mtime +7 -delete 2>/dev/null' | crontab - && crond -f"
    environment:
      - TZ=Asia/Shanghai
```

**关键变化：**
1. backend/frontend 改用 `expose` 替代 `ports`，不再直接暴露到宿主机，只在 Docker 内部网络可访问
2. backend 添加 `healthcheck`，frontend 的 `depends_on` 使用 `condition: service_healthy` 确保启动顺序
3. 所有服务添加 `logging` 限制（单文件 10MB，最多 3 个），防止日志撑爆磁盘
4. volumes 添加 `:ro`（只读）标记，最小权限原则
5. `NEXT_PUBLIC_SITE_URL` 传入 frontend 容器

**⚠️ 部署前提醒：**
- 将 `your-domain.com` 替换为实际域名
- 确保 `backend/.env` 已配置所有必要变量
- 首次部署前创建必要目录：`mkdir -p data/backups temp_media cert`

**验证方式：**
```bash
docker compose up -d
docker compose ps        # 确认所有服务 running/healthy
docker compose logs -f   # 观察启动日志无报错
curl http://localhost/   # 通过 Nginx 访问前端
curl http://localhost/api/ # 通过 Nginx 访问后端
```

---

### TASK-4.05：Nginx HTTPS 配置 — Let's Encrypt 证书

**文件：** `deploy/nginx.conf`
**需求：** 生产环境必须启用 HTTPS。使用 Let's Encrypt 免费证书。

**操作：** 替换 `deploy/nginx.conf` 完整内容：

```nginx
# HTTP → HTTPS 重定向
server {
    listen 80;
    server_name your-domain.com;

    # Let's Encrypt 验证路径（certbot 需要）
    location /.well-known/acme-challenge/ {
        root /usr/share/nginx/html;
    }

    # 其他所有请求重定向到 HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS 主配置
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    client_max_body_size 20M;

    # SSL 证书路径
    ssl_certificate /etc/nginx/cert/fullchain.pem;
    ssl_certificate_key /etc/nginx/cert/privkey.pem;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # SEO 文件
    location = /sitemap.xml {
        proxy_pass http://backend:8000/api/sitemap.xml;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location = /robots.txt {
        proxy_pass http://backend:8000/api/robots.txt;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 临时媒体文件
    location /temp/ {
        alias /usr/share/nginx/html/temp/;
        autoindex off;
        expires 24h;
        add_header Cache-Control "public, max-age=86400";
    }

    # API 接口
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 流式输出配置
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;

        # 超时设置（AI 分析可能较慢）
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    # 前端应用（放在最后作为兜底）
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**证书申请步骤（在服务器上执行）：**

```bash
# 1. 先用 HTTP-only 模式启动（注释掉 443 server 块，只保留 80 块）
docker compose up -d nginx

# 2. 安装 certbot 并申请证书
sudo apt install certbot -y
sudo certbot certonly --webroot -w /path/to/project/cert -d your-domain.com

# 3. 复制证书到项目 cert 目录
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./cert/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./cert/

# 4. 恢复完整 nginx.conf（取消 443 块注释），重启
docker compose restart nginx

# 5. 设置自动续期（crontab -e 添加）
0 3 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/*.pem /path/to/project/cert/ && docker compose restart nginx
```

**验证方式：**
1. `curl -I http://your-domain.com` → 应返回 `301 Moved Permanently` 到 HTTPS
2. `curl -I https://your-domain.com` → 应返回 `200 OK` + 安全头
3. 使用 [SSL Labs](https://www.ssllabs.com/ssltest/) 测试，目标评级 A 或 A+

---

### TASK-4.06：CORS 加固 — 生产环境限制来源

**文件：** `backend/main.py`
**问题：** 当前第 36-42 行 CORS 配置为 `allow_origins=["*"]`，允许任何域名跨域访问，生产环境存在安全风险。

**操作：** 替换 CORS 配置（第 35-42 行）：

**将：**
```python
# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**替换为：**
```python
# CORS 配置 — 生产环境限制来源
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

**同时在 `backend/.env.example` 中添加：**
```env
# ========== CORS 配置 ==========
# 多个域名用逗号分隔，不要有空格
ALLOWED_ORIGINS=https://your-domain.com,http://localhost:3000
```

**在 `backend/.env` 中添加（实际部署时）：**
```env
ALLOWED_ORIGINS=https://your-domain.com
```

**关键变化：**
1. 来源白名单通过环境变量控制，开发环境默认 `localhost:3000`
2. `allow_methods` 限制为实际使用的 4 种方法
3. `allow_headers` 限制为实际需要的 2 个头
4. 生产环境只允许自己的域名

**验证方式：**
- 从 `https://your-domain.com` 发起 API 请求 → 正常
- 从其他域名发起请求 → 被 CORS 拦截

---

### TASK-4.07：GitHub Actions CI/CD — 自动构建与部署

**新建文件：** `.github/workflows/deploy.yml`
**需求：** 推送到 `main` 分支时自动构建 Docker 镜像并部署到服务器。

**操作：** 创建 `.github/workflows/deploy.yml`，完整内容：

```yaml
name: Build & Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to server via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd ${{ secrets.PROJECT_PATH }}
            git pull origin main
            docker compose build --no-cache
            docker compose up -d
            docker compose ps
            # 清理旧镜像
            docker image prune -f
```

**GitHub Secrets 配置（在仓库 Settings → Secrets and variables → Actions 中添加）：**

| Secret 名称 | 值 | 说明 |
|---|---|---|
| `SERVER_HOST` | `123.45.67.89` | 服务器 IP |
| `SERVER_USER` | `root` 或 `deploy` | SSH 用户名 |
| `SERVER_SSH_KEY` | SSH 私钥内容 | 用于免密登录 |
| `PROJECT_PATH` | `/opt/ai-content-analyzer` | 服务器上项目路径 |

**服务器端前置准备：**

```bash
# 1. 在服务器上克隆仓库
cd /opt
git clone git@github.com:YOUR_USERNAME/ai-content-analyzer.git
cd ai-content-analyzer

# 2. 创建必要目录和配置
mkdir -p data/backups temp_media cert
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入真实 API Key

# 3. 首次手动构建验证
docker compose build
docker compose up -d
```

**验证方式：**
1. 推送一次 commit 到 `main` 分支
2. 在 GitHub Actions 页面查看 workflow 运行状态
3. SSH 到服务器确认容器已更新：`docker compose ps`

---

### TASK-4.08：前端 Dockerfile 优化 — standalone 模式

**文件：** `frontend/Dockerfile`
**问题：** 需要确认前端 Dockerfile 存在且使用 Next.js standalone 输出模式，减小镜像体积。

**操作：** 创建或替换 `frontend/Dockerfile`，完整内容：

```dockerfile
# 阶段 1: 安装依赖
FROM node:18-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# 阶段 2: 构建
FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# 阶段 3: 生产运行
FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# 创建非 root 用户
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 复制 standalone 输出
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

**前置条件：** `frontend/next.config.js` 中已包含 `output: 'standalone'`（TASK-2.05 已添加）。

**关键设计：**
1. 三阶段构建：依赖安装 → 构建 → 生产运行，最终镜像只包含运行时文件
2. 使用非 root 用户 `nextjs` 运行，安全最佳实践
3. standalone 模式下最终镜像约 100-150MB（对比完整 node_modules 可达 500MB+）

**验证方式：**
```bash
cd frontend
docker build -t analysis-frontend .
docker run -p 3000:3000 -e BACKEND_URL=http://host.docker.internal:8000 analysis-frontend
# 访问 http://localhost:3000 确认页面正常
```

---

> **Phase 4 完成标志：** 8 个 TASK 全部执行并验证通过。此时系统具备：
> - ✅ GitHub 仓库已创建，密钥安全（.env 不在仓库中）
> - ✅ Docker Compose 生产级配置（健康检查、日志限制、最小权限）
> - ✅ HTTPS 启用 + 安全头 + SSL A 级评分
> - ✅ CORS 白名单限制
> - ✅ CI/CD 自动部署（push to main → 自动更新服务器）
> - ✅ 前端多阶段构建，镜像精简

---

## 九、基础设施安全机制

> 本章不涉及新功能开发，而是对已有机制的汇总说明和运维指南。所有技术实现已在 Phase 2-4 的 TASK 中完成，本章供运维参考。

---

### 9.1 存储清理策略

| 清理对象 | 策略 | 实现位置 |
|----------|------|----------|
| `temp_media/` 临时图片 | 超过 24 小时自动删除 | `cron` 容器，每小时执行 `find -mmin +1440 -delete` |
| `data/backups/` 数据库备份 | 保留最近 7 天，超期自动删除 | `cron` 容器，每天凌晨 3 点执行 |
| Docker 旧镜像 | 每次部署后自动清理 | GitHub Actions `docker image prune -f` |
| 日志文件 | 单文件 10MB，最多 3 个轮转 | `docker-compose.yml` logging 配置 |

**手动清理命令（紧急情况）：**
```bash
# 清理所有临时媒体
find ./temp_media -type f -delete

# 清理 Docker 所有未使用资源
docker system prune -af --volumes

# 查看磁盘占用
du -sh data/ temp_media/ && docker system df
```

---

### 9.2 数据库备份与恢复

**自动备份：** `cron` 容器每天凌晨 3 点将 `analysis_records.db` 复制到 `data/backups/db_YYYYMMDD.sqlite3`。

**手动备份：**
```bash
cp data/analysis_records.db data/backups/db_manual_$(date +%Y%m%d_%H%M%S).sqlite3
```

**恢复：**
```bash
# 1. 停止后端服务
docker compose stop backend

# 2. 替换数据库文件
cp data/backups/db_20260318.sqlite3 data/analysis_records.db

# 3. 重启
docker compose start backend
```

**⚠️ 注意：** SQLite 不支持并发写入。备份时如果后端正在写入，可能产生损坏的备份。生产环境如果并发量较高（>10 QPS），建议迁移到 PostgreSQL。

---

### 9.3 限流策略

| 接口类别 | 限流规则 | 实现方式 |
|----------|----------|----------|
| `/api/fetch`、`/api/analyze`、`/api/analyze/account` | 每分钟 5 次（可通过 `RATE_LIMIT_PER_MINUTE` 调整） | slowapi + `@limiter.limit()` 装饰器 |
| `/api/history`、`/api/history/{id}` | 每分钟 5 次 | 同上 |
| `/api/public/cases`、`/api/public/cases/{slug}` | 无限流（公开 SEO 页面） | — |
| `/api/admin/*` | 无限流（Token 鉴权已保护） | — |
| Nginx 层 | `client_max_body_size 20M` | nginx.conf |

**如果遭遇恶意请求，可临时在 Nginx 层添加 IP 限流：**
```nginx
# 在 http 块中添加（nginx.conf 顶部或单独的 conf 文件）
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

# 在 location /api/ 块中添加
limit_req zone=api burst=20 nodelay;
```

---

### 9.4 安全检查清单

部署上线前，逐项确认：

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | `backend/.env` 不在 Git 仓库中 | ☐ |
| 2 | `ADMIN_TOKEN` 已设置为强随机字符串（≥32 字符） | ☐ |
| 3 | `ALLOWED_ORIGINS` 已限制为实际域名 | ☐ |
| 4 | `DEBUG=false` 已设置 | ☐ |
| 5 | HTTPS 已启用，HTTP 自动重定向 | ☐ |
| 6 | SSL Labs 评级 ≥ A | ☐ |
| 7 | Nginx 安全头已配置（X-Frame-Options, HSTS 等） | ☐ |
| 8 | Docker 容器使用非 root 用户运行（前端已配置） | ☐ |
| 9 | 数据库备份 cron 正常运行（`docker exec analysis-cron crontab -l`） | ☐ |
| 10 | `SITE_URL` 已设置为实际域名 | ☐ |
| 11 | GitHub Secrets 已配置（SERVER_HOST, SSH_KEY 等） | ☐ |
| 12 | 服务器防火墙仅开放 80/443 端口 | ☐ |

---

### 9.5 监控与告警建议（可选增强）

以下为推荐但非必须的监控手段，可在系统稳定运行后逐步添加：

1. **Uptime 监控：** 使用 [UptimeRobot](https://uptimerobot.com)（免费）监控 `https://your-domain.com/api/` 端点，宕机时邮件/Telegram 告警
2. **磁盘监控：** 在服务器 crontab 中添加磁盘告警脚本：
```bash
# 每小时检查，磁盘使用超过 85% 时告警
0 * * * * df -h / | awk 'NR==2{if(int($5)>85) print "DISK WARNING: "$5" used"}' | mail -s "Disk Alert" your@email.com
```
3. **Docker 容器状态：** `docker compose ps` 定期检查，或使用 Portainer 可视化管理

---

## 十、附录：完整文件清单与修改索引

> 供执行模型快速定位每个 TASK 涉及的文件。

| TASK | 操作类型 | 文件路径 |
|------|----------|----------|
| 2.01 | 修改 | `backend/requirements.txt` |
| 2.02 | 修改 | `backend/main.py`（init_db + sitemap） |
| 2.03 | 修改 | `backend/main.py`（新增 stream_and_save + 重写 analyze_content） |
| 2.04 | 修改 | `frontend/app/page.tsx`（SSE 解析逻辑） |
| 2.05 | 修改 | `frontend/next.config.js` + `deploy/docker-compose.yml` |
| 2.06 | 修改 | `backend/Dockerfile` + `deploy/docker-compose.yml` |
| 2.07 | 修改 | `frontend/app/page.tsx` + `frontend/app/globals.css` + `frontend/package.json` |
| 2.08 | 修改 | `backend/main.py`（删除 call_doubao_api） |
| 2.09 | 修改 | `backend/main.py`（新增 /api/history） |
| 2.10 | 修改 | `frontend/app/page.tsx`（历史记录面板） |
| 2.11 | 修改 | `backend/main.py`（重写 analyze_account） |
| 2.12 | 修改 | `frontend/app/page.tsx`（账号分析入口） |
| 3.01 | 新建 | `frontend/app/cases/[slug]/page.tsx` |
| 3.02 | 新建 | `frontend/app/cases/page.tsx` |
| 3.03 | 新建 | `frontend/app/not-found.tsx` |
| 3.04 | 修改 | `backend/main.py`（管理后台 6 个接口） |
| 3.05 | 修改 | `backend/main.py`（Sitemap 增强） |
| 3.06 | 修改 | `backend/main.py` + `deploy/nginx.conf` |
| 3.07 | 修改 | `backend/scripts/report_generator.py` |
| 3.08 | 修改 | `frontend/app/layout.tsx` + `deploy/docker-compose.yml` |
| 4.01 | 修改 | `backend/.env.example` |
| 4.02 | 修改 | `.gitignore` |
| 4.03 | 操作 | Git 初始化 + GitHub 推送 |
| 4.04 | 修改 | `deploy/docker-compose.yml` |
| 4.05 | 修改 | `deploy/nginx.conf` |
| 4.06 | 修改 | `backend/main.py`（CORS） + `backend/.env.example` |
| 4.07 | 新建 | `.github/workflows/deploy.yml` |
| 4.08 | 新建 | `frontend/Dockerfile` |

---

**— 蓝图文档结束 —**
