<p align="center">
   <strong>English</strong> | <a href="DEVELOPMENT_GUIDE_JA.md">日本語</a> | <a href="DEVELOPMENT_GUIDE_ZH.md">简体中文</a>
</p>

# BookWith Development Environment Setup Guide

This guide provides detailed instructions on how to set up a development environment for contributors and developers of the BookWith project.

## 📚 Table of Contents

- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Environment Setup Steps](#detailed-environment-setup-steps)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Directory Structure](#directory-structure)
- [Contribution Guidelines](#contribution-guidelines)

## 🎯 Project Overview

BookWith is a next-generation browser-based ePub reader powered by AI. It offers a richer reading experience through interactive conversations with an AI assistant that understands the book's content.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (Next.js + TypeScript)                       │
│  · Pages Router                                        │
│  · Rendering with ePub.js                              │
│  · Real-time AI Chat                                   │
└─────────────────────────────────────────────────────────┘
                           ↓ API
┌─────────────────────────────────────────────────────────┐
│  Backend (FastAPI + Python)                            │
│  · DDD Layered Architecture                            │
│  · AI Integration with LangChain                       │
│  · Memory Management System                            │
└─────────────────────────────────────────────────────────┘
                           ↓ Persistence
┌─────────────────────────────────────────────────────────┐
│  Data Stores                                           │
│  · Supabase (Primary DB)                               │
│  · Weaviate (Vector DB)                                │
│  · GCS Emulator (Development Storage)                  │
└─────────────────────────────────────────────────────────┘
```

## 🛠 Prerequisites

### Required Tools

| Tool           | Version     | How to Check             |
| -------------- | ----------- | ------------------------ |
| Node.js        | ≥ 18.0.0    | `node -v`                |
| pnpm           | 9.15.4      | `pnpm -v`                |
| Python         | ≥ 3.13      | `python --version`       |
| uv             | Latest      | `uv --version`           |
| Docker         | Latest      | `docker --version`       |
| Docker Compose | v2 or later | `docker compose version` |

### Installation

#### Install pnpm

```bash
# If Node.js is already installed
yarn global add pnpm@9.15.4
# or using Homebrew (macOS)
brew install pnpm
```

#### Install uv

```bash
# Official installer
curl -LsSf https://astral.sh/uv/install.sh | sh
# or using Homebrew (macOS)
brew install uv
```

## 🚀 Quick Start

You can spin up the development environment quickly with the following commands:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/bookwith.git
cd bookwith

# 2. Install all dependencies (JS via pnpm + Python via uv)
pnpm setup

# 3. Set environment variables
cp apps/api/src/config/.env.example apps/api/src/config/.env
# Edit apps/api/src/config/.env and add your API keys

# 4. Start Supabase (needs to be installed separately)
supabase start

# 5. Start everything from the repo root in one command
#    (Docker services + FastAPI + Next.js are launched in parallel via Turborepo)
pnpm dev
```

#### Selective startup

| Command | Starts |
| --- | --- |
| `pnpm setup` | Install JS + Python dependencies (run once on first checkout) |
| `pnpm setup:api` | Re-install Python dependencies only (when `uv.lock` changes) |
| `pnpm dev` | Docker services + FastAPI + Next.js |
| `pnpm dev:reader` | Next.js only |
| `pnpm dev:api` | Docker services + FastAPI only |
| `pnpm dev:services` | Docker services (Weaviate + GCS emulator) only |

Accessible endpoints:

- Frontend: http://localhost:7127
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📋 Detailed Environment Setup Steps

### 1. Clone the Repository and Install Dependencies

```bash
# Clone from GitHub
git clone https://github.com/your-org/bookwith.git
cd bookwith

# Install all dependencies (JS via pnpm + Python via uv)
pnpm setup
```

> `pnpm setup` is equivalent to `pnpm install && pnpm -F @flow/api run setup`.
> Re-run `pnpm setup:api` whenever `uv.lock` changes (e.g. after a pull) to refresh the Python virtual environment.

### 2. Configure Environment Variables

#### Backend (API) Environment Variables

```bash
cd apps/api
cp src/config/.env.example src/config/.env
```

Edit the `.env` file and set the following:

```env
# Basic Settings
PORT=8000

# Required: OpenAI API Key
OPENAI_API_KEY=sk-...  # Obtain from your OpenAI dashboard

# Optional: LangSmith (for tracing)
LANGCHAIN_API_KEY=ls__...  # Obtain from LangSmith
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=bookwith

# Database (Supabase local default port 54322)
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres

# Storage (use defaults when running with Docker Compose)
GCS_EMULATOR_HOST=http://127.0.0.1:4443

# Memory Settings (you can start with default values)
MEMORY_BUFFER_SIZE=10
MEMORY_SUMMARIZE_THRESHOLD=50
MEMORY_CHAT_RESULTS=3
MAX_PROMPT_TOKENS=8192
```

#### Frontend Environment Variables (if needed)

```bash
cd apps/reader
cp .env.example .env
```

### 3. Start Docker Environment

#### Start the PostgreSQL Database (Supabase)

This project uses Supabase as the PostgreSQL database. Start Supabase locally:

```bash
# If you have Supabase installed globally or in another project
# npx supabase start
# or simply
supabase start

# Check Supabase status
supabase status
```

**Note:** `apps/api/docker-compose.yml` does not include PostgreSQL. Start Supabase separately.

#### Start Other Docker Services

```bash
# From the repo root
pnpm dev:services

# (or directly via Make from apps/api)
cd apps/api && make docker.up
```

This will start the following services:

- **Weaviate** (Vector DB): http://localhost:8080
- **GCS Emulator**: http://localhost:4443

### 4. Initialize the Database

On first run or whenever the database schema changes:

```bash
cd apps/api

# Run in a Python interpreter
uv run python
>>> from src.config.db import init_db
>>> init_db()
>>> exit()
```

This automatically creates the required tables based on SQLAlchemy model definitions.

### 5. Start the Backend (API)

```bash
# Only the first time: dependencies are already installed via `pnpm setup`.
# If you skipped `pnpm setup`, run `pnpm setup:api` to install Python deps.

# Start the development server (Docker services + FastAPI)
pnpm dev:api
```

API Documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 6. Start the Frontend

Open a new terminal:

```bash
# From the repo root
pnpm openapi        # Regenerate OpenAPI types (first time / after API schema changes)
pnpm dev:reader     # Start the Next.js dev server
```

Frontend: http://localhost:7127

> ✨ Or, run **`pnpm dev`** at the repo root once and Turborepo will start Docker services, FastAPI, and Next.js together.

### 7. Verify Everything Works

1. Navigate to http://localhost:7127 in your browser.
2. Drag & drop an ePub file or select one to import.
3. Once the book loads, chat with the AI in the panel on the right.

## 💻 Development Workflow

### Code Change Flow

#### Backend Development

1. **Make Code Changes**

   ```bash
   # Follow DDD layers
   # src/domain/          - Entities & Value Objects
   # src/usecase/         - Business Logic
   # src/infrastructure/  - External Integrations
   # src/presentation/    - API Endpoints
   ```

2. **Type Check & Lint**

   ```bash
   # From the repo root (covers both api & reader)
   pnpm typecheck
   pnpm lint
   pnpm lint:fix   # auto-fix
   # API only
   cd apps/api && make lint  # MyPy + pre-commit
   ```

3. **Restart API**
   FastAPI supports auto-reload, so changes are usually picked up automatically.

#### Frontend Development

1. **Make Code Changes**

   ```bash
   # Key Directories
   # src/components/  - React Components
   # src/hooks/       - Custom Hooks
   # src/pages/       - Page Components
   # src/lib/         - Utilities
   ```

2. **Type Check**

   ```bash
   pnpm typecheck                       # cross-workspace
   pnpm -F @flow/reader run typecheck   # reader only
   ```

3. **Hot Reload**
   Next.js automatically reloads when it detects changes.

### Build & Test

#### Full Build

```bash
# From repository root (excludes the vendored @flow/epubjs package)
pnpm build
```

#### Run Tests / Linters

```bash
# Entire workspace
pnpm test
pnpm lint
pnpm lint:fix
pnpm typecheck

# API only
cd apps/api && make lint

# Frontend only
cd apps/reader && pnpm lint
```

#### Cleanup caches

```bash
pnpm clean   # remove .next / .turbo / __pycache__ / .mypy_cache etc.
```

### Update OpenAPI Schema

If you change the API types:

```bash
# 1) Make sure the API server is running (in another terminal)
pnpm dev:api

# 2) Regenerate types from the repo root
pnpm openapi
```

## 🔧 Troubleshooting

### Common Problems & Solutions

#### 1. Errors during `pnpm install`

```bash
# Clear cache
pnpm store prune

# Remove node_modules and reinstall
rm -rf node_modules pnpm-lock.yaml
pnpm i
```

#### 2. Docker Services Fail to Start

```bash
# Stop & remove existing containers
cd apps/api
docker compose down -v

# Check ports
lsof -i :8080  # Weaviate
lsof -i :4443  # GCS Emulator

# Restart
make docker.up
```

#### 3. API Fails to Start

```bash
# Rebuild uv environment
cd apps/api
rm -rf .venv
uv sync --frozen

# Verify environment variables
cat src/config/.env  # Check API keys
```

#### 4. Frontend API Communication Errors

```bash
# Ensure API is running
curl http://localhost:8000/health

# For CORS errors, check API CORS settings
```

#### 5. Weaviate Connection Errors

```bash
# Check if Weaviate is up
curl http://localhost:8080/v1/.well-known/ready

# View logs
cd apps/api
docker compose logs weaviate
```

#### 6. PostgreSQL/Supabase Connection Errors

```bash
# Check if Supabase is running
supabase status

# Verify port 54322 is used
lsof -i :54322

# Connection test
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -c "SELECT 1"

# If Supabase is not running
supabase start
```

#### 7. Missing Database Tables

```bash
# Initialize the database
cd apps/api
uv run python
>>> from src.config.db import init_db
>>> init_db()
>>> exit()
```

### Debugging Tips

1. **Check API Logs**

   ```bash
   # FastAPI logs are shown in the terminal
   # If LangSmith tracing is enabled, check trace information too
   ```

2. **Browser DevTools**

   - Use the Network tab to inspect API requests.
   - Check the Console for error messages.

3. **Docker Logs**

   ```bash
   cd apps/api
   docker compose logs -f      # All services
   docker compose logs -f weaviate  # Weaviate only
   ```

## 📁 Directory Structure

### Top-Level Structure

```
bookwith/
├── apps/
│   ├── api/          # FastAPI backend
│   │   ├── src/
│   │   │   ├── domain/          # Domain layer (DDD)
│   │   │   ├── usecase/         # Use-case layer
│   │   │   ├── infrastructure/  # Infrastructure layer
│   │   │   ├── presentation/    # Presentation layer
│   │   │   └── config/          # Config files
│   │   ├── Makefile             # Helper commands
│   │   └── docker-compose.yml   # Docker configuration
│   │
│   └── reader/       # Next.js frontend
│       ├── src/
│       │   ├── components/      # UI components
│       │   ├── hooks/           # Custom hooks
│       │   ├── pages/           # Page components
│       │   └── lib/             # Utilities
│       └── package.json
│
├── packages/         # Shared packages (future expansion)
├── docs/             # Documentation
├── package.json      # Monorepo configuration
├── pnpm-workspace.yaml
└── turbo.json        # Turbo configuration
```

### Key Backend Files

- `apps/api/src/domain/` – Entities, Value Objects, Repository Interfaces
- `apps/api/src/usecase/` – Business Logic
- `apps/api/src/infrastructure/memory/` – AI Memory Management
- `apps/api/src/presentation/api/` – API Endpoints

### Key Frontend Files

- `apps/reader/src/components/viewlets/chat/` – AI Chat UI
- `apps/reader/src/components/Reader.tsx` – Core ePub Reader
- `apps/reader/src/lib/apiHandler/` – API Communication Logic
- `apps/reader/src/models/reader.ts` – State Management (Valtio)

## 🤝 Contribution Guidelines

### Coding Standards

#### Python (Backend)

1. **Formatter:** Black
2. **Type Checking:** MyPy with no errors
3. **Naming Conventions:**
   - Classes: PascalCase
   - Functions & Variables: snake_case
   - Constants: UPPER_SNAKE_CASE

```python
# Good Example
class BookRepository(ABC):
    def find_by_id(self, book_id: BookId) -> Optional[Book]:
        pass

# Bad Example
class bookRepository:
    def findById(self, bookId):  # No type hints
        pass
```

#### TypeScript (Frontend)

1. **Formatter:** Prettier
2. **Linter:** Follow ESLint configurations
3. **Strict Typing:** `strict: true`

```typescript
// Good Example
interface BookProps {
  id: string
  title: string
  onSelect?: (id: string) => void
}

// Bad Example
interface BookProps {
  id: any // Avoid any
  title: string
}
```

### Commit Guidelines

We recommend Conventional Commits:

```bash
# Format
<type>(<scope>): <subject>

# Example
feat(reader): Add streaming support for AI chat
fix(api): Fix memory leak
docs: Add environment setup guide
refactor(domain): Improve validation in Book entity
test(usecase): Add unit tests for CreateBookUseCase
```

#### Type List

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Changes that do not affect code meaning
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding or correcting tests
- `chore`: Changes to the build process or auxiliary tools

### Pull Requests

1. **Branch Naming:** `feature/xxx`, `fix/xxx`, `docs/xxx`
2. **PR Template:** Include the following
   - Summary of changes
   - Related issue numbers
   - How to test
   - Screenshots (for UI changes)

### Review Checklist

- [ ] Type safety is maintained
- [ ] Follows DDD principles (backend)
- [ ] Proper error handling
- [ ] No negative performance impact
- [ ] Tests are added when appropriate

## 📚 Reference Resources

### Official Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [LangChain Documentation](https://python.langchain.com/)

### Project-Specific Docs

- [CLAUDE.md](../CLAUDE.md) – AI Assistant Guide
- [backend-architecture.md](./backend-architecture.md) – Backend Architecture Details
- [frontend-directory-structure.md](./frontend-directory-structure.md) – Frontend Structure Details

### Helpful Tools

- [Swagger Editor](https://editor.swagger.io/) – OpenAPI schema editing
- [Weaviate Console](http://localhost:8080/v1/console) – Vector DB management
- [React Developer Tools](https://react.dev/learn/react-developer-tools) – React debugging

## 🆘 Support

If you still have issues:

1. Search existing [GitHub Issues](https://github.com/your-org/bookwith/issues)
2. Create a new issue (include reproduction steps)
3. Ask in [Discussions](https://github.com/your-org/bookwith/discussions)

---

Happy Coding! 🚀
