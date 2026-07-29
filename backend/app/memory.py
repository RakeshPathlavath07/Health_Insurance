"""
Session Memory Manager — Fast ConversationBufferWindowMemory
Preserves the last k conversation turns in memory with zero import errors.
"""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from langchain.memory import ConversationBufferWindowMemory
except (ImportError, ModuleNotFoundError):
    try:
        from langchain_community.memory import ConversationBufferWindowMemory
    except (ImportError, ModuleNotFoundError):
        class SimpleMessage:
            def __init__(self, type: str, content: str):
                self.type = type
                self.content = content

        class ConversationBufferWindowMemory:
            """Fallback zero-dependency sliding window memory implementation."""
            def __init__(self, k: int = 6, memory_key: str = "chat_history", return_messages: bool = True):
                self.k = k
                self.memory_key = memory_key
                self.return_messages = return_messages
                self.messages = []

            def save_context(self, inputs: dict, outputs: dict):
                user_input = inputs.get("input") or inputs.get("query") or ""
                ai_output = outputs.get("output") or outputs.get("answer") or ""
                if user_input:
                    self.messages.append(SimpleMessage("human", str(user_input)))
                if ai_output:
                    self.messages.append(SimpleMessage("ai", str(ai_output)))
                max_msgs = self.k * 2
                if len(self.messages) > max_msgs:
                    self.messages = self.messages[-max_msgs:]

            def load_memory_variables(self, inputs: dict = None) -> dict:
                return {self.memory_key: self.messages}

            def clear(self):
                self.messages = []

# In-memory session registry: session_id -> ConversationBufferWindowMemory
_SESSION_MEMORIES = {}

def get_memory(session_id: str) -> ConversationBufferWindowMemory:
    """
    Retrieves or creates a ConversationBufferWindowMemory instance for a session_id.
    Retains the last 6 turns for instant, zero-latency history retrieval.
    """
    if session_id not in _SESSION_MEMORIES:
        _SESSION_MEMORIES[session_id] = ConversationBufferWindowMemory(
            k=6,
            memory_key="chat_history",
            return_messages=True
        )
    return _SESSION_MEMORIES[session_id]

def clear_session_memory(session_id: str):
    """Resets memory state for a given session."""
    if session_id in _SESSION_MEMORIES:
        del _SESSION_MEMORIES[session_id]

if __name__ == "__main__":
    print("=== Testing Memory Layer Standalone ===")
    test_session = "test_session_123"
    mem = get_memory(test_session)

    turns = [
        ("Hi, I am looking for a health insurance plan for my family.",
         "Hello! I can help you compare Indian health insurance policies. What features are most important to you?"),
        ("I want maternity cover and zero room rent capping.",
         "For maternity cover, Star Health Comprehensive and Care Supreme are good options. Optima Secure offers zero room rent capping.")
    ]

    for user_msg, ai_msg in turns:
        mem.save_context({"input": user_msg}, {"output": ai_msg})

    memory_variables = mem.load_memory_variables({})
    chat_history = memory_variables.get("chat_history", [])
    print(f"Total stored message turns: {len(chat_history)}")
    for msg in chat_history:
        print(f"[{msg.type.upper()}]: {msg.content}")
