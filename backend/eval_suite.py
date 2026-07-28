"""
Automated Evaluation Benchmark Suite
Executes 15 benchmark questions against the multi-agent system dispatcher.
Verifies tool routing accuracy, keyword presence, and execution latency.
"""
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import json
import time
from backend.app.dispatcher import route_and_execute

EVAL_CASES = [
    {
        "id": "EVAL-01",
        "category": "Compare Tool",
        "query": "Which policies offer zero room rent capping?",
        "expected_tool": "compare_policies",
        "expected_keywords": ["room rent", "capping", "icici"]
    },
    {
        "id": "EVAL-02",
        "category": "Compare Tool",
        "query": "Compare waiting periods of Niva Bupa ReAssure and Care Supreme",
        "expected_tool": "compare_policies",
        "expected_keywords": ["waiting", "month"]
    },
    {
        "id": "EVAL-03",
        "category": "Compare Tool",
        "query": "Does ICICI Lombard Max Protect have co-payment?",
        "expected_tool": "compare_policies",
        "expected_keywords": ["co-payment"]
    },
    {
        "id": "EVAL-04",
        "category": "Compare Tool",
        "query": "Which policies include maternity coverage?",
        "expected_tool": "compare_policies",
        "expected_keywords": ["maternity"]
    },
    {
        "id": "EVAL-05",
        "category": "Risk Tool",
        "query": "Check risk metrics for ICICI Lombard",
        "expected_tool": "insurer_financial_risk",
        "expected_keywords": ["claim settlement", "icr", "solvency", "98.6%"]
    },
    {
        "id": "EVAL-06",
        "category": "Risk Tool",
        "query": "Which insurer has a solvency ratio above 2.5?",
        "expected_tool": "insurer_financial_risk",
        "expected_keywords": ["2.62", "icici"]
    },
    {
        "id": "EVAL-07",
        "category": "Risk Tool",
        "query": "What is the Claim Settlement Ratio of Star Health?",
        "expected_tool": "insurer_financial_risk",
        "expected_keywords": ["star health", "95"]
    },
    {
        "id": "EVAL-08",
        "category": "RAG Document QA",
        "query": "What is the pre-existing disease waiting period in Niva Bupa ReAssure policy?",
        "expected_tool": "policy_document_qa",
        "expected_keywords": ["waiting period", "month"]
    },
    {
        "id": "EVAL-09",
        "category": "RAG Document QA",
        "query": "Does HDFC Ergo Optima Secure cover daycare procedures?",
        "expected_tool": "policy_document_qa",
        "expected_keywords": ["daycare", "day care"]
    },
    {
        "id": "EVAL-10",
        "category": "RAG Document QA",
        "query": "Nivabupa re-assure policy me waiting period kitna h?",
        "expected_tool": "policy_document_qa",
        "expected_keywords": ["waiting", "month"]
    },
    {
        "id": "EVAL-11",
        "category": "Compare Tool",
        "query": "Which policies offer unlimited room rent coverage?",
        "expected_tool": "compare_policies",
        "expected_keywords": ["room", "rent"]
    },
    {
        "id": "EVAL-12",
        "category": "Compare Tool",
        "query": "Which policies include no-claim bonus benefits?",
        "expected_tool": "compare_policies",
        "expected_keywords": ["bonus"]
    },
    {
        "id": "EVAL-13",
        "category": "Risk Tool",
        "query": "What is the Incurred Claim Ratio of HDFC Ergo?",
        "expected_tool": "insurer_financial_risk",
        "expected_keywords": ["hdfc", "%"]
    },
    {
        "id": "EVAL-14",
        "category": "RAG Document QA",
        "query": "What expenses are covered under organ donor benefit in Care Supreme?",
        "expected_tool": "policy_document_qa",
        "expected_keywords": ["organ", "donor"]
    },
    {
        "id": "EVAL-15",
        "category": "Compare Tool",
        "query": "Which policy has zero co-payment and no room rent capping?",
        "expected_tool": "compare_policies",
        "expected_keywords": ["co-payment", "room"]
    },
    {
        "id": "EVAL-16",
        "category": "General Chat / Out of Scope",
        "query": "what you do? why are you here?",
        "expected_tool": "general_chat",
        "expected_keywords": ["health insurance", "advisor"]
    },
    {
        "id": "EVAL-17",
        "category": "General Chat / Out of Scope",
        "query": "who are you",
        "expected_tool": "general_chat",
        "expected_keywords": ["advisor", "insurance"]
    },
    {
        "id": "EVAL-18",
        "category": "General Chat / Out of Scope",
        "query": "hello good morning",
        "expected_tool": "general_chat",
        "expected_keywords": ["hello", "advisor"]
    },
    {
        "id": "EVAL-19",
        "category": "General Chat / Out of Scope",
        "query": "what can I ask you?",
        "expected_tool": "general_chat",
        "expected_keywords": ["policy", "compare"]
    },
    {
        "id": "EVAL-20",
        "category": "Short Casual English",
        "query": "can you tell me a joke?",
        "expected_tool": "general_chat",
        "expected_keywords": ["health insurance", "advisor"]
    },
    {
        "id": "EVAL-21",
        "category": "Short Casual English",
        "query": "is this app working?",
        "expected_tool": "general_chat",
        "expected_keywords": ["health insurance", "help"]
    },
    {
        "id": "EVAL-22",
        "category": "Nonsense / Gibberish",
        "query": "asdfghjk 123456",
        "expected_tool": "general_chat",
        "expected_keywords": ["health insurance", "advisor"]
    },
    {
        "id": "EVAL-23",
        "category": "Nonsense / Gibberish",
        "query": "xyz pdq random nonsense query",
        "expected_tool": "general_chat",
        "expected_keywords": ["health insurance", "help"]
    }
]

def run_eval_suite():
    print(f"=== STARTING AUTOMATED EVALUATION SUITE ({len(EVAL_CASES)} BENCHMARK QUESTIONS) ===")
    
    passed_cases = 0
    failed_cases = 0
    results = []

    start_suite = time.time()

    for item in EVAL_CASES:
        case_id = item["id"]
        category = item["category"]
        query = item["query"]
        expected_tool = item["expected_tool"]
        expected_keywords = item["expected_keywords"]

        print(f"\n[RUNNING {case_id}] {category} — '{query}'")
        try:
            res = route_and_execute(query, session_id="eval_suite_session")
            actual_tool = res.get("tool")
            answer = res.get("answer", "").lower()
            confidence = res.get("confidence_score", 0)
            latency = res.get("latency_ms", 0)

            # Check tool routing accuracy
            tool_match = (actual_tool == expected_tool)
            
            # Check keyword presence in synthesized answer
            keyword_match = any(k.lower() in answer for k in expected_keywords)
            
            case_passed = tool_match and keyword_match

            if case_passed:
                passed_cases += 1
                status_str = "PASS ✅"
            else:
                failed_cases += 1
                status_str = "FAIL ❌"

            eval_res = {
                "id": case_id,
                "category": category,
                "query": query,
                "expected_tool": expected_tool,
                "actual_tool": actual_tool,
                "tool_match": tool_match,
                "keyword_match": keyword_match,
                "confidence_score": confidence,
                "latency_ms": latency,
                "status": status_str
            }
            results.append(eval_res)

            print(f"  Result: {status_str} | Tool: {actual_tool} (Expected: {expected_tool}) | Latency: {latency:.1f}ms | Confidence: {confidence}%")

        except Exception as e:
            failed_cases += 1
            print(f"  Result: FAIL ❌ (Exception: {e})")
            results.append({
                "id": case_id,
                "category": category,
                "query": query,
                "status": "FAIL ❌ (Exception)",
                "error": str(e)
            })

    total_time = round(time.time() - start_suite, 2)
    pass_rate = round((passed_cases / len(EVAL_CASES)) * 100, 2)

    summary = {
        "total_cases": len(EVAL_CASES),
        "passed": passed_cases,
        "failed": failed_cases,
        "pass_rate_percentage": pass_rate,
        "total_duration_sec": total_time,
        "eval_results": results
    }

    report_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n==================================================")
    print("=== AUTOMATED EVALUATION SUITE RESULTS ===")
    print(f"Total Benchmark Cases: {len(EVAL_CASES)}")
    print(f"Passed: {passed_cases} / {len(EVAL_CASES)} ({pass_rate}%)")
    print(f"Failed: {failed_cases} / {len(EVAL_CASES)}")
    print(f"Total Test Duration: {total_time}s")
    print(f"Detailed Results saved to: {report_path}")
    print("==================================================")

if __name__ == "__main__":
    run_eval_suite()
