# MedVault

AI-powered medical document organizer — MVP.

## Overview

MedVault helps patients upload, organize, and search medical records using OCR, LLM extraction, embeddings, and RAG.

## Repository Structure

```
medvault/
├── frontend/   # Next.js 16 application
├── backend/    # FastAPI modular monolith
└── docs/       # Product and architecture documentation
```

## Tech Stack

| Layer    | Technologies |
| -------- | ------------ |
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4, shadcn/ui, TanStack Query, Zustand, React Hook Form, Zod |
| Backend  | FastAPI, Python 3.13+, SQLAlchemy 2.x, Alembic, PostgreSQL, Pydantic v2 |
| AI       | OCR, LLM, Embeddings, RAG |

## Getting Started

See [frontend/README.md](frontend/README.md) and [backend/README.md](backend/README.md) for setup instructions.

## Documentation

- [PRD](docs/PRD.md)
- [Technical Architecture](docs/TAD.md)
- [Frontend Specification](docs/FSD.md)
- [Security & Access](docs/SAD.md)

## License

Proprietary — All rights reserved.
