# MedVault

MedVault is an intelligent, secure medical document management and health tracking system. It leverages advanced AI features like Retrieval-Augmented Generation (RAG), Optical Character Recognition (OCR), and an intelligent Chat Copilot to help users digitize, store, analyze, and query their medical records and health history.

## Features

- **Intelligent Document Processing:** Upload medical documents (PDFs, images) and extract key information using multiple OCR engines (Tesseract) and PDF extractors (PyMuPDF, Docling).
- **AI-Powered Chat Copilot:** Chat with your medical documents to get summaries, query lab results, and discover health trends.
- **RAG Integration:** Uses embedding models and vector search to ground AI responses in your actual medical records.
- **Health Timeline:** Automatically generates a chronological timeline of your clinical history from uploaded documents.
- **Dashboard & Family Overview:** View clinical snapshots, recent activity feeds, and manage health records for multiple family members.

## Architecture

The project consists of two main components:
- **Backend:** A Python-based FastAPI server managing database models (PostgreSQL + Alembic), asynchronous tasks (ARQ/Redis), document processing pipelines, and AI integrations (OpenAI, Groq, Ollama, Vercel AI, Gemini, X.AI).
- **Frontend:** A Next.js application built with modern React features, providing a beautiful and responsive user interface for the dashboard, document upload, timeline, and AI chat.

## Getting Started

### Prerequisites

- Node.js (v18+) & pnpm
- Python 3.10+
- PostgreSQL
- Redis
- Tesseract (for OCR)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd medvault
   ```

2. **Environment Variables:**
   Copy the example environment files and update them with your own API keys and database credentials.
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env.local
   ```

3. **Backend Setup:**
   ```bash
   cd backend
   # Set up virtual environment and install dependencies (e.g., using poetry or pip)
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --reload
   ```

4. **Frontend Setup:**
   ```bash
   cd frontend
   pnpm install
   pnpm dev
   ```

## Configuration

MedVault is highly configurable. You can adjust the AI providers in the `.env` file, selecting different models for specific tasks (e.g., Classification, Metadata Extraction, Summarization, Chat, and Embeddings) using fallback mechanisms to ensure high availability and reliability.

## License
MIT License
