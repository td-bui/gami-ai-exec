from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from redis import Redis
from rq import Queue
from rq.job import Job
import os

from worker import run_code, execute_problem

app = FastAPI()

class CodeRequest(BaseModel):
    code: str

class TestCase(BaseModel):
    id: int
    input: str

class CompareCodeRequest(BaseModel):
    userCode: str
    solutionCode: str
    testCases: List[TestCase]

# Connect to Redis and RQ
redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", 6379))
redis_user = os.environ.get("REDIS_USER", None)
redis_password = os.environ.get("REDIS_PASSWORD", None)

redis_conn = Redis(
    host=redis_host,
    port=redis_port,
    username=redis_user,
    password=redis_password,
    decode_responses=True
)
q = Queue(connection=redis_conn)

@app.post("/execute")
async def execute_code_endpoint(req: CodeRequest):
    job = q.enqueue(run_code, req.code)
    return {"job_id": job.get_id()}

@app.post("/execute-problem")
async def execute_problem_endpoint(req: CompareCodeRequest):
    job = q.enqueue(execute_problem, req.userCode, req.solutionCode, [tc.dict() for tc in req.testCases])
    return {"job_id": job.get_id()}

@app.get("/")
async def root():
    return {"message": "Welcome to the Code Execution API with RQ!"}

@app.get("/result/{job_id}")
async def get_result(job_id: str):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return {"status": "not_found", "output": "", "error": "Job not found"}

    if job.is_finished:
        return {"status": "finished", "output": job.result.get("output", ""), "error": job.result.get("error", "")}
    elif job.is_failed:
        return {"status": "failed", "output": "", "error": "Job failed"}
    else:
        return {"status": "pending", "output": "", "error": ""}

@app.get("/result-problem/{job_id}")
async def get_result_problem(job_id: str):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return {"status": "not_found", "results": [], "error": "Job not found"}

    if job.is_finished:
        return {"status": "finished", "results": job.result.get("results", []), "error": job.result.get("error", "")}
    elif job.is_failed:
        return {"status": "failed", "results": [], "error": "Job failed"}
    else:
        return {"status": "pending", "results": [], "error": ""}

# DO NOT start the worker loop here!