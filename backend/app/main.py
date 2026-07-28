"""
FastAPI Backend Application
Exposes health insurance assistant REST API endpoints for session-based chat.
Includes confidence and relevance evaluation metrics.
"""
import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from backend.app.dispatcher import handle_query
from backend.app.guardrails import validate_response

app = FastAPI(
    title="Health Insurance Recommendation API",
    description="Multi-agent GenAI backend for Indian Health Insurance recommendations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str = Field(default="default_session", description="Session ID for chat memory continuity")
    query: str = Field(..., description="User question or query string")

class ChatResponse(BaseModel):
    session_id: str
    query: str
    answer: str
    tools_used: list[str] = Field(default=[], description="List of tools invoked by the agent")
    confidence_score: int = Field(default=95, description="Relevance and confidence evaluation score (0-100%)")
    confidence_level: str = Field(default="High Precision", description="Human-readable confidence category description")

@app.get("/")
def read_root():
    return {"message": "Health Insurance Recommendation Agent API is running."}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    try:
        res_dict = route_and_execute(request.query.strip(), session_id=request.session_id)
        raw_answer = res_dict.get("answer", "")
        tools_used = res_dict.get("tools_used", [])
        confidence_score = res_dict.get("confidence_score", 95)
        confidence_level = res_dict.get("confidence_level", "High Precision")

        validated_answer = validate_response(request.query, raw_answer)

        return ChatResponse(
            session_id=request.session_id,
            query=request.query,
            answer=validated_answer,
            tools_used=tools_used,
            confidence_score=confidence_score,
            confidence_level=confidence_level
        )
    except Exception as e:
        traceback.print_exc()
        print(f"[CHAT ERROR TRACEBACK]: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port)
