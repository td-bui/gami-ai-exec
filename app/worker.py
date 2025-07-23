import sys
import tempfile
import os
import subprocess
import time
import resource
from rq import Worker, Connection
from redis import Redis

def build_code_to_run(code: str, test_input: str) -> str:
    return f"{code}\nprint({test_input})"

def run_code(code: str):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        tmp.write(code)
        tmp_path = tmp.name
    try:
        start_time = time.time()
        usage_start = resource.getrusage(resource.RUSAGE_CHILDREN)
        result = subprocess.run(
            ["python3", tmp_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        usage_end = resource.getrusage(resource.RUSAGE_CHILDREN)
        end_time = time.time()
        runtime = end_time - start_time
        # Memory usage in kilobytes (maxrss), convert to MB
        mem_usage_kb = usage_end.ru_maxrss - usage_start.ru_maxrss
        # On Linux, ru_maxrss is in kilobytes; on macOS, it's in bytes
        if sys.platform == "darwin":
            mem_usage_mb = mem_usage_kb / (1024 * 1024)
        else:
            mem_usage_mb = mem_usage_kb / 1024
        return {
            "output": result.stdout.strip(),
            "error": result.stderr.strip(),
            "runtime": runtime,
            "memory": mem_usage_mb
        }
    except subprocess.TimeoutExpired:
        return {"output": "", "error": "Execution timed out.", "runtime": None, "memory": None}
    finally:
        os.remove(tmp_path)

def execute_problem(user_code: str, solution_code: str, test_cases: list):
    results = []
    for tc in test_cases:
        # Run solution code
        sol_code_to_run = build_code_to_run(solution_code, tc["input"])
        sol_result = run_code(sol_code_to_run)
        # Run user code
        user_code_to_run = build_code_to_run(user_code, tc["input"])
        user_result = run_code(user_code_to_run)
        # Compare
        passed = (not sol_result["error"]) and (not user_result["error"]) and (user_result["output"] == sol_result["output"])
        results.append({
            "id": tc["id"],
            "input": tc["input"],
            "solutionOutput": sol_result["output"],
            "userOutput": user_result["output"],
            "passed": passed,
            "solutionError": sol_result["error"],
            "userError": user_result["error"],
            "solutionRuntime": sol_result.get("runtime"),
            "solutionMemory": sol_result.get("memory"),
            "userRuntime": user_result.get("runtime"),
            "userMemory": user_result.get("memory"),
        })
    return {"results": results, "error": ""}

if __name__ == "__main__":
    redis_conn = Redis(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        username=os.environ.get("REDIS_USER", None),
        password=os.environ.get("REDIS_PASSWORD", None),
        decode_responses=True
    )
    with Connection(redis_conn):
        worker = Worker(['default'])
        worker.work()