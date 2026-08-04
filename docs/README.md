# MedVault Documentation

Product and architecture documentation for the MedVault MVP.

## Documents

| Document | Description |
| -------- | ----------- |
| [PRD.md](PRD.md) | Product requirements |
| [TAD.md](TAD.md) | Technical architecture |
| [FSD.md](FSD.md) | Frontend specification |
| [SAD.md](SAD.md) | Security and access |
| [FTL.md](FTL.md) | Feature task list |

## Architecture Summary

MedVault is built as a **modular monolith**:

- **Frontend** — Next.js 16 with feature-first organization
- **Backend** — FastAPI with layered feature modules (router → service → repository)
- **AI** — OCR, LLM, embeddings, and RAG for document processing and search

See [TAD.md](TAD.md) for the full system design.
