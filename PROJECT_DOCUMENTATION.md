# Health Insurance Multi-Agent System — Architecture & Documentation

## 1. System Overview & Architecture
The **Health Insurance Recommendation Agent** is a multi-agent GenAI platform built for Indian health insurance analysis. It combines structured MongoDB querying, IRDAI risk data lookups, FAISS vector retrieval with live PDF search fallback, and hybrid conversation memory.

### Architecture Tech Stack:
- **Frontend UI**: Streamlit (Session state, chat history, live tool badges)
- **Backend API**: FastAPI (Asynchronous endpoints, CORS, Pydantic validation)
- **Master Orchestrator**: LangChain ReAct Agent backed by Groq (`llama-3.3-70b-versatile`)
- **Structured Database**: MongoDB Atlas Cloud (`insurance_db.health_insurance`)
- **Unstructured RAG**: FAISS Vector Store + HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
- **Web Search**: Tavily Search API
- **Evaluation**: Benchmark test suite (`backend/eval_suite.py`)

---

## 2. Detailed Component Specifications

### 1. Streamlit Frontend (`frontend/streamlit_app.py`)
- **Input**: User text query + Session ID in `st.session_state`.
- **Processing**: Calls `POST http://localhost:8000/chat`. Renders response markdown and displays tool badge.
- **Output Format**: Interactive Chat UI with tool badges (`🛠️ Tool Called: compare_policies`).

### 2. FastAPI REST API (`backend/app/main.py`)
- **Input**: `ChatRequest(session_id: str, query: str)` JSON payload.
- **Processing**: Validates input, invokes Master Dispatcher, applies Guardrails validation.
- **Output Format**: JSON `ChatResponse(session_id, query, answer, tools_used)`.

### 3. ReAct Master Dispatcher (`backend/app/dispatcher.py`)
- **Input**: `session_id: str`, `query: str`.
- **Processing**: Loads memory, constructs ReAct prompt with 3 tools (`compare_policies`, `insurer_financial_risk`, `policy_document_qa`). Executes agent loop and captures tool names.
- **Output Format**: Dict `{"answer": str, "tools_used": list[str]}`.

### 4. Text-to-MongoDB Compare Tool (`backend/app/tools/compare_tool.py`)
- **Input**: Natural language comparison query string.
- **Processing**: Prompts `deep_model` to generate single-line PyMongo `find()` code. Validates query safety via `is_query_safe()`. Executes against MongoDB Atlas.
- **Output Format**: Structured feature rating & details comparison string.

### 5. Dynamic Insurer Risk Tool (`backend/app/tools/risk_tool.py`)
- **Input**: Query containing provider/insurer name.
- **Processing**: Extracts provider name via `fuzzy_matcher.py`. Looks up versioned metrics in `data/risk_data.json`. Enforces IRDAI report disclaimer.
- **Output Format**: Formatted risk string with CSR, ICR, Solvency Ratio, and `IRDAI FY2024` disclaimer.

### 6. Centralized Fuzzy Matcher (`backend/app/tools/fuzzy_matcher.py`)
- **Input**: `query: str`, `score_threshold: int = 50`.
- **Processing**: Resolves aliases, calculates `rapidfuzz` partial ratios against canonical registries in `data/policy_names.py`.
- **Output Format**: Tuple `(canonical_provider_name: str, match_score: int)`.

### 7. FAISS Vector Store & PDF Ingest Pipeline (`backend/app/ingestion/pdf_ingest.py`)
- **Input**: PDF URL or path, `provider`, `policy_name`.
- **Processing**: Extracts text (`pdfplumber`), chunks (500 chars), embeds with local `all-MiniLM-L6-v2` model. Appends to `faiss_index/` without overwriting existing index.
- **Output Format**: Boolean success status + FAISS index stored on disk.

### 8. Web Search Agent (`backend/app/ingestion/web_search_agent.py`)
- **Input**: `policy_name: str`.
- **Processing**: Executes Tavily Search for policy PDF, prompts `light_model` to return direct PDF link.
- **Output Format**: Direct PDF URL string or empty string.

### 9. RAG Tool (`backend/app/tools/rag_tool.py`)
- **Input**: Natural language policy query.
- **Processing**: Searches FAISS vector store. If empty, triggers Web Search Agent -> PDF Ingest pipeline -> Re-searches FAISS. Synthesizes answer using `light_model`.
- **Output Format**: Detailed synthesized response string.

### 10. Hybrid Session Memory Manager (`backend/app/memory.py`)
- **Input**: `session_id: str`, turn messages.
- **Processing**: `ConversationSummaryBufferMemory(max_token_limit=300)`. Keeps recent turns verbatim and summarizes older turns using `light_model`.
- **Output Format**: Chat history message objects.

### 11. Guardrails (`backend/app/guardrails.py`)
- **Input**: `query: str`, `raw_answer: str`.
- **Processing**: Validates answer formatting and output non-emptiness.
- **Output Format**: Clean validated answer string.

### 12. Automated Evaluation Benchmark Suite (`backend/eval_suite.py`)
- **Input**: 5 benchmark test dicts.
- **Processing**: Executes tests, verifies tool selection accuracy and answer keywords.
- **Output Format**: Accuracy summary report string (`Overall Accuracy: 5/5 Passed (100.0% Correct)`).

---

## 3. Core Data Schemas

### MongoDB Document Schema (`insurance_db.health_insurance`)
```json
{
  "provider": "hdfc-ergo",
  "insurance_name": "hdfc-ergo-optima-secure",
  "description": "Flagship product offering 4X coverage benefit.",
  "features": {
     "maternity-cover": {"rating": "bad", "details": "Not covered in Optima Secure"},
     "room-rent-limit": {"rating": "good", "details": "No room rent capping"},
     "waiting-period": {"rating": "good", "details": "30 days initial, 36 months PED"}
  }
}
```

### Risk Data Schema (`backend/data/risk_data.json`)
```json
{
  "as_of_year": 2024,
  "source": "IRDAI Annual Report FY2023-24",
  "data": {
    "icici-lombard": {
      "display_name": "ICICI Lombard General Insurance",
      "CSR": "98.6%",
      "ICR": "78.4%",
      "solvency_ratio": "2.62",
      "summary": "Strong claim settlement ratio (98.6%) and healthy solvency."
    }
  }
}
```
