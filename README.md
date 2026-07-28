# Health Insurance Recommendation Agent 🏥🤖

A multi-agent GenAI platform built for Indian health insurance policy analysis, feature comparison, IRDAI financial risk lookups, and natural language Q&A with hybrid memory and voice interaction.

---

## 🏛️ System Architecture

```text
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                        Streamlit Chat UI (Port 8501)                     │
 │   - Centered Bottom Dock (12% Mic Icon + 88% Input Box)                  │
 │   - Client-Side JS Recording State Watcher & Pulsing Recording Banner   │
 │   - Instant Two-Stage Chat Streamer & Text Fill Visibility Fix          │
 │   - Voice STT (Groq Whisper-large-v3) & TTS (gTTS Audio Response)        │
 └────────────────────────────────────┬─────────────────────────────────────┘
                                      │ HTTP REST API
 ┌────────────────────────────────────▼─────────────────────────────────────┐
 │                         FastAPI Backend (Port 8000)                      │
 │                     POST /chat  |  GET /health                           │
 └────────────────────────────────────┬─────────────────────────────────────┘
                                      │
 ┌────────────────────────────────────▼─────────────────────────────────────┐
 │                      Master ReAct Dispatcher Agent                       │
 │  - Intent Classification Router (Groq Llama-3.1-8b-instant)              │
 │  - Programmatic Language Detection (English vs Hinglish)                 │
 │  - Dynamic & Static Confidence Scoring (85% - 98%)                        │
 │  - Structured JSON Line Execution Logging (execution_logs.jsonl)         │
 └───────┬────────────────────────────┼────────────────────────────┬────────┘
         │                            │                            │
 ┌───────▼─────────────┐    ┌─────────▼─────────────┐    ┌─────────▼────────────┐
 │    Compare Tool     │    │       RAG Tool        │    │      Risk Tool       │
 │ (Text-to-MongoDB)   │    │ (FAISS Vector Search) │    │ (IRDAI Risk Lookup)  │
 │  - Primary Path:    │    │  - HuggingFace        │    │  - Claim Settlement  │
 │    LLM PyMongo Code │    │    all-MiniLM-L6-v2  │    │    Ratio (CSR)       │
 │    Generation       │    │  - Live Tavily Web    │    │  - Incurred Claim    │
 │    (Llama-3.3-70b)  │    │    Search Fallback    │    │    Ratio (ICR)       │
 │  - Guardrails &     │    │  - Brand Validation   │    │  - Solvency Ratio    │
 │    Safety Filter    │    │  - Dynamic Distance   │    │  - Versioned IRDAI   │
 │  - Fallback:        │    │    Confidence Score   │    │    FY2024 Report     │
 │    Deterministic    │    │                       │    │                      │
 │    Python Engine    │    │                       │    │                      │
 └───────┬─────────────┘    └─────────┬─────────────┘    └─────────┬────────────┘
         │                            │                            │
 ┌───────▼────────────────────────────▼────────────────────────────▼────────────┐
 │                           Data & Persistence Layer                           │
 │  - MongoDB Atlas Cloud: insurance_db.health_insurance (9 Feature Schema)     │
 │  - MongoDB Atlas Cloud: insurance_db.user_profile (Long-Term Memory)        │
 │  - Short-Term Memory: ConversationSummaryBufferMemory (Session History)     │
 └──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🌐 Live Demo & Deployment Endpoints

- **Frontend Web Application (Streamlit)**: [http://localhost:8501](http://localhost:8501) *(Deployed on Streamlit Community Cloud)*
- **Backend REST API (FastAPI)**: [http://127.0.0.1:8000](http://127.0.0.1:8000) *(Deployed on Render Web Service)*
- **API Health Check**: `curl http://127.0.0.1:8000/health` ➔ `{"status": "healthy"}`

> **Note on Render Free Tier**: Render web services automatically sleep after ~15 minutes of inactivity. The first request after idle will experience a ~30–60 second cold-start delay while the instance spins up.

---

## 📊 Benchmark Results

| Benchmark Metric | Result | Evaluation Method & Description |
| :--- | :---: | :--- |
| **Compare-Tool LLM Primary Path Success** | **86.67%** *(26 / 30 runs)* | Fresh baseline benchmark across 15 comparison questions × 2 repeats. Evaluates how often `deep_model` (`llama-3.3-70b-versatile`) safely generates valid PyMongo queries without hitting the deterministic fallback (13.33%). |
| **Automated Evaluation Suite Pass Rate** | **100.0%** *(15 / 15 cases)* | *Note: Validates tool-routing correctness & key entity presence, not full natural language semantic answer accuracy.* |
| **Dynamic RAG Confidence Scoring** | **0–100% Dynamic** | Normalizes top retrieved chunk's FAISS L2 Euclidean distance $d$ via: $S = \max(0, \min(100, \text{round}((1.0 - d / 2.0) \times 100)))$. |

---

## 📸 Screenshots

### 1. Zero Co-Payment Feature Comparison & Centered Dock Interface
![Zero Co-Payment Query](docs/screenshots/streamlit_chat_dock.png)

### 2. Hinglish Waiting Period Q&A & Live Web Ingestion Fallback
![Hinglish Q&A and Web Search Fallback](docs/screenshots/voice_input_recording.png)

---

## ✨ Key Features & Component Architecture

### 1. User Interface & Streamlit UX Innovations (`streamlit_app.py`)
- **Centered Bottom Input Dock**: Single capsule containing a 12% Microphone Icon on the left + 88% Text Input Box on the right (`bottom: 24px`, `max-width: 800px`).
- **Client-Side JS Recording Watcher**: Injected zero-height JavaScript component (`components.html`) monitoring the mic recorder iframe state (`⏹️` recording vs `🎙️` idle) to dynamically toggle the pulsing recording banner without Streamlit page reruns.
- **High-Contrast Input Text Styling**: Specific CSS rules enforcing `-webkit-text-fill-color: #FFFFFF !important` and `caret-color: #FFFFFF !important` to ensure typed text remains crisp and visible across all browser themes and UA autofill styles.
- **Instant Two-Stage Chat Streamer**: User question renders ON SCREEN IMMEDIATELY before backend query execution begins.
- **Voice STT & TTS**: Groq Whisper API (`whisper-large-v3`) transcribes voice recordings; `gTTS` synthesizes audio responses.

### 2. Master ReAct Orchestrator & Dispatcher (`dispatcher.py`)
- **Model**: Groq `llama-3.1-8b-instant` with fast rule-based heuristic routing.
- **Routing Categories**:
  - `compare_policies`: Text-to-MongoDB feature comparison.
  - `insurer_financial_risk`: IRDAI financial metrics lookup.
  - `policy_document_qa`: Vector store retrieval & document Q&A.
- **Language Matching**: `is_query_hinglish()` regex detection routes English queries to `ENGLISH_SYNTHESIS_PROMPT` and Hinglish queries to `HINGLISH_SYNTHESIS_PROMPT`.

### 3. Compare Tool (`compare_tool.py`)
- **Primary Path**: Uses `deep_model` (`llama-3.3-70b-versatile`) to generate read-only PyMongo code string (`list(collection.find({...}))`).
- **Safety Check**: `is_query_safe(code)` blocks destructive write/drop commands.
- **Fallback Path**: If LLM generation fails safety, throws an exception, or returns empty results, it safely falls back to a deterministic Python feature filtering engine.
- **Path Logging**: Logs every execution (`llm_success` vs `llm_fallback` with `failure_reason`) to `compare_tool_paths.log`.

### 4. Dynamic RAG Tool (`rag_tool.py`)
- **Vector Search**: Local FAISS index + HuggingFace `all-MiniLM-L6-v2` embeddings.
- **Dynamic Confidence Score**: Uses `similarity_search_with_score()` to compute top chunk L2 Euclidean distance $d$, normalized to a 0–100 score.
- **Live Ingestion Fallback**: Triggers Tavily search to fetch, download, chunk, and embed policy PDFs on-the-fly when local context is absent or mismatched.

### 5. Dynamic Risk Tool (`risk_tool.py`)
- Versioned IRDAI FY2024 financial metrics (CSR, ICR, Solvency Ratio) with explicit `as_of_year: 2024` disclaimers.

### 6. Dual Memory Architecture
- **Short-Term Memory**: `ConversationSummaryBufferMemory` retains recent turns verbatim while summarizing older turns past 1000 tokens.
- **Long-Term Memory**: MongoDB Atlas `insurance_db.user_profile` persists stated user preferences (e.g., maternity interest, budget conscious) across sessions.

---

## 🛠️ MongoDB Atlas Policy Schema (9 Features)

The `insurance_db.health_insurance` collection contains policy feature documents formatted as:

```json
{
  "provider": "icici-lombard",
  "insurance_name": "icici-lombard-max-protect-classic",
  "features": {
    "co-payment": {"rating": "good", "details": "No co-payment for age < 60 years"},
    "room-rent-limit": {"rating": "good", "details": "No room rent capping for single private room"},
    "pre-post-hospitalization": {"rating": "good", "details": "60 days pre, 180 days post"},
    "restoration-benefit": {"rating": "good", "details": "100% restoration"},
    "day-care-treatments": {"rating": "good", "details": "All day care procedures covered"},
    "waiting-period": {"rating": "average", "details": "30 days initial, 36 months PED"},
    "no-claim-bonus": {"rating": "good", "details": "50% increase per year up to 100%"},
    "maternity-cover": {"rating": "bad", "details": "Not covered"},
    "disease-sub-limit": {"rating": "good", "details": "No sub-limits on specific diseases"}
  }
}
```

---

## 🚀 Getting Started

### 1. Installation
```bash
# Clone repository
git clone https://github.com/RakeshPathlavath07/personal_dashboard.git
cd personal_dashboard

# Install dependencies
pip install -r requirements.txt
pip install -r frontend/requirements.txt
```

### 2. Environment Setup (`.env`)
Create a `.env` file in the project root:
```ini
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/
```

### 3. Seed MongoDB Atlas Database
```bash
python3 backend/app/ingestion/scrape_policy_data.py
```

### 4. Run Servers Locally

**Start FastAPI Backend**:
```bash
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

**Start Streamlit Frontend**:
```bash
python3 -m streamlit run frontend/streamlit_app.py --server.port 8501
```

---

## 🧪 Testing & Evaluation

### Run Benchmark Suite (15 Test Cases)
```bash
python3 -m backend.eval_suite
```

### Run 30-Run Compare Tool Benchmark
```bash
python3 test_30_runs_new_compare.py
```

---

## 📝 License
MIT License. Built for Indian Health Insurance Recommendation Research.
