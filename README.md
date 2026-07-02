# Mechanical & Multi-Department RAG Chatbot

An enterprise-grade **Retrieval-Augmented Generation (RAG)** platform built for the mechanical engineering domain and extended into a **multi-department document management system** (mechanical, technical, accounting, HR, and shared documents). The system automatically classifies PDF documents by domain, extracts structured data (Bills of Materials), enforces department- and security-level access control, and returns accurate, citation-backed answers without hallucination.

---

## Key Features

| Feature | Description |
|---|---|
| **Domain-Aware Document Processing** | Documents are automatically classified into domains (`co_khi`, `ky_thuat`, `ke_toan`, `nhan_su`, `chung`) based on content. Each domain has its own extractor and quality-scoring strategy, configured centrally in `domain_registry.py`. |
| **Structured Vision OCR** | Uses an OpenAI-compatible Vision model to extract technical tables and Bills of Materials into a strict schema (`BangKeVatTu`). |
| **Persistent FastAPI RAG Backend** | A high-performance API server (`rag_server.py`) that loads embedding/retrieval models once into memory, ensuring low latency and controlled concurrency (`MAX_CONCURRENT_RAG`). |
| **Asynchronous Ingestion Pipeline** | A background worker (`ingestion_worker.py`) handles PDF processing, OCR, and embedding generation via a managed job queue (`IngestionJobs`). |
| **RBAC + Department + Security-Level Access Control** | Named roles (Admin, Reviewer, Uploader, Viewer), per-user department scoping (`UserDepartments`), and per-user security clearance (`UserSecurityClearance`: `public` / `internal` / `confidential`). Access policy managed in `auth/security_policy.py`. |
| **Rate Limiting** | Login rate limiting to prevent brute-force attacks (`auth/rate_limit.py`). |
| **Anti-Hallucination Guardrails** | A strict evidence-based verification layer refuses to answer when quantitative data (fabrication time, costs, quantities) is absent from retrieved context. |
| **Entity Resolver** | `rag/entity_resolver.py` normalizes material names and product codes before lookup. |
| **Intelligent Chitchat Handling** | `rag/chitchat.py` distinguishes casual conversation from technical queries, with bilingual (Vietnamese/English) support. |
| **Sensitive Content Scanner** | `ingestion/sensitive_scanner.py` automatically detects sensitive information in documents during ingestion. |
| **Visual Citations** | Provides source page images in the chat interface so users can verify the origin of every answer. |
| **Bilingual UI (Vi/En)** | The full interface and all system messages support both Vietnamese and English. |
| **Access Audit Logging** | All access to `confidential`-level documents is recorded for compliance auditing. |
| **Docker Compose Ready** | A single command brings up the full stack (UI + API backend + ingestion worker). |

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| Frontend / UI | [Streamlit](https://streamlit.io/) |
| API Backend | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| LLM & Vision | OpenAI-compatible endpoint (ProxyLLM) — configured via `GPT_MODEL_NAME`, `GPT_VISION_MODEL_NAME` |
| Embedding Model | `BAAI/bge-m3` (sentence-transformers, 1024 dims) |
| Vector Database | [Qdrant Cloud](https://qdrant.tech/) |
| Relational Database | Microsoft SQL Server |
| Key Libraries | `PyMuPDF`, `pdfplumber`, `LangChain`, `SQLAlchemy`, `pyodbc`, `underthesea`, `bcrypt`, `tenacity`, `Pillow` |

---

## Project Structure

```text
ChatBotProject/
├── .env                        # Environment variables (API keys, DB, model names)
├── Dockerfile                  # Python 3.11 image used by all services
├── docker/
│   └── docker-compose.yml      # Orchestration: UI + API server + Worker
├── run.py                      # Entry point: Streamlit UI
├── run_server.py               # Launcher: FastAPI RAG server
├── run_worker.py               # Launcher: Ingestion worker
├── requirements.txt            # Python dependencies
├── requirements.lock.txt       # Pinned dependencies
├── pytest.ini                  # Test configuration
│
├── database/
│   ├── init/
│   │   └── Mech_Chatbot_DB.sql         # Initial schema (tables, seed data)
│   └── migrations/                     # Versioned SQL migrations (Flyway-style)
│       ├── V0001__backfill_clearance_safe_default.sql
│       ├── V0002__deactivate_legacy_stage_departments.sql
│       ├── V0003__add_filepath_to_tailieu.sql
│       ├── V0004__add_common_document_metadata.sql
│       ├── V0005__add_app_settings.sql
│       ├── V0006__department_status_archive_reassign.sql
│       ├── V0007__add_login_attempts.sql
│       ├── V0008__add_site_to_departments.sql
│       └── V0009__normalize_phongban_sharing.sql
│
├── scripts/
│   ├── create_qdrant_indexes.py        # Initialize Qdrant Cloud collections
│   ├── nap_them_file.py                # Manually ingest additional documents
│   ├── admin/                          # Administrative scripts
│   ├── diagnostics/                    # System diagnostics (DB, Qdrant, LLM)
│   ├── eval/                           # RAG quality evaluation scripts
│   ├── migrations/                     # Migration helper scripts
│   ├── ops/                            # Operational scripts
│   └── danger_ops/                     # Destructive operations (delete, reset)
│
├── tests/                              # Golden question sets and test fixtures
├── mech_chatbot_tests_layered/         # Layered tests (unit, integration, e2e)
├── reports/                            # RAG evaluation reports
├── data/
│   ├── raw/                            # Source PDF documents
│   ├── processed/                      # Rendered page images
│   └── cache/                          # Vision OCR cache (not committed to git)
│
└── src/mech_chatbot/                   # Core application source code
    ├── ui/
    │   ├── app.py                      # Streamlit main router
    │   └── pages/
    │       ├── chatbot.py              # RAG Q&A chat page
    │       ├── queue.py                # Ingestion queue monitor
    │       ├── documents.py            # Document browser & approval
    │       ├── upload.py               # Document upload
    │       ├── admin.py                # System administration
    │       ├── users.py                # User management
    │       ├── audit.py                # Security access audit log
    │       ├── analytics.py            # Usage analytics
    │       ├── dashboard.py            # Per-department dashboard
    │       ├── materials.py            # Bill of Materials lookup
    │       ├── settings.py             # System settings & language toggle
    │       ├── feedback.py             # User feedback collection
    │       └── help.py                 # User guide
    ├── api/
    │   └── rag_server.py               # Persistent FastAPI RAG server
    ├── workers/
    │   ├── ingestion_worker.py         # Background document ingestion daemon
    │   └── rag_worker.py               # Isolated RAG subprocess worker
    ├── ingestion/
    │   ├── document_classifier.py      # 2-tier document classifier
    │   ├── domain_registry.py          # Central domain configuration registry
    │   ├── domain_handlers.py          # Per-domain processing handlers
    │   ├── doc_type_registry.py        # Document type registry
    │   ├── site_registry.py            # Site/branch registry
    │   ├── material_registry.py        # Material registry
    │   ├── mechanical_extractors.py    # Extractor for mechanical documents
    │   ├── generic_extractors.py       # General-purpose extractor
    │   ├── pdf_processor.py            # PDF rendering, OCR, and chunking
    │   ├── sensitive_scanner.py        # Sensitive content detection
    │   ├── vision_cache.py             # Vision OCR result cache
    │   └── file_ingestor.py            # Ingestion pipeline orchestrator
    ├── rag/
    │   ├── service.py                  # Core RAG logic (retrieval + generation)
    │   ├── rbac.py                     # RBAC-based document filter
    │   ├── entity_resolver.py          # Entity / material name normalizer
    │   ├── chitchat.py                 # Chitchat detection and handling
    │   ├── regression.py               # RAG quality regression checks
    │   └── text_utils.py               # Text processing utilities
    ├── auth/
    │   ├── service.py                  # Authentication, authorization, departments
    │   ├── security_policy.py          # Security clearance policy (resolve_clearance)
    │   └── rate_limit.py               # Login rate limiting (brute-force protection)
    ├── db/
    │   └── repository.py               # SQL Server models, queries, and operations
    ├── llm/
    │   ├── llm_client.py               # LLM client (OpenAI-compatible)
    │   └── vision_client.py            # Vision model client
    └── config/                         # Logging, theme, and app configuration
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10+ (3.11 matches the Docker image)
- Docker & Docker Compose (recommended)
- Microsoft SQL Server + ODBC Driver (for `pyodbc`)
- A Qdrant Cloud account (URL + API key)
- An OpenAI-compatible LLM endpoint (ProxyLLM or direct OpenAI)

### 2. Configure Environment

Create a `.env` file at the project root and populate the following variables:

```env
# LLM / Vision
PROXYLLM_BASE_URL=https://api.proxyllm.eu/v1
PROXYLLM_API_KEY=<your-api-key>
GPT_MODEL_NAME=gpt-5.4
GPT_VISION_MODEL_NAME=gpt-5.4
GPT_TEMPERATURE=0
GPT_MAX_OUTPUT_TOKENS=8000
GPT_VISION_MAX_OUTPUT_TOKENS=16000
GPT_TIMEOUT_SECONDS=300

# Vector Database
QDRANT_URL=<your-qdrant-cloud-url>
QDRANT_API_KEY=<your-qdrant-api-key>

# Embedding
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIM=1024
EMBEDDING_CHUNK_SIZE=600
EMBEDDING_CHUNK_OVERLAP=80

# SQL Server
SQL_SERVER=localhost\SQLEXPRESS
SQL_DATABASE=Mech_Chatbot_DB
SQL_TRUSTED_CONNECTION=true

# RAG Server
RAG_SERVER_URL=http://localhost:8100
RAG_SERVER_PORT=8100
MAX_CONCURRENT_RAG=2

# Strict Modes
STRICT_INGEST_REQUIRE_VISION=true
STRICT_ANSWER_MODE=true
```

### 3. Database Setup

```bash
# Step 1: Create the base schema on your SQL Server instance
#   Run: database/init/Mech_Chatbot_DB.sql

# Step 2: Apply versioned migrations in order (V0001 → V0009)
#   Run each file in: database/migrations/

# Step 3: Initialize Qdrant collections
python scripts/create_qdrant_indexes.py
```

> **Security note:** Migrations seed example accounts (`admin`, `reviewer1`, `viewer1`, `uploader1`). Change or remove default credentials before any production deployment.

### 4. Running the Application

**Option A: Docker Compose (recommended)**

```bash
docker-compose -f docker/docker-compose.yml up -d --build
```

This launches:
- Streamlit UI → `http://localhost:8501`
- FastAPI RAG server → `http://localhost:8100`
- Ingestion worker (background)

**Option B: Local Development**

```bash
git clone https://github.com/giabao2605/ChatbotProject.git
cd ChatbotProject
pip install -r requirements.txt
```

Start each service in a separate terminal:

```bash
# Terminal 1 — RAG API server
python run_server.py

# Terminal 2 — Ingestion worker
python run_worker.py

# Terminal 3 — Streamlit UI
streamlit run run.py
```

> Alternatively, run modules directly with `PYTHONPATH=src`:
> ```bash
> PYTHONPATH=src python -m mech_chatbot.api.rag_server
> PYTHONPATH=src python -m mech_chatbot.workers.ingestion_worker
> ```
> This is what the Docker Compose configuration uses internally.

---

## Application Pages

Access pages via the Streamlit sidebar (visibility depends on your role):

| Page | Description | Required Role |
|---|---|---|
| **Chatbot Q&A** | Ask technical questions and get evidence-based answers with visual citations | All |
| **Ingestion Queue** | Monitor background document processing jobs | Uploader, Admin |
| **Documents** | Browse, search, and approve documents | Reviewer, Admin |
| **Upload** | Upload new PDF documents to the ingestion queue | Uploader, Admin |
| **Admin** | System settings, site/branch management | Admin |
| **Users** | Manage accounts, roles, departments, and security clearance | Admin |
| **Audit** | Confidential document access log | Admin |
| **Analytics** | System usage statistics | Admin, Reviewer |
| **Dashboard** | Per-department overview | All |
| **Materials** | Bill of Materials (BOM) lookup | All |
| **Settings** | Interface language, personal preferences | All |
| **Feedback** | Submit feedback on answer quality | All |
| **Help** | System user guide | All |

---

## Testing

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run the full test suite
pytest

# Run by layer
pytest tests/
pytest mech_chatbot_tests_layered/
```

Evaluation reports are stored in the `reports/` directory.

---

## Useful Scripts

| Script | Purpose |
|---|---|
| `scripts/create_qdrant_indexes.py` | Create or recreate Qdrant collections |
| `scripts/nap_them_file.py` | Manually ingest additional documents |
| `scripts/eval/` | Evaluate RAG quality with golden question sets |
| `scripts/diagnostics/` | Diagnose DB, Qdrant, and LLM connectivity |
| `scripts/admin/` | Advanced administrative tasks |
| `scripts/danger_ops/` | Destructive operations (data deletion, system reset) |

---

## Contributing

Contributions, bug reports, and feature requests are welcome. Please open an issue on the GitHub repository.

## License

This project is proprietary. All rights reserved.
