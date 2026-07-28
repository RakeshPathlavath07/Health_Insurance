"""
Structured Execution Logger
Appends JSON lines containing session_id, tool_used, latency_ms, status, and estimated_tokens
to backend/data/execution_logs.jsonl.
"""
import os
import json
import time

LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "execution_logs.jsonl")

def log_execution(session_id: str, query: str, tool_used: str, latency_ms: float, success: bool, estimated_tokens: int = 0):
    """Logs structured execution details as a JSON line."""
    try:
        os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "session_id": session_id,
            "query": query,
            "tool_used": tool_used,
            "latency_ms": round(latency_ms, 2),
            "status": "success" if success else "fallback",
            "estimated_tokens": estimated_tokens or (len(query.split()) + 150)
        }
        with open(LOG_FILE_PATH, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Structured logging error: {e}")

if __name__ == "__main__":
    log_execution("test_sess", "Which policy has zero room rent?", "compare_policies", 145.2, True, 180)
    print(f"Logged sample entry to: {LOG_FILE_PATH}")
