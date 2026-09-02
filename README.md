# Blood Test Intelligence System

A production-oriented, modular monolith platform for extracting, standardizing, and analyzing blood test lab reports.

## Core Architectural Principles

- **Deterministic First**: Initial numerical extraction and reference range evaluation are strictly deterministic (No LLM in primary extraction).
- **Separation of Concerns**: AI/LLM analysis is used only for contextual summarization and stored separately from primary lab values.
- **Auditability**: Every doctor correction and override is tracked with audit fields.
- **Standardized Identification**: Uses canonical test identifiers and LOINC code mappings.
- **Future-Ready**: Built for HL7 FHIR and EMR integration compatibility.

---

## Repository Structure

```text
blood-test-intelligence/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/           # FastAPI endpoint routes
│   │   ├── core/                 # Config, Database, Redis, Logging, Exception Handlers
│   │   ├── schemas/              # Pydantic data schemas
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── services/             # Core business logic services
│   │   ├── repositories/         # Database access layer
│   │   ├── utils/                # Helper utilities
│   │   └── main.py               # FastAPI application entrypoint
│   ├── tests/                    # Pytest test suite
│   ├── Dockerfile                # Backend container spec
│   ├── pytest.ini                # Pytest configuration
│   └── requirements.txt          # Python dependencies
├── frontend/                     # Next.js UI dashboard placeholder
├── data/
│   ├── uploads/                  # Raw uploaded report files (PDF/Image)
│   └── processed/                # Validated report output JSONs
├── docker-compose.yml            # Multi-container orchestration
├── .env.example                  # Environment configuration template
├── .gitignore
└── README.md
```

---

## Quick Start (Docker Compose)

### 1. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 2. Launch Services
Build and start all containers (FastAPI Backend, PostgreSQL, Redis):
```bash
docker compose up --build
```

### 3. Verify Health Check
Access the API health endpoint:
```bash
curl http://localhost:8000/api/health
```

Expected Response:
```json
{
  "status": "ok",
  "database": "connected",
  "redis": "connected"
}
```

Interactive API documentation is available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 1. Copy Environment Configuration (From Project Root)

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Linux / macOS:**
```bash
cp .env.example .env
```

### 2. Setup Virtual Environment

**Windows (PowerShell):**
```powershell
cd backend

# Create virtual environment using the Python launcher (py)
py -m venv venv

# Activate virtual environment in PowerShell
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run backend server
uvicorn app.main:app --reload --port 8000
```

**Linux / macOS:**
```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend server
uvicorn app.main:app --reload --port 8000
```

### Running Tests
Execute the pytest suite:
```powershell
# Windows
py -m pytest tests

# Linux / macOS
pytest tests
```

