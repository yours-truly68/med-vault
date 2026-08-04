# MedVault Backend

FastAPI modular monolith for the MedVault API.

## Architecture

```
app/
├── core/           # Cross-cutting infrastructure (config, database, security)
├── shared/         # Shared utilities, schemas, and storage abstractions
├── modules/        # Feature modules (auth, documents, search, chat, …)
├── ai/             # AI capabilities (OCR, LLM, embeddings, RAG)
└── workers/        # Background document processing
```

Each feature module follows a layered structure:

```
router/ → service/ → repository/ → models/
```

## Prerequisites

- Python 3.13+
- PostgreSQL 16+
- [uv](https://docs.astral.sh/uv/) or pip

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Start PostgreSQL (from repo root):

```bash
docker compose up -d postgres
```

Run migrations:

```bash
alembic upgrade head
```

Start the development server:

```bash
uvicorn app.main:app --reload
```

## Testing

```bash
pytest
```

## Module Overview

| Module          | Responsibility                          |
| --------------- | --------------------------------------- |
| `auth`          | Authentication and session management   |
| `users`         | User account management                 |
| `family_members`| Family member profiles                  |
| `documents`     | Document upload and metadata            |
| `search`        | Keyword and semantic search             |
| `chat`          | AI assistant (RAG)                      |
| `processing`    | Async document processing orchestration |

## Documentation

See [docs/TAD.md](../docs/TAD.md) for the full technical architecture.
