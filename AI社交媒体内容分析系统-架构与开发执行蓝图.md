# AI 社交媒体内容分析系统 - 架构与开发执行蓝图 (MVP)

⚠️ 致接手此文档的 AI 开发者 (Agent Instructions):
本文档是该项目的最高执行准则。项目运行于资源受限的个人轻量级云服务器。
核心原则： 极简主义、零冗余依赖、第一性原理驱动。绝对禁止引入重量级数据库（如 MySQL/PostgreSQL）、禁止引入外部云存储 SDK（如 AWS S3/阿里云 OSS）、禁止开发复杂的账号鉴权系统。严格遵守本文档定义的边界。

## 1. 系统概览 (System Overview)
本项目是一个自动化数据管道，旨在抓取海外第三方 API 提供的抖音/小红书内容，将其转换为大模型可读取的格式，通过火山引擎豆包大模型（带预设 Prompt）进行深度分析，最终通过 SSE 流式输出给用户。同时，系统将在后台自动挖掘高频查询数据，生成定期报告，辅助管理员人工筛选并创作 GEO（生成式引擎优化）结构化网页内容，以获取自然流量。

## 2. 技术栈约束 (Tech Stack Constraints)
- **前端展示层**: Next.js (App Router, React) + Tailwind CSS
  要求: 必须使用 Server-Side Rendering (SSR) 以支持 SEO。
- **后端 API 层**: Python + FastAPI
  要求: 负责路由转发、第三方 API 鉴权、文件流中转、SSE (Server-Sent Events) 流式输出、定期数据报告生成。
  必须集成轻量级限流中间件（如 `slowapi`），对分析类接口按 IP 或 UUID 限流（建议: 单 IP 每分钟不超过 5 次分析请求），防止第三方 API 额度和豆包 token 被恶意耗尽。
- **数据库层**: SQLite 3 (单文件本地库)
  要求: 仅存储纯文本、JSON 字符串和 Markdown，绝对禁止存储二进制媒体文件。
- **部署环境**: Docker + Docker Compose + Nginx (部署于腾讯云轻量应用服务器)
  Nginx SSE 必要配置: 反向代理 FastAPI 的 SSE 接口时，必须在对应 `location` 块中显式添加以下指令，否则流式输出将被缓冲后一次性返回，前端无法实现打字机效果：
  ```nginx
  proxy_buffering off;
  proxy_cache off;
  proxy_set_header Connection '';
  proxy_http_version 1.1;
  chunked_transfer_encoding off;
  ```

## 3. UI/UX 风格同步指令 (UI/UX Synchronization Protocol)
⚠️ AI 开发者注意：
本项目将内嵌或链接至用户的个人主页。风格必须为 “极简主义 (Minimalist) + 新野兽派 (Neo-Brutalism)”。
执行步骤:
1. 在生成任何前端组件之前，请求用户提供其个人网站的 URL 或屏幕截图。
2. 分析并提取其设计系统：包括高对比度纯色背景、粗犷的黑色边框 (Border: 2px/4px solid black)、锐利的直角或极小的圆角 (rounded-none 或 rounded-sm)、大号无衬线字体。
3. 所有的 Button、Input、Card 组件必须遵循上述提取到的 Design Token，不可使用默认的现代柔和风格 (如默认的 shadcn/ui 或 Material Design)。

## 4. 核心工作流设计 (Core Data Pipelines)

### Workflow A: 单条内容 AI 分析流 (Single Content Analysis)
1. **触发**: 用户在前端输入作品 URL，生成 UUID (localStorage) 一并提交。前端显示硬朗风格的 Loading 状态。
2. **获取数据**: FastAPI 调用第三方 API，获取内容元数据（文案、标签、评论等）和媒体原始链接（视频/图片 CDN 链接）。
3. **多模态资源本地中转 (关键解决防盗链与解析)**:
   - FastAPI 验证原始媒体链接。如果大模型无法直接读取，将文件流式下载到宿主机映射的本地目录 `/app/public/temp_media/`。
   - 使用极简压缩算法（如图片降分辨率，视频仅提取前 3 帧截图），防止消耗过多出网带宽。
   - 通过 Nginx 暴露该本地文件，生成临时公网 URL (如 `https://domain.com/temp/{uuid4}.jpg`)。文件名必须使用 UUID4 或 SHA256 哈希命名，禁止使用自增 ID 或可预测的文件名。Nginx 对应 `location /temp/` 必须设置 `autoindex off;` 防止目录遍历。
4. **组装与分析**: 将”元数据文本 + 媒体资源 + 用户可编辑的系统预设 Prompt” 提交至火山引擎豆包 API。
   ⚠️ 多模态输入兼容性: 豆包 API 的多模态接口可能要求 base64 编码图片而非外部 URL。Phase 1 开发前必须先验证豆包视觉理解接口的实际输入格式。若不支持 URL 读取，则改为：FastAPI 读取本地临时文件 -> base64 编码 -> 作为 `image_url` 的 `data:image/jpeg;base64,...` 格式传入。此时临时文件无需通过 Nginx 暴露公网访问，仅作为本地中转缓存。
5. **SSE 流式返回**: FastAPI 将豆包的响应以 `text/event-stream` 格式逐字推送到 Next.js 前端打字机组件。
6. **落库**: 分析完成后，将 UUID、原始 URL、获取的文本 JSON、分析结果 MD 存入 SQLite。

### Workflow B: AI 账号对标分析流 (Account Benchmarking)
1. **触发**: 用户输入主页 URL。
2. **聚合抓取**: 获取主页基础数据及近期 5 条作品数据。
3. **数据降噪**: 后端脚本剥离冗余信息，仅保留 5 条作品的“标题、获赞数、Top 3 评论”，拼接为紧凑的高密度文本。
4. **AI 分析与输出**: 同 Workflow A，传入专门的账号拆解 Prompt，通过 SSE 输出。

### Workflow C: 高潜内容挖掘与人工 GEO 沉淀流 (High-Potential Content Mining & Manual GEO Pipeline)
1. **定期扫描与报告生成**: Python 后台设置定时任务（如每周），扫描 SQLite 中高频访问或管理员标记为 `candidate_for_blog=True` 的分析记录。将这些核心数据（URL、抓取数据概要、原生分析结果）导出为本地 CSV/Excel 报告，或在简单的受保护 API 接口中输出汇总 JSON 供查阅。
2. **人工筛选与创作**: 管理员定期查阅报告，人工挑选有价值的案例。结合提取到的客观数据，人工撰写符合 GEO 规范的博客文章（要求包含 100 字 TL;DR 摘要、Q&A 问答句式的 H2 标题、明确的实体和数据指标）。
3. **人工发布入库**: 管理员通过预留的简单后台接口或直接操作数据库，将撰写完成的 Markdown 文本录入对应记录的 `geo_blog_md` 字段，设定友好的 `slug` 和 SEO 标签，并将 `is_public` 更新为 `True`。
4. **前端 SSR 与 SEO 收录**: Next.js 动态路由 `/cases/[slug]` 读取标记为公开的记录，将其渲染为 HTML，并注入 JSON-LD Schema (Article类型)。系统根据 `is_public=True` 的记录自动更新 `/sitemap.xml`，等待搜索引擎抓取。

## 5. 数据库设计 (SQLite Schema)
**表名: analysis_records**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| user_uuid | TEXT | 浏览器生成的唯一标识符 (追踪需求挖掘) |
| task_type | TEXT | 'single_content' 或 'account_analysis' |
| source_url | TEXT | 用户输入的原始链接 |
| raw_data_json | TEXT | 第三方API返回的文本数据 (文案/评论/标签) |
| ai_analysis | TEXT | 豆包生成的原生 Markdown 分析结果 |
| geo_blog_md | TEXT | 人工创作的 GEO 友好格式文章 (初始为 NULL，供后续发布填入) |
| slug | TEXT | SEO 友好的 URL 路径 (如 analyze-douyin-beauty-xxx) |
| seo_title | TEXT | 网页 Title 标签内容 |
| seo_desc | TEXT | 网页 Meta Description 内容 |
| candidate_for_blog | BOOLEAN | 管理员标记为 GEO 候选内容 (默认 False，供 Workflow C 定期扫描筛选) |
| is_public | BOOLEAN | 是否对搜索引擎公开 (默认 False) |
| created_at | DATETIME | 创建时间 |

## 6. 基础设施与资源防爆指令 (Infrastructure Safeguards)
⚠️ AI 开发者注意： 必须在 Dockerfile 或部署脚本中实现以下安全机制，否则服务器将面临存储和带宽耗尽风险。

- **存储回收机制 (Garbage Collection)**:
  必须在部署脚本中写入 Cron 任务：`0 * * * * find /app/public/temp_media/ -type f -mmin +1440 -delete`。确保临时媒体文件存活周期严格限制在 24 小时内。

- **带宽保护**:
  在 FastAPI 下载第三方媒体流时，设置 Content-Length 阈值（如最大 20MB）。超出则拒绝处理或仅下载部分字节（若适用）。
  视频处理降级方案：优先考虑不下载视频实体，仅向豆包传递视频封面图 URL 和文案。只有当用户明确要求深度视频画面分析时，再触发下载。

- **SQLite 数据备份**:
  必须在部署脚本中写入 Cron 任务：`0 3 * * * cp /app/data/db.sqlite3 /app/data/backups/db_$(date +\%Y\%m\%d).sqlite3 && find /app/data/backups/ -type f -mtime +7 -delete`。每日凌晨 3 点自动备份数据库文件，保留最近 7 天的备份副本。备份目录 `/app/data/backups/` 需在 Docker Volume 中持久化映射。

## 7. 分阶段开发提示 (Development Phases)
请 AI 代理按照以下顺序进行开发并与用户确认：
1. **Phase 1: 核心管道跑通** -> 编写 FastAPI 脚本，打通 "第三方 API 获取 -> 存入本地 /temp_media -> 构造 URL -> 提交豆包 API" 的数据链路。
2. **Phase 2: 流式输出与前端集成** -> 实现 FastAPI 的 StreamingResponse，搭建 Next.js 框架，并完成与用户个人网站风格的同步。
3. **Phase 3: 数据库与内容挖掘体系** -> 配置 SQLite 存储基础记录，实现后台高潜记录的定期报告导出逻辑（如 CSV 导出接口），最后打通 Next.js 基于发布状态的动态路由渲染及 Sitemap 机制。