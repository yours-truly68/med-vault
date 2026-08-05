Technical Architecture Document (TAD)

Product Name: MedVault

Version: MVP v1.0

Status: Draft

⸻

1. Overview

Purpose

This document describes the high-level technical architecture of MedVault MVP.

The architecture prioritizes:

* Simplicity
* Fast development
* Easy maintenance
* AI integration
* Future scalability

The MVP is designed as a modular monolith, allowing the application to grow into a distributed architecture later if necessary.

⸻

2. High-Level Architecture

                        Browser
                           │
                           │
                  Next.js Frontend
                           │
                     REST API (HTTPS)
                           │
                    FastAPI Backend
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   PostgreSQL         File Storage      AI Processing
        │             (Local Disk)          Worker
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                   Vector Database

⸻

3. Technology Stack

Frontend

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui
* TanStack Query
* Zustand
* React Hook Form
* Zod

⸻

Backend

* FastAPI
* Python
* SQLAlchemy
* Alembic
* PostgreSQL
* JWT Authentication

⸻

AI

* Extraction Engine (PyMuPDF → Docling → Tesseract; Vision OCR deferred to future release)
* LLM for classification, metadata, and summarization
* Embedding Model
* Retrieval-Augmented Generation (RAG)

⸻

Storage

MVP

* Local file storage
* PostgreSQL
* Vector database

Future versions can migrate to cloud storage such as Amazon S3 without changing the application architecture.

⸻

4. System Components

Frontend

Responsible for:

* Authentication
* Dashboard
* File uploads
* Document browsing
* Search
* Timeline
* AI Chat

The frontend communicates only with the REST API.

⸻

Backend API

Responsible for:

* Authentication
* Authorization
* User management
* Family member management
* File uploads
* Document management
* AI orchestration
* Search
* Chat

Business logic resides here.

⸻

Database

Stores structured application data.

Examples:

* Users
* Family Members
* Documents
* Metadata
* AI Summaries

⸻

File Storage

Stores uploaded files.

Example structure:

uploads/
    user-id/
        member-id/
            document.pdf
            blood-test.jpg

⸻

AI Processing Service

Processes uploaded documents asynchronously.

Responsibilities:

* Text extraction (strategy-routed; AI-agnostic)
* Metadata extraction
* Document classification
* Summary generation
* Embedding generation

⸻

Vector Database

Stores embeddings generated from processed documents.

Used for:

* Semantic search
* AI chat retrieval

⸻

5. Document Processing Flow

User Uploads File
        │
        ▼
Store Original File
        │
        ▼
Extract Text (Extraction Engine: searchable PDF → native text; scanned → OCR/Docling; last resort → Vision)
        │
        ▼
Classify Document
        │
        ▼
Extract Metadata
        │
        ▼
Generate AI Summary
        │
        ▼
Generate Embeddings
        │
        ▼
Store Results
        │
        ▼
Document Ready

⸻

6. AI Workflow

For every uploaded document:

1. Store the original file.
2. Extract text.
3. Detect the document type.
4. Extract metadata.
5. Generate a concise summary.
6. Generate embeddings.
7. Save all processed information.
8. Mark the document as processed.

⸻

7. API Architecture

The backend follows a layered architecture.

Client
   │
Router
   │
Service
   │
Repository
   │
Database

Router

* Receives HTTP requests
* Validates input
* Returns responses

Service

* Business logic
* Coordinates AI processing
* Handles permissions

Repository

* Database operations only

⸻

8. Frontend Architecture

Pages
    │
Components
    │
Hooks
    │
API Client
    │
Backend

State management:

* TanStack Query → Server state
* Zustand → Client state

⸻

9. Database Overview

Core tables:

Users
FamilyMembers
Documents
DocumentMetadata
AISummaries
Embeddings

Relationships:

* One User → Many Family Members
* One Family Member → Many Documents
* One Document → One Metadata Record
* One Document → One Summary
* One Document → One Embedding

⸻

10. Authentication Flow

User Login
      │
Access Token
      │
Protected API
      │
Authorized Response

Authentication uses:

* JWT Access Token
* HTTP-only Refresh Token Cookie

⸻

11. Search Architecture

Two search methods are supported.

Keyword Search

Searches metadata such as:

* Hospital
* Doctor
* Document type
* Date

Semantic Search

Searches document meaning using embeddings.

Used by:

* AI Chat
* Medical history search

⸻

12. Error Handling

The system should gracefully handle:

* Invalid file uploads
* Unsupported file types
* OCR failures
* AI processing failures
* Database errors
* Missing documents

Failed AI processing should not delete uploaded files. Users should still be able to access the original document.

⸻

13. Deployment Architecture

For MVP deployment:

Internet
    │
Next.js Frontend
    │
FastAPI Backend
    │
PostgreSQL
    │
Local File Storage
    │
Vector Database

All services can initially run on a single virtual machine or cloud instance.

⸻

14. Future Scalability

The architecture is intentionally designed to evolve without major rewrites.

Future improvements may include:

* Amazon S3 or Azure Blob Storage
* Background job queue (Celery, Dramatiq, or similar)
* Redis for caching
* Multiple AI workers
* Docker and Kubernetes deployment
* Multi-region storage
* CDN for file delivery
* Event-driven architecture

These enhancements can be introduced incrementally while preserving the existing API contracts.

⸻

15. Design Principles

* Keep the architecture simple.
* Prefer readability over abstraction.
* Build a modular monolith before microservices.
* Process documents asynchronously whenever possible.
* Keep AI services isolated from business logic.
* Design APIs to remain stable as the platform grows.
* Optimize for developer productivity during the MVP phase.