<p align="center">
  <a href="DEVELOPMENT_GUIDE.md">English</a> | <a href="DEVELOPMENT_GUIDE_JA.md">日本語</a> | <strong>简体中文</strong>
</p>

# BookWith 开发环境设置指南

本指南为 BookWith 项目的贡献者和开发者提供详细的开发环境设置说明。

## 📚 目录

- [项目概述](#项目概述)
- [前提条件](#前提条件)
- [快速开始](#快速开始)
- [详细环境设置步骤](#详细环境设置步骤)
- [开发工作流程](#开发工作流程)
- [故障排除](#故障排除)
- [目录结构](#目录结构)
- [贡献指南](#贡献指南)

## 🎯 项目概述

BookWith 是一个由 AI 驱动的下一代基于浏览器的 ePub 阅读器。它通过与理解图书内容的 AI 助手进行交互式对话，提供更丰富的阅读体验。

### 架构概览

```
┌─────────────────────────────────────────────────────────┐
│  前端 (Next.js + TypeScript)                           │
│  · Pages Router                                        │
│  · 使用ePub.js进行渲染                                  │
│  · 实时AI聊天                                          │
└─────────────────────────────────────────────────────────┘
                           ↓ API
┌─────────────────────────────────────────────────────────┐
│  后端 (FastAPI + Python)                               │
│  · DDD分层架构                                         │
│  · 使用LangChain进行AI集成                              │
│  · 内存管理系统                                        │
└─────────────────────────────────────────────────────────┘
                           ↓ 持久化
┌─────────────────────────────────────────────────────────┐
│  数据存储                                              │
│  · Supabase (主数据库)                                 │
│  · Weaviate (向量数据库)                                │
│  · GCS模拟器 (开发存储)                                 │
└─────────────────────────────────────────────────────────┘
```

## 🛠 前提条件

### 必需工具

| 工具           | 版本      | 检查方式                 |
| -------------- | --------- | ------------------------ |
| Node.js        | ≥ 18.0.0  | `node -v`                |
| pnpm           | 9.15.4    | `pnpm -v`                |
| Python         | ≥ 3.13    | `python --version`       |
| uv             | 最新版    | `uv --version`           |
| Docker         | 最新版    | `docker --version`       |
| Docker Compose | v2 或更高 | `docker compose version` |

### 安装

#### 安装 pnpm

```bash
# 如果已安装Node.js
yarn global add pnpm@9.15.4
# 或使用Homebrew (macOS)
brew install pnpm
```

#### 安装 uv

```bash
# 官方安装器
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或使用Homebrew (macOS)
brew install uv
```

## 🚀 快速开始

您可以使用以下命令快速启动开发环境：

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/bookwith.git
cd bookwith

# 2. 一次性安装所有依赖（JS via pnpm + Python via uv）
pnpm setup

# 3. 设置环境变量
cp apps/api/src/config/.env.example apps/api/src/config/.env
# 编辑 apps/api/src/config/.env 并添加您的 API 密钥

# 4. 启动Supabase (需要单独安装)
supabase start

# 5. 在仓库根目录一键启动（Turborepo 并行启动 Docker services + FastAPI + Next.js）
pnpm dev
```

#### 选择性启动 / 安装

| 命令 | 启动 / 执行内容 |
| --- | --- |
| `pnpm setup` | 一次性安装 JS + Python 依赖（首次 checkout 时运行） |
| `pnpm setup:api` | 仅重新安装 Python 依赖（`uv.lock` 变更时） |
| `pnpm dev` | Docker services + FastAPI + Next.js |
| `pnpm dev:reader` | 仅 Next.js |
| `pnpm dev:api` | 仅 Docker services + FastAPI |
| `pnpm dev:services` | 仅 Docker services（Weaviate + GCS emulator） |

可访问的端点：

- 前端：http://localhost:7127
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 📋 详细环境设置步骤

### 1. 克隆仓库并安装依赖

```bash
# 从GitHub克隆
git clone https://github.com/your-org/bookwith.git
cd bookwith

# 一次性安装所有依赖（JS via pnpm + Python via uv）
pnpm setup
```

> `pnpm setup` 内部执行 `pnpm install && pnpm -F @flow/api run setup`。
> 当 `uv.lock` 变更后（例如 git pull 之后），可使用 `pnpm setup:api` 仅重新同步 Python 依赖。

### 2. 配置环境变量

#### 后端(API)环境变量

```bash
cd apps/api
cp src/config/.env.example src/config/.env
```

编辑`.env`文件并设置以下内容：

```env
# 基本设置
PORT=8000

# 必需：OpenAI API密钥
OPENAI_API_KEY=sk-...  # 从您的OpenAI仪表板获取

# 可选：LangSmith (用于追踪)
LANGCHAIN_API_KEY=ls__...  # 从LangSmith获取
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=bookwith

# 数据库 (Supabase本地默认端口54322)
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres

# 存储 (使用Docker Compose运行时使用默认值)
GCS_EMULATOR_HOST=http://127.0.0.1:4443

# 内存设置 (您可以从默认值开始)
MEMORY_BUFFER_SIZE=10
MEMORY_SUMMARIZE_THRESHOLD=50
MEMORY_CHAT_RESULTS=3
MAX_PROMPT_TOKENS=8192
```

#### 前端环境变量 (如有需要)

```bash
cd apps/reader
cp .env.example .env
```

### 3. 启动 Docker 环境

#### 启动 PostgreSQL 数据库 (Supabase)

该项目使用 Supabase 作为 PostgreSQL 数据库。在本地启动 Supabase：

```bash
# 如果您已全局安装Supabase或在其他项目中安装
# npx supabase start
# 或简单地使用
supabase start

# 检查Supabase状态
supabase status
```

**注意：** `apps/api/docker-compose.yml`不包含 PostgreSQL。需要单独启动 Supabase。

#### 启动其他 Docker 服务

```bash
# 在仓库根目录（推荐）
pnpm dev:services

# 或直接调用 Make
cd apps/api && make docker.up
```

这将启动以下服务：

- **Weaviate** (向量数据库): http://localhost:8080
- **GCS 模拟器**: http://localhost:4443

### 4. 初始化数据库

首次运行或数据库模式更改时：

```bash
cd apps/api

# 在Python解释器中运行
uv run python
>>> from src.config.db import init_db
>>> init_db()
>>> exit()
```

这将根据 SQLAlchemy 模型定义自动创建所需的表。

### 5. 启动后端(API)

```bash
# 依赖已通过 `pnpm setup` 安装。
# 如果跳过了 `pnpm setup`，可运行 `pnpm setup:api` 仅安装 Python 依赖。

# 启动开发服务器（Docker services + FastAPI）
pnpm dev:api
```

API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 6. 启动前端

打开新终端：

```bash
# 从仓库根目录
pnpm openapi        # 重新生成 OpenAPI 类型（首次 / API schema 变更后）
pnpm dev:reader     # 启动 Next.js 开发服务器
```

前端：http://localhost:7127

> ✨ 或者只需在仓库根目录运行 **`pnpm dev`**，Turborepo 会一起启动 Docker services / FastAPI / Next.js。

### 7. 验证一切正常工作

1. 在浏览器中导航到 http://localhost:7127。
2. 拖放一个 ePub 文件或选择一个进行导入。
3. 书籍加载后，在右侧面板与 AI 聊天。

## 💻 开发工作流程

### 代码更改流程

#### 后端开发

1. **进行代码更改**

   ```bash
   # 遵循DDD层次
   # src/domain/          - 实体和值对象
   # src/usecase/         - 业务逻辑
   # src/infrastructure/  - 外部集成
   # src/presentation/    - API端点
   ```

2. **类型检查和代码检查**

   ```bash
   # 在仓库根目录（覆盖 api & reader）
   pnpm typecheck
   pnpm lint
   pnpm lint:fix     # 自动修复
   # 仅 API
   cd apps/api && make lint  # MyPy + pre-commit
   ```

3. **重启 API**
   FastAPI 支持自动重载，因此更改通常会自动生效。

#### 前端开发

1. **进行代码更改**

   ```bash
   # 关键目录
   # src/components/  - React组件
   # src/hooks/       - 自定义Hooks
   # src/pages/       - 页面组件
   # src/lib/         - 工具类
   ```

2. **类型检查**

   ```bash
   pnpm typecheck                       # 跨工作区
   pnpm -F @flow/reader run typecheck   # 仅 reader
   ```

3. **热重载**
   Next.js 检测到更改时会自动重载。

### 构建和测试

#### 完整构建

```bash
# 从仓库根目录（不包含 vendored 的 @flow/epubjs）
pnpm build
```

#### 运行测试 / 代码检查

```bash
# 整个工作空间
pnpm test
pnpm lint
pnpm lint:fix
pnpm typecheck

# 仅 API
cd apps/api && make lint

# 仅前端
cd apps/reader && pnpm lint
```

#### 清理缓存

```bash
pnpm clean   # 删除 .next / .turbo / __pycache__ / .mypy_cache 等
```

### 更新 OpenAPI 模式

如果您更改了 API 类型：

```bash
# 1) 在另一个终端启动 API
pnpm dev:api

# 2) 从仓库根目录重新生成类型
pnpm openapi
```

## 🔧 故障排除

### 常见问题及解决方案

#### 1. `pnpm install`期间出现错误

```bash
# 清除缓存
pnpm store prune

# 删除node_modules并重新安装
rm -rf node_modules pnpm-lock.yaml
pnpm i
```

#### 2. Docker 服务启动失败

```bash
# 停止并删除现有容器
cd apps/api
docker compose down -v

# 检查端口
lsof -i :8080  # Weaviate
lsof -i :4443  # GCS模拟器

# 重启
make docker.up
```

#### 3. API 启动失败

```bash
# 重建 uv 环境
cd apps/api
rm -rf .venv
uv sync --frozen

# 验证环境变量
cat src/config/.env  # 检查API密钥
```

#### 4. 前端 API 通信错误

```bash
# 确保API正在运行
curl http://localhost:8000/health

# 对于CORS错误，检查API CORS设置
```

#### 5. Weaviate 连接错误

```bash
# 检查Weaviate是否运行
curl http://localhost:8080/v1/.well-known/ready

# 查看日志
cd apps/api
docker compose logs weaviate
```

#### 6. PostgreSQL/Supabase 连接错误

```bash
# 检查Supabase是否运行
supabase status

# 验证端口54322被使用
lsof -i :54322

# 连接测试
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -c "SELECT 1"

# 如果Supabase未运行
supabase start
```

#### 7. 缺少数据库表

```bash
# 初始化数据库
cd apps/api
uv run python
>>> from src.config.db import init_db
>>> init_db()
>>> exit()
```

### 调试技巧

1. **检查 API 日志**

   ```bash
   # FastAPI日志显示在终端中
   # 如果启用了LangSmith追踪，也检查追踪信息
   ```

2. **浏览器开发者工具**

   - 使用网络标签检查 API 请求。
   - 检查控制台的错误消息。

3. **Docker 日志**

   ```bash
   cd apps/api
   docker compose logs -f      # 所有服务
   docker compose logs -f weaviate  # 仅Weaviate
   ```

## 📁 目录结构

### 顶级结构

```
bookwith/
├── apps/
│   ├── api/          # FastAPI后端
│   │   ├── src/
│   │   │   ├── domain/          # 领域层 (DDD)
│   │   │   ├── usecase/         # 用例层
│   │   │   ├── infrastructure/  # 基础设施层
│   │   │   ├── presentation/    # 表示层
│   │   │   └── config/          # 配置文件
│   │   ├── Makefile             # 辅助命令
│   │   └── docker-compose.yml   # Docker配置
│   │
│   └── reader/       # Next.js前端
│       ├── src/
│       │   ├── components/      # UI组件
│       │   ├── hooks/           # 自定义hooks
│       │   ├── pages/           # 页面组件
│       │   └── lib/             # 工具类
│       └── package.json
│
├── packages/         # 共享包 (未来扩展)
├── docs/             # 文档
├── package.json      # Monorepo配置
├── pnpm-workspace.yaml
└── turbo.json        # Turbo配置
```

### 关键后端文件

- `apps/api/src/domain/` – 实体、值对象、仓储接口
- `apps/api/src/usecase/` – 业务逻辑
- `apps/api/src/infrastructure/memory/` – AI 内存管理
- `apps/api/src/presentation/api/` – API 端点

### 关键前端文件

- `apps/reader/src/components/viewlets/chat/` – AI 聊天 UI
- `apps/reader/src/components/Reader.tsx` – 核心 ePub 阅读器
- `apps/reader/src/lib/apiHandler/` – API 通信逻辑
- `apps/reader/src/models/reader.ts` – 状态管理 (Valtio)

## 🤝 贡献指南

### 编码标准

#### Python (后端)

1. **格式化器：** Black
2. **类型检查：** MyPy，无错误
3. **命名约定：**
   - 类：PascalCase
   - 函数和变量：snake_case
   - 常量：UPPER_SNAKE_CASE

```python
# 好的示例
class BookRepository(ABC):
    def find_by_id(self, book_id: BookId) -> Optional[Book]:
        pass

# 不好的示例
class bookRepository:
    def findById(self, bookId):  # 没有类型提示
        pass
```

#### TypeScript (前端)

1. **格式化器：** Prettier
2. **代码检查器：** 遵循 ESLint 配置
3. **严格类型：** `strict: true`

```typescript
// 好的示例
interface BookProps {
  id: string
  title: string
  onSelect?: (id: string) => void
}

// 不好的示例
interface BookProps {
  id: any // 避免使用any
  title: string
}
```

### 提交指南

我们推荐使用约定式提交：

```bash
# 格式
<type>(<scope>): <subject>

# 示例
feat(reader): Add streaming support for AI chat
fix(api): Fix memory leak
docs: Add environment setup guide
refactor(domain): Improve validation in Book entity
test(usecase): Add unit tests for CreateBookUseCase
```

#### 类型列表

- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 仅文档
- `style`: 不影响代码含义的更改
- `refactor`: 既不修复错误也不添加功能的代码更改
- `test`: 添加或修正测试
- `chore`: 对构建过程或辅助工具的更改

### Pull 请求

1. **分支命名：** `feature/xxx`, `fix/xxx`, `docs/xxx`
2. **PR 模板：** 包括以下内容
   - 更改摘要
   - 相关问题编号
   - 如何测试
   - 截图 (对于 UI 更改)

### 审查检查清单

- [ ] 保持类型安全
- [ ] 遵循 DDD 原则 (后端)
- [ ] 适当的错误处理
- [ ] 无负面性能影响
- [ ] 适当时添加测试

## 📚 参考资源

### 官方文档

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Next.js 文档](https://nextjs.org/docs)
- [Weaviate 文档](https://weaviate.io/developers/weaviate)
- [LangChain 文档](https://python.langchain.com/)

### 项目特定文档

- [CLAUDE.md](../CLAUDE.md) – AI 助手指南
- [backend-architecture.md](./backend-architecture.md) – 后端架构详情
- [frontend-directory-structure.md](./frontend-directory-structure.md) – 前端结构详情

### 有用工具

- [Swagger 编辑器](https://editor.swagger.io/) – OpenAPI 模式编辑
- [Weaviate 控制台](http://localhost:8080/v1/console) – 向量数据库管理
- [React 开发者工具](https://react.dev/learn/react-developer-tools) – React 调试

## 🆘 支持

如果您仍有问题：

1. 搜索现有的[GitHub 问题](https://github.com/your-org/bookwith/issues)
2. 创建新问题 (包含重现步骤)
3. 在[讨论区](https://github.com/your-org/bookwith/discussions)询问

---

快乐编程！ 🚀
