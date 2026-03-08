# AI社交媒体内容分析系统

基于 FastAPI + Next.js 的抖音/小红书内容智能分析系统，采用"极简主义 + 新野兽派"设计风格。

## 项目结构

```
.
├── backend/                 # 后端API服务 (Python + FastAPI)
│   ├── main.py             # 主入口文件
│   ├── requirements.txt    # Python依赖
│   ├── .env.example        # 环境变量模板
│   └── Dockerfile          # 后端Docker配置
├── frontend/               # 前端应用 (Next.js + Tailwind CSS)
│   ├── app/                # App Router页面
│   ├── package.json        # Node依赖
│   ├── tailwind.config.ts  # Tailwind配置
│   ├── next.config.js      # Next.js配置
│   └── Dockerfile          # 前端Docker配置
├── deploy/                 # 部署配置
│   ├── docker-compose.yml  # Docker Compose配置
│   └── nginx.conf          # Nginx配置
├── data/                   # 数据存储 (SQLite + 备份)
├── temp_media/             # 临时媒体文件 (自动清理)
├── docs/                   # 项目文档
└── README.md               # 项目说明
```

## 核心功能

### Phase 1 (已完成)
- ✅ 抖音/小红书链接解析与数据获取
- ✅ 媒体文件自动下载与压缩处理
- ✅ 第三方API (TikHub) 集成
- ✅ 基础FastAPI框架搭建
- ✅ 新野兽派风格前端页面
- ✅ SSE流式输出接口
- ✅ SQLite数据库设计

### Phase 2 (开发中)
- [ ] 火山引擎豆包API集成
- [ ] 前端流式输出打字机效果
- [ ] 账号对标分析功能
- [ ] 用户历史记录管理

### Phase 3 (规划中)
- [ ] 高潜内容挖掘与报告生成
- [ ] GEO博客内容管理系统
- [ ] 动态路由与SEO优化
- [ ] Sitemap自动生成
- [ ] 后台管理界面

## 快速开始

### 本地开发

#### 后端启动
```bash
cd backend
# 安装依赖
pip install -r requirements.txt
# 复制环境变量并配置
cp .env.example .env
# 编辑 .env 填入API密钥
# 启动服务
python main.py
```

#### 前端启动
```bash
cd frontend
# 安装依赖
npm install
# 启动开发服务器
npm run dev
```

### Docker部署

```bash
# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入API密钥

# 启动服务
cd deploy
docker-compose up -d
```

## 环境变量配置

### 后端环境变量 (.env)
```env
# 第三方API配置
TIKHUB_API_KEY=your_tikhub_api_key
TIKHUB_BASE_URL=https://api.tikhub.io

# 火山引擎豆包API配置
VOLC_ACCESS_KEY=your_volc_access_key
VOLC_SECRET_KEY=your_volc_secret_key
VOLC_REGION=cn-beijing
DOUBAO_MODEL=doubao-seed-code

# 系统配置
TEMP_MEDIA_DIR=./temp_media
MAX_FILE_SIZE_MB=20
RATE_LIMIT_PER_MINUTE=5
DEBUG=false
```

## API接口

### 分析接口
- `POST /api/analyze` - 分析单条内容
- `POST /api/analyze/account` - 分析账号

### 公开接口
- `GET /api/public/cases` - 获取公开案例列表
- `GET /api/public/cases/{slug}` - 获取案例详情
- `GET /api/sitemap.xml` - 获取站点地图

## 安全机制

1. **存储自动清理**：临时媒体文件24小时自动删除
2. **数据备份**：数据库每日自动备份，保留7天
3. **流量限制**：分析接口单IP每分钟限制5次请求
4. **文件大小限制**：单个媒体文件最大20MB
5. **目录保护**：临时文件目录禁止遍历

## 设计风格

本项目采用**新野兽派 (Neo-Brutalism)** 设计风格：
- 高对比度黑白配色
- 4px粗黑边框
- 无圆角或极小圆角
- 8px硬阴影
- 大号无衬线字体
- 强烈的视觉冲击力

## 技术栈

**后端：**
- Python 3.11
- FastAPI 0.110
- Uvicorn ASGI服务器
- SQLite 3
- OpenCV / Pillow 图像处理
- SlowAPI 限流

**前端：**
- Next.js 14 (App Router)
- React 18
- Tailwind CSS 3
- TypeScript
- SSE 流式输出

**部署：**
- Docker + Docker Compose
- Nginx 反向代理
- 腾讯云轻量应用服务器

## 开发规范

1. 严格遵循架构文档中的技术栈约束
2. 禁止引入重量级依赖 (MySQL, Redis等)
3. 所有组件必须符合新野兽派设计风格
4. 临时文件必须存放在 `temp_media/` 目录
5. 敏感信息必须通过环境变量配置，禁止硬编码

## 维护说明

### 日志查看
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend
```

### 数据备份
数据库自动备份在 `data/backups/` 目录，保留最近7天的备份文件。

### 临时文件清理
系统自动每小时清理一次24小时前的临时文件，无需手动干预。

## 许可证

MIT License
