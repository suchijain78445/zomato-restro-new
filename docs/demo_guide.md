# Zomato AI Recommendation System - Demo & Manual Verification Guide

This guide provides step-by-step instructions for running, testing, and demonstrating the AI-powered restaurant recommendation engine.

---

## 1. Quick Start / Environment Setup

### Option A: Local Python Execution

1. **Activate virtual environment & install requirements:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate   # On Windows
   # source venv/bin/activate # On Linux/macOS
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   *Set `GROQ_API_KEY` or `OPENAI_API_KEY` in `.env` if using real LLM API ranking.*

3. **Run Data Preprocessing (One-time step):**
   ```bash
   python scripts/preprocess_dataset.py
   ```

4. **Start Backend API Service:**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Start Streamlit Frontend (In a separate terminal):**
   ```bash
   streamlit run frontend/app.py
   ```

---

### Option B: Docker Compose Execution

Run both API and Frontend in containerized environment:

```bash
docker compose build
docker compose up
```

Access:
- **FastAPI Backend:** [http://localhost:8000](http://localhost:8000)
- **API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Streamlit Frontend UI:** [http://localhost:8501](http://localhost:8501)

---

## 2. Automated Smoke Test Suite

To verify system health and core features automatically:

```bash
python -m pytest
```

---

## 3. Demo Scenarios & Sample Queries

### Demo Scenario 1: Standard AI Recommendation
- **Goal:** Experience personalized AI explanations based on user notes.
- **Payload (cURL):**
  ```bash
  curl -X POST "http://localhost:8000/recommendations" \
       -H "Content-Type: application/json" \
       -d '{
         "city": "Bangalore",
         "location": "Koramangala 5th Block",
         "budget_tier": "medium",
         "cuisine": "Italian",
         "min_rating": 4.0,
         "top_k": 5,
         "notes": "Looking for romantic vibe, delicious pasta, and great ambiance"
       }'
  ```
- **Expected Outcome:**
  - `total_matches` > 0
  - Ranked recommendations return structured restaurant details, rating, cost, and AI explanation tailored to romantic ambiance and pasta.

---

### Demo Scenario 2: Auto Constraint Relaxation
- **Goal:** Test fallback behavior when user parameters are overly narrow.
- **Payload (cURL):**
  ```bash
  curl -X POST "http://localhost:8000/recommendations" \
       -H "Content-Type: application/json" \
       -d '{
         "city": "Bangalore",
         "location": "Indiranagar",
         "budget_tier": "low",
         "cuisine": "Mongolian",
         "min_rating": 4.8,
         "top_k": 3,
         "notes": "Cheap eats only"
       }'
  ```
- **Expected Outcome:**
  - `relaxed_constraints` list populated (e.g. relaxed `min_rating` or `cuisine`).
  - System dynamically relaxes constraints until candidates are found.

---

### Demo Scenario 3: Streamlit UI Walkthrough
1. Open [http://localhost:8501](http://localhost:8501).
2. Select **City**: `Bangalore`.
3. Observe location dropdown automatically populating locations within Bangalore.
4. Select **Cuisine**: `North Indian`.
5. Select **Budget**: `Medium (₹500 - ₹1500)`.
6. Add **Personal Notes**: `"Family dining with vegetarian options and good desserts"`.
7. Click **"Get AI Recommendations"**.
8. View recommendation cards with badges, pricing, ratings, direct Zomato link, and AI generated reasoning.

---

## 4. Manual Smoke Test Verification Checklist

- [x] **Health Check:** `GET http://localhost:8000/health` returns `{"status": "ok"}`
- [x] **Metadata Endpoints:** `GET /metadata/cities`, `/metadata/locations`, `/metadata/cuisines` respond with JSON lists
- [x] **Input Validation:** Sending an invalid city returns 400 Bad Request with helpful error message listing valid cities
- [x] **Streamlit UI:** Loads metadata dynamically into dropdowns without UI freeze
- [x] **LLM Execution & Fallback:** System successfully generates recommendations via LLM when API key is provided, or seamlessly falls back to rule-based ranking if offline/mock.
