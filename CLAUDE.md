# CLAUDE.md

This file offers comprehensive guidance for Claude Code (claude.ai/code) when working with the BookWith project codebase.

**Last updated**: 2025-06-29  
**Project Version**: v0.1.0  
**Supported Claude Code**: claude.ai/code

## Project Overview

This project is an AI-powered next-generation browser-based ePub reader called "BookWith".

**Differentiators from conventional e-book readers:**

- **Interactive reading with an AI assistant** that understands the book's content
- **Multi-tier memory system**: short-, mid-, and long-term memory for context retention
- **Semantic search**: discover related information via vector search
- **Integrated annotation**: seamless integration of highlights, notes, and AI conversations
- **Reading continuity**: a continuous reading experience across sessions

**Target users:**

- Academic researchers (deep understanding of papers and technical books)
- Avid readers (enhanced enjoyment of novels and general-interest books)
- Learners (efficient study with textbooks and reference books)
- Business professionals (grasp key points of business books and reports)

## Architecture

### Monorepo Setup

**Turbo + pnpm Workspaces**

```
packages:
  - 'apps/*' # applications
  - 'packages/*' # shared libraries
```

**Directory Structure**

- **apps/api/**: FastAPI backend (Python 3.13+)
  - Dependency management with Poetry
  - DDD layered architecture
  - Automatic OpenAPI generation
- **apps/reader/**: Next.js frontend (TypeScript/React)
  - App Router + Turbopack
  - Automatic type generation (OpenAPI → TypeScript)
  - State management with Valtio
- **packages/**: Shared libraries (planned)
  - Shared type definitions
  - Utility functions
  - Common components

### Backend Architecture

DDD (Domain-Driven Design) layered architecture:

- **Domain Layer** (`src/domain/`): Entities, value objects, repository interfaces
- **UseCase Layer** (`src/usecase/`): Application-specific business logic
- **Infrastructure Layer** (`src/infrastructure/`): Integration with external tech (DB, DI, memory)
- **Presentation Layer** (`src/presentation/`): FastAPI routes & schemas

## Development Commands

### Environment Setup

```bash
# 1. Install dependencies (repo root)
pnpm i

# 2. Set environment variables
cd apps/api
cp src/config/.env.example src/config/.env
# Edit .env (set API keys, etc.)

# 3. Start Docker services (Weaviate + GCS emulator)
make docker.up

# 4. Launch API in dev mode
make configure  # poetry install --no-root
make run        # FastAPI on port 8000

# 5. Launch frontend in another terminal
cd apps/reader
pnpm dev        # Next.js on port 7127

# Or launch everything at once (repo root)
pnpm dev        # turbo run dev --parallel
```

### Build & Test

```bash
# Build all
pnpm build      # turbo run build

# Lint all
pnpm lint       # turbo run lint

# API lint & type-check
cd apps/api
make lint       # mypy + pre-commit

# Frontend type-check
cd apps/reader
pnpm ts:check   # tsc --noEmit
```

### API Development

```bash
cd apps/api

# Start dev server
make run

# Lint & type-check
make lint

# Run via Docker
make docker.up

# Generate OpenAPI schema (for frontend)
cd ../reader
pnpm openapi:ts
```

## Key Tech Stack

### Backend (apps/api/)

- **FastAPI** – web framework
- **SQLAlchemy** – ORM (PostgreSQL)
- **Pydantic** – data validation
- **Weaviate** – vector DB (memory)
- **LangChain** – LLM integration
- **OpenAI API** – GPT-4 for chat & summarization

### Frontend (apps/reader/)

- **Next.js 15** – React framework
- **TypeScript** – type safety
- **Tailwind CSS** – styling
- **SWR** – data fetching
- **Epub.js** – ePub rendering
- **Valtio & Jotai** – state management

## Memory Management Feature

A distinctive feature is long-term memory in LLM interactions.

### Memory Levels

- **Short-term memory** – recent conversation buffer
- **Mid-term memory** – automatic conversation summaries
- **Long-term memory** – vector search for relevant info
- **User profile** – extraction & use of personal info

### Implementation Locations

- `src/infrastructure/memory/` – memory functionality
- `src/usecase/message/` – message processing logic
- `src/config/app_config.py` – memory-related settings

## Domain Model

### Main Entities

- **Book** – book entity (ID, title, description, status)
- **Chat** – chat entity (user + book)
- **Message** – individual message within a chat
- **Annotation** – highlights & notes

### Repository Pattern

For each entity:

- Interface defined in domain layer
- PostgreSQL implementation in infrastructure layer

## Development Notes

### DDD Principles

- Entity identity by ID
- Value objects immutable with `@dataclass(frozen=True)`
- Business logic in domain layer
- Maintain dependency direction (upper → lower)

### Type Safety

- Backend: mandatory MyPy checks
- Frontend: TypeScript strict mode
- API schema: automatic OpenAPI generation

### Configuration Management

- `apps/api/src/config/.env*` – env vars
- `AppConfig` class – Pydantic settings
- Memory-related thresholds & limits also here

## Deployment

### Docker Support

**Docker Compose**

```
services:
  weaviate: # vector DB
    - Ports: 8080 (HTTP), 50051 (gRPC)
    - Persistence: weaviate_data volume
    - No-auth (dev)

  gcloud-storage-emulator: # GCS emulator
    - Port: 4443
    - Storage: ./gcs
```

**Frontend Build**

```dockerfile
# apps/reader/Dockerfile (multi-stage build)
stage 1: Builder   – turbo prune
stage 2: Installer – install deps + build
stage 3: Runner    – production run (non-root)
```

**Docker Commands**

```bash
# Start dev services
cd apps/api && make docker.up

# Build frontend
docker build -f apps/reader/Dockerfile -t bookwith-reader .

# Entire stack (future)
docker-compose up  # root docker-compose.yml
```

**Others**

- `PORT=8000` – API port
- `LANGSMITH_TRACING=true` – enable tracing

## Reference Links

### Official Docs

- FastAPI
- Next.js 15
- Weaviate
- LangChain
- ePub.js

### Related Tech

- Turbo (Monorepo)
- Valtio (State Management)
- SWR (Data Fetching)
- Tailwind CSS
- shadcn/ui

## How to Use the API Client

**Common API client** (`apps/reader/src/lib/apiHandler/apiClient.ts`):

```typescript
// Basic usage
import { apiClient } from '@/lib/apiHandler/apiClient'

// GET request
const books = await apiClient<Book[]>('/books')

// POST request (JSON)
const newBook = await apiClient<Book>('/books', {
  method: 'POST',
  body: { title: 'Sample Book', description: 'Description' },
})

// With query params
const messages = await apiClient<Message[]>('/messages', {
  params: { chat_id: 123, limit: 50 },
})
```

**Features**

- Automatically attaches USER_ID (`TEST_USER_ID`)
- Auto-parses JSON responses
- Error handling (logs + throws)
- Supports standard response format `{success: boolean, data: T}`

## BookWith-Specific Notes

### Rationale for Tech Choices

- **Python 3.13** – latest typing features
- **FastAPI** – auto OpenAPI, high performance, streaming
- **Next.js 15** – App Router, Turbopack, RSC
- **Weaviate** – open source, multi-tenant, semantic search
- **Valtio** – proxy-based state management for React

### Development Philosophy

- **Type safety** across all layers
- **DDD / Clean Architecture** for maintainability & extensibility
- **User experience** as a comfortable ePub reader
- **AI integration** as a natural part of reading

### Uniqueness of Memory Feature

- Traditional chatbots handle single Q&A
- BookWith enables continuous conversation with reading context
- Integrates book content + past conversations + annotations search
- Learns the user's reading style

### Code Style

- **Backend**: Black + MyPy + pre-commit
- **Frontend**: Prettier + ESLint + TypeScript strict
- **Commits**: Conventional Commits recommended
- **Docs**: auto-generated + manual additions

## Docs

### LangChain Weaviate

This notebook covers how to get started with the Weaviate vector store in LangChain, using the langchain-weaviate package.
https://python.langchain.com/docs/integrations/vectorstores/weaviate/

### Weaviate

https://weaviate.io/developers/weaviate

## Important Notes

- Components under @apps/reader/src/components/ui should never be edited as they use components from shadcn/ui.
