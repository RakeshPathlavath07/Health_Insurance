"""
Benchmark script: Runs 15 comparison questions twice (30 runs total) through rebuilt compare_tool.py.
Logs for each run:
- Path used: llm_success (LLM primary path succeeded) vs llm_fallback (Deterministic engine fallback used)
- Question
- Returned valid data?
- Generated PyMongo code snippet
"""
import os
import json
from backend.app.tools.compare_tool import run_compare_tool, is_query_safe, PATH_LOG_FILE

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

def run_30_run_benchmark():
    # Reset path log file if exists
    if os.path.exists(PATH_LOG_FILE):
        os.remove(PATH_LOG_FILE)

    results = []
    run_counter = 1
    llm_success_count = 0
    llm_fallback_count = 0

    print("=== STARTING 30-RUN BENCHMARK (15 QUESTIONS x 2 REPEATS) ===")

    for pass_num in [1, 2]:
        for idx, q in enumerate(TEST_QUESTIONS, 1):
            # Capture log length before execution
            log_lines_before = []
            if os.path.exists(PATH_LOG_FILE):
                with open(PATH_LOG_FILE, "r") as f:
                    log_lines_before = f.readlines()

            res_text = run_compare_tool(q)

            # Read log length after execution
            path_used = "unknown"
            if os.path.exists(PATH_LOG_FILE):
                with open(PATH_LOG_FILE, "r") as f:
                    lines_after = f.readlines()
                    if len(lines_after) > len(log_lines_before):
                        last_line = lines_after[-1]
                        if "llm_success" in last_line:
                            path_used = "llm_success"
                            llm_success_count += 1
                        elif "llm_fallback" in last_line:
                            path_used = "llm_fallback"
                            llm_fallback_count += 1

            has_data = bool(res_text and "No policies found" not in res_text and "Error" not in res_text)

            run_info = {
                "run_id": run_counter,
                "pass_num": pass_num,
                "question_num": idx,
                "question": q,
                "path_used": path_used,
                "returned_data": has_data,
                "output_preview": res_text.split("\n")[0] if res_text else "Empty"
            }
            results.append(run_info)
            print(f"Run #{run_counter:02d} [Pass {pass_num} | Q{idx:02d}]: Path='{path_used}' | Data={has_data} | Question: '{q[:40]}...'")
            run_counter += 1

    summary = {
        "total_runs": 30,
        "llm_success": llm_success_count,
        "llm_fallback": llm_fallback_count,
        "llm_success_percentage": round((llm_success_count / 30) * 100, 2),
        "results": results
    }

    with open("benchmark_30_runs_new_compare.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\n==================================================")
    print("=== FINAL 30-RUN BENCHMARK SUMMARY ===")
    print(f"Total Runs: 30")
    print(f"LLM Primary Path Success (llm_success): {llm_success_count} / 30 ({summary['llm_success_percentage']}%)")
    print(f"Deterministic Engine Fallback (llm_fallback): {llm_fallback_count} / 30 ({round(100 - summary['llm_success_percentage'], 2)}%)")
    print("==================================================")

if __name__ == "__main__":
    run_30_run_benchmark()
