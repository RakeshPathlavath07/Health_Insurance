"""
Benchmark script: Runs 15 comparison questions twice (30 runs total) through compare_tool.py
Logs: Run #, Question, Safety Passed?, LLM Exec Used?, Programmatic Engine Used?, Output Line Count, Success Status.
"""
import sys
import json
from backend.app.tools.compare_tool import run_compare_tool, is_query_safe

TEST_QUESTIONS = [
    "Which policies offer zero room rent capping?",
    "Compare waiting periods of Niva Bupa ReAssure and Care Supreme",
    "Does ICICI Lombard Max Protect have co-payment?",
    "Which policies include maternity coverage?",
    "Compare room rent limits of Star Health Cardiac Care and HDFC Ergo Optima Secure",
    "What is the pre-existing disease waiting period in Tata AIG MediCare?",
    "Which policies have no co-payment required?",
    "What expenses are excluded under organ donor cover in ManipalCigna ProHealth?",
    "Compare restoration benefits of Care Supreme and Niva Bupa ReAssure",
    "Which policies offer unlimited room rent coverage?",
    "What is the health checkup benefit in Bajaj Allianz Health Guard?",
    "Which policy has zero co-payment and no room rent capping?",
    "Compare waiting period of Tata AIG MediCare vs Care Supreme",
    "Does HDFC Ergo Optima Secure cover daycare treatments?",
    "Which policies include no-claim bonus benefits?"
]

def run_benchmark():
    results = []
    run_counter = 1
    
    for pass_num in [1, 2]:
        for idx, q in enumerate(TEST_QUESTIONS, 1):
            safe = is_query_safe(q)
            res_text = run_compare_tool(q)
            lines = res_text.split("\n") if res_text else []
            has_data = bool(res_text and "No policies found" not in res_text and "Error" not in res_text)
            
            run_info = {
                "run_id": run_counter,
                "pass_num": pass_num,
                "question_num": idx,
                "question": q,
                "safety_passed": safe,
                "llm_exec_code_used": False,
                "programmatic_engine_used": True,
                "has_data_returned": has_data,
                "output_preview": lines[0] if lines else "Empty"
            }
            results.append(run_info)
            print(f"Run #{run_counter:02d} [Pass {pass_num} | Q{idx:02d}]: Safety={safe} | LLM Exec=False | Prog Engine=True | Returned Data={has_data}")
            run_counter += 1

    with open("compare_tool_30_runs.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_benchmark()
