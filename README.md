# Zomato AI Restaurant Recommendation System

An AI-powered restaurant recommendation engine that combines deterministic filtering over real Zomato data with LLM-based ranking and explanations.

---

## Architecture Overview

1. **Data Foundation**: Ingests and cleans Hugging Face Zomato dataset, normalizes ratings & costs, extracts budget tiers (`low`, `medium`, `high`), and caches as compressed Parquet & metadata JSON.
2. **Deterministic Filter Service**: Filters candidate restaurants by location, cuisine, budget, ratings, and booking/ordering preferences with automated fallback constraint relaxation.
3. **LLM Ranking Engine**: Constructs prompt contexts with candidate subsets, sends to LLM provider (Groq / OpenAI / Ollama / Mock), parses structured JSON, and enforces hallucination guarding against returned IDs.
4. **FastAPI Backend**: Exposes REST endpoints for metadata lookup (`/metadata/*`) and recommendations (`/recommendations`).
5. **Streamlit UI**: Dynamic user interface supporting location filtering, budget selection, custom preference notes, and rich recommendation cards.

---

## Requirements

- **Python**: 3.11+
- **Docker & Docker Compose**: (Optional, for containerized run)

---

## Quick Start

### 1. Local Python Setup

```bash
# Create and activate virtual environment
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

#### Key Environment Variables

| Variable | Default Value | Description |
| --- | --- | --- |
| `API_HOST` | `0.0.0.0` | Host IP address for FastAPI server |
| `API_PORT` | `8000` | Port for FastAPI server |
| `CORS_ORIGINS` | `["http://localhost:8501", "http://localhost:3000"]` | Allowed CORS origins |
| `API_BASE_URL` | `http://localhost:8000` | FastAPI URL used by Streamlit frontend |
| `DATASET_NAME` | `ManikaSaini/zomato-restaurant-recommendation` | Hugging Face dataset reference |
| `DATA_CACHE_PATH` | `data/processed/restaurants.parquet` | Parquet cache path |
| `METADATA_DIR` | `data/metadata` | Directory for exported metadata JSON files |
| `LLM_PROVIDER` | `groq` | Provider choice: `groq`, `openai`, `ollama`, or `mock` |
| `GROQ_API_KEY` | `""` | Groq API Key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq Model ID |
| `OPENAI_API_KEY` | `""` | OpenAI API Key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI Model ID |
| `MAX_CANDIDATES_FOR_LLM` | `25` | Max candidate restaurants sent to LLM prompt |
| `DEFAULT_TOP_K` | `5` | Default recommendation count |

---

### 3. Data Preprocessing (One-time CLI)

Preprocess and cache the Hugging Face dataset locally:

```bash
python scripts/preprocess_dataset.py
```

---

### 4. Running locally

#### Option A: Run Backend & Frontend Separately

```bash
# Terminal 1: Start FastAPI server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Streamlit UI
streamlit run frontend/app.py
```

- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Frontend UI**: [http://localhost:8501](http://localhost:8501)

#### Option B: Run Standalone Streamlit App

```bash
streamlit run streamlit_app.py
```

#### Option C: Run via Docker Compose

```bash
docker compose build
docker compose up
```

---

## 🚀 Streamlit Cloud Deployment

This repository is pre-configured for one-click deployment on **Streamlit Community Cloud**:

1. **Push to GitHub**: Ensure your latest changes are pushed to your GitHub repository.
2. **New App on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io) and click **"New app"**.
   - Select your repository, branch (`main`), and set **Main file path** to:
     ```text
     streamlit_app.py
     ```
3. **Configure Secrets**:
   - In Streamlit Cloud dashboard, navigate to **Settings > Secrets**.
   - Paste your API key configuration (see `.streamlit/secrets.toml.example`):
     ```toml
     LLM_PROVIDER = "groq"
     GROQ_API_KEY = "your-groq-api-key-here"
     GROQ_MODEL = "llama-3.3-70b-versatile"
     ```
4. **Deploy**: Click **Deploy!** Streamlit Cloud will automatically install `requirements.txt`, initialize the dataset on boot, and run in standalone in-memory engine mode.


---

## Verification & Testing

Run full unit and integration test suite:

```bash
python -m pytest
```

---

## Directory Structure

```
.
├── Dockerfile                  # FastAPI API Dockerfile
├── docker-compose.yml          # Docker Compose orchestration
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
├── README.md                   # Main documentation
├── docs/                       # Architecture & demo guides
│   ├── demo_guide.md           # Manual verification & sample queries
│   ├── architecture.md         # System architecture specification
│   └── implementation-plan.md  # Master phase roadmap
├── src/                        # Backend FastAPI service
│   ├── main.py                 # FastAPI app entrypoint & logging setup
│   ├── config.py               # Settings management via Pydantic
│   ├── models/                 # Domain & API schemas
│   ├── data/                   # Loader, preprocessor & repository
│   ├── services/               # Filter service & recommendation service
│   ├── llm/                    # LLM clients, prompt builder & schemas
│   └── api/                    # Metadata & recommendation route handlers
├── frontend/                   # Frontend Streamlit Application
│   ├── app.py                  # Main Streamlit UI layout & state
│   ├── api_client.py           # HTTP client helper for backend
│   └── Dockerfile              # Frontend Dockerfile
├── scripts/                    # CLI scripts
│   └── preprocess_dataset.py   # Dataset ingestion CLI script
├── tests/                      # Automated test suite
│   ├── test_filter_service.py
│   ├── test_health.py
│   ├── test_integration_flow.py
│   ├── test_llm_parser.py
│   ├── test_metadata_api.py
│   ├── test_preprocessor.py
│   ├── test_prompt_builder.py
│   └── test_recommendation_service.py
└── data/                       # Processed data cache & exported metadata
    ├── processed/              # Parquet cache
    └── metadata/               # Metadata JSONs (cities, locations, cuisines)
```

---

## Demo & Verification

For detailed demo scenarios, sample cURL requests, and manual verification checklists, see [docs/demo_guide.md](file:///c:/Users/HP/Documents/Project%20Management/Cursor%20Project/antigravity/docs/demo_guide.md).
