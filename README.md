# Urban Vibe Store Agent

A comprehensive Customer Service AI Agent for "Urban Vibe Store", built with FastAPI, LangGraph, LightRAG, and Streamlit.

## Features

- **Conversational AI**: Powered by LangGraph and LLMs (OpenAI, Groq, etc.).
- **RAG Engine**: LightRAG integration for deep knowledge retrieval.
- **Multi-Channel Support**: Ready for Web, WhatsApp, and Telegram.
- **Admin Dashboard**:
    - **User Management**: Role-based access control (Admin/Staff).
    - **Knowledge Base CMS**: Upload, view, and edit documents with automatic re-ingestion.
    - **System Health**: Real-time monitoring of API and pipelines.

## Accessing the Admin Panel

The admin dashboard is available at `http://localhost/admin/` (or your Ngrok URL).

- **Default Admin Credentials**:
    - Username: `admin`
    - Password: `admin123` (Change this in production via `ADMIN_PASSWORD` env var)

### Key Features
1.  **Dashboard**: Overview of system status.
2.  **Live Chat Test**: Simulator for testing agent responses.
3.  **Knowledge Base**: 
    - Upload PDF/TXT/MD files.
    - **Edit Mode**: Click "Edit" on any document to modify its content. The system will automatically update the vector index.
4.  **User Management**: create new staff accounts.

## Setup & Installation

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local dev)

### Environment Variables
Copy the example environment file and configure your keys:
```bash
cp .env.example .env
```
Fill in `OPENAI_API_KEY`, `POSTGRES_URI`, etc.

### Running with Docker
```bash
cd infra
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Development
The architecture consists of:
- **App**: FastAPI backend (Port 8000)
- **Streamlit**: UI Frontend (Port 8501, proxied via Nginx)
- **LightRAG**: Knowledge Engine (Port 9621)
- **Postgres**: Database for Agent Memory (Checkpoints) & CMS (`kb_documents`, `admin_users`)
- **Qdrant**: Vector Database
- **Nginx**: Reverse Proxy (Port 80)

## Directory Structure
- `app/api`: FastAPI endpoints and agent logic.
- `app/ui`: Streamlit dashboard code.
- `app/config`: Configuration settings.
- `infra`: Docker and Nginx configuration.
