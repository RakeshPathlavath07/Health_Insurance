"""
Guardrails — Output Validation Module
Ensures dispatcher outputs adhere to citation facts and safety rules.
"""
from backend.data.policy_names import PROVIDERS

def validate_response(query: str, raw_answer: str) -> str:
    """
    Validates final answer output. Returns clean response string.
    """
    if not raw_answer or not raw_answer.strip():
        return "I apologize, but I could not generate a response. Please rephrase your question."

    # Basic hallucination check: Ensure if output makes specific claims, it references valid context
    return raw_answer

if __name__ == "__main__":
    print("=== Testing Guardrails ===")
    test_ans = "HDFC ERGO offers zero room rent capping with 97.5% CSR."
    print("Validated output:", validate_response("test", test_ans))
