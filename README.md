# Mechanical & Multi-Department RAG Chatbot

An advanced Retrieval-Augmented Generation (RAG) platform originally built for the **mechanical engineering** domain and now extended into a **multi-department document platform** (mechanical, technical, accounting, HR, and shared documents). The system ingests complex technical PDFs, classifies them by domain, extracts precise structured data (such as Bills of Materials), enforces department- and security-level access control, and returns accurate, evidence-based answers without hallucination.

## Key Features

- **Domain-Aware Document Processing:** Documents are automatically classified by content into domains (e.g. `co_khi`, `ky_thuat`, `ke_toan`, `nhan_su`, `chung`). Each domain has its own extractor and quality-scoring strategy, configured centrally in `domain_registry.py`.
- **Structured Vision OCR:** Uses an OpenAI-compatible Vision model (served via a ProxyLLM endpoint, model name configurable) to extract and format technical tables and Bills of Materials into a strict, schema-enforced structure (`BangKeVatTu`).
- **Domain-Specific Extractors:** Mechanical drawings use a dedicated extractor; tabular/accounting and generic documents use their own extractors and quality functions.
- **Persistent FastAPI RAG Backend:** A decoupled, high-performance API server (`rag_server.py`) that loads embedding/retrieval models into memory once, ensuring low latency and controlled concurrency (`MAX_CONCURRENT_RAG`).
- **Asynchronous Ingestion Pipeline:** A dedicated background worker (`ingestion_worker.py`) handles heavy document processing, OCR, and embedding generation asynchronously via a managed job queue (`IngestionJobs`).
- **Role-Based + Department + Security-Level Access Control:** Authentication with named roles (e.g. Admin, Reviewer, Uploader, Viewer) backed by `Roles`/`UserRoles`, per-user department scoping (`UserDepartments`), and per-user security clearance (`UserSecurityClearance`, levels such as `internal` / `confidential`). A document's visibility is controlled by its `Domain`, `Department`/`Site`, and `SecurityLevel`.
- **Access Audit Logging:** Access to confidential documents is recorded for auditing (see the Audit page in the UI).
- **Anti-Hallucination Guardrails:** A strict "evidence-based" verification layer. The chatbot refuses to guess quantitative data (fabrication time, costs, quantities) when the evidence is missing from retrieved context.
- **Visual Citations:** Provides explicit reference images in the chat interface so users can verify the source of an answer.
- **Multi-Page Streamlit Interface:** Dedicated pages for chat, ingest queue monitoring, document upload/approval, admin, user management, audit, analytics, dashboards, materials, settings, and help.
- **Docker Compose Ready:** One command brings up the full stack (UI, API backend, and ingestion worker).

## Technology Stack

- **Language:** Python 3.11 (per the Docker image; 3.10+ recommended for local runs)
- **Frontend / UI:** [Streamlit](https://streamlit.io/)
- **API Backend:** [FastAPI](https://fastapi.tiangolo.com/) & Uvicorn
- **LLM & Vision:** OpenAI-compatible endpoints via a ProxyLLM service (LangChain). Model names are configured through environment variables (`GPT_MODEL_NAME`, `GPT_VISION_MODEL_NAME`) and are not hard-coded.
- **Embeddings:** BAAI/bge-m3 (via sentence-transformers)
- **Vector Database:** [Qdrant Cloud](https://qdrant.tech/)
- **Relational Database:** Microsoft SQL Server
- **Key Libraries:** `PyMuPDF`, `pdfplumber`, `LangChain`, `SQLAlchemy`, `pyodbc`, `Tenacity`, `underthesea`, `bcrypt`, `Docker`

## Project Structure

```text
chatbot/
├── .env                    # Environment variables (API keys, DB connections, model names)
├── Dockerfile              # Python 3.11 image used by all services
├── docker/
│   └── docker-compose.yml  # Orchestration for UI, API, and Worker
├── run.py                  # Streamlit UI entry point (streamlit run run.py)
├── run_server.py           # Convenience launcher for the FastAPI RAG server
├── run_worker.py           # Convenience launcher for the ingestion worker
├── requirements.txt        # Python dependencies (requirements.lock.txt = pinned)
├── database/
│   ├── init/
│   │   └── Mech_Chatbot_DB.sql   # Initial schema (tables, seed data)
│   └── migrations/               # Incremental SQL migrations (P0 multi-domain, RBAC, sites, ...)
├── scripts/                # Admin, ops, eval, diagnostics, and migration helper scripts
├── tests/                  # Golden questions and test fixtures
├── reports/                # Evaluation reports
├── data/                   # raw/ (source docs) and processed/ (extracted page images)
└── src/mech_chatbot/       # Core application source code
    ├── ui/
    │   ├── app.py          # Streamlit router
    │   └── pages/          # chatbot, queue, documents, upload, admin, users,
    │                       #   audit, analytics, dashboard, materials, settings, feedback, help
    ├── api/
    │   └── rag_server.py   # Persistent FastAPI RAG server
    ├── workers/
    │   ├── ingestion_worker.py  # Background PDF/ingest daemon
    │   └── rag_worker.py        # Isolated RAG subprocess worker
    ├── ingestion/          # PDF processing, Vision OCR, classification & extractors
    │   ├── document_classifier.py
    │   ├── domain_registry.py
    │   ├── doc_type_registry.py
    │   ├── site_registry.py
    │   ├── material_registry.py
    │   ├── mechanical_extractors.py
    │   ├── generic_extractors.py
    │   ├── pdf_processor.py
    │   ├── vision_cache.py
    │   └── file_ingestor.py
    ├── rag/                # Retrieval, generation, and anti-hallucination logic
    │   ├── service.py
    │   ├── regression.py
    │   └── text_utils.py
    ├── auth/               # Authentication, roles, departments, security clearance
    │   └── service.py
    ├── db/                 # SQL Server models, queries, and operations
    │   └── repository.py
    ├── llm/                # LLM and Vision clients (OpenAI-compatible / ProxyLLM)
    │   ├── llm_client.py
    │   └── vision_client.py
    └── config/             # Logging and theme configuration
```

## Getting Started

### 1. Prerequisites

- Python 3.10+ (3.11 matches the Docker image) if running locally without Docker
- Docker & Docker Compose (recommended)
- Microsoft SQL Server (plus the ODBC driver for `pyodbc`)
- A Qdrant Cloud account (URL + API key)
- An OpenAI-compatible API key (e.g. a ProxyLLM endpoint)

### 2. Configure Environment

Copy/create a `.env` file at the project root and set at least:

- Database connection (SQL Server)
- `QDRANT_URL` and Qdrant API key
- LLM/Vision endpoint, API key, and model names (`GPT_MODEL_NAME`, `GPT_VISION_MODEL_NAME`)

### 3. Database Setup

1. Run `database/init/Mech_Chatbot_DB.sql` against your SQL Server instance to create the base tables (`TaiLieu`, `BangKeVatTu`, `DocumentPages`, `IngestionJobs`, `LichSuChat`, `Users`, `Roles`, etc.).
2. Apply the migrations in `database/migrations/` (in order) to enable the multi-department features — e.g. `migrate_p0_multi_domain.sql` (adds `Domain`, `SecurityLevel`, `Site`, `UserSecurityClearance`, `DocumentAttributes`), `fix_rbac_departments.sql`, `p1_multi_site_queue_admin.sql`, and the seed-hardening migration. These scripts are idempotent and safe to re-run.
3. Create your Qdrant Cloud cluster, then initialize indexes with `python scripts/create_qdrant_indexes.py`.

> Security note: the migrations seed example accounts (e.g. `admin`, `reviewer1`, `viewer1`, `uploader1`). Change or remove default credentials before any production use (`p0_harden_seed_accounts.sql`).

### 4. Running the Application

**Option A: Docker Compose (recommended)**

```bash
docker-compose -f docker/docker-compose.yml up -d --build
```
This launches:
- The Streamlit UI on `http://localhost:8501`
- The FastAPI RAG server on `http://localhost:8100`
- The ingestion worker in the background

**Option B: Running Locally (Development)**

```bash
git clone https://github.com/giabao2605/ChatbotProject.git
cd ChatbotProject
pip install -r requirements.txt
```

Then start each service (the `run_*.py` launchers add `src/` to the Python path for you):

```bash
# 1. RAG API server
python run_server.py

# 2. Ingestion worker (separate terminal)
python run_worker.py

# 3. Streamlit UI (separate terminal)
streamlit run run.py
```

> Alternatively, run the modules directly with `PYTHONPATH=src` set, e.g.
> `PYTHONPATH=src python -m mech_chatbot.api.rag_server` and
> `PYTHONPATH=src python -m mech_chatbot.workers.ingestion_worker` (this is what docker-compose uses).

### 5. Application Modules

Once running, use the Streamlit sidebar to access (availability depends on your role/permissions):
- **Chatbot Hỏi Đáp:** Ask domain questions and get evidence-based answers with visual citations.
- **Tiến Trình Ingest (Queue):** Monitor background document processing jobs.
- **Duyệt / Tải Tài Liệu (Documents / Upload):** Upload technical PDFs and commit them to the ingestion queue (Admin/Uploader/Reviewer roles).
- **Quản trị (Admin / Users):** Manage users, roles, departments, and security clearance.
- **Audit & Analytics & Dashboard:** Review confidential-access logs, usage analytics, and per-department dashboards.

## Contributing

Contributions, issues, and feature requests are welcome. Please open an issue on the GitHub repository.

## License

This project is proprietary. All rights reserved.
