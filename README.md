# Gami-AI Code Execution Service

This project is a secure, asynchronous Python code execution service built with FastAPI and Redis Queue (RQ). It is designed to safely run untrusted code in an isolated environment, compare user submissions against a reference solution for multiple test cases, and measure performance metrics like runtime and memory usage.

This service is a core component of the Gami-AI platform, providing the backend for evaluating programming exercises.

## Features

-   **Asynchronous Execution**: Leverages RQ and Redis to handle code execution in background worker processes, preventing the API from blocking and ensuring responsiveness.
-   **Sandboxed Environment**: Executes code in isolated `subprocess` calls to ensure safety and prevent malicious code from affecting the host system.
-   **Resource Monitoring**: Measures runtime and memory usage for each execution using the `resource` module.
-   **Timeout Protection**: Automatically terminates jobs that exceed a 5-second execution time limit to prevent long-running or infinite loops.
-   **Comprehensive Testing**: Compares user code against a reference solution across multiple test cases to validate correctness.
-   **Intelligent Output Comparison**: Correctly compares outputs, even for custom objects, by serializing their state (`__dict__`) to a consistent JSON format.
-   **Containerized**: Includes a `Dockerfile` for easy and consistent deployment of the API server and workers.

## Architecture

The service operates on a job queue model to handle code execution securely and efficiently:

1.  The FastAPI server (`app/main.py`) receives an API request to execute code for a problem.
2.  It enqueues a job in a Redis queue and immediately returns a `job_id` to the client.
3.  One or more separate RQ worker processes (`app/worker.py`) are constantly listening to the Redis queue.
4.  A worker picks up the job, executes the user's code and the solution code against all test cases in a sandboxed subprocess, and records the output, errors, and performance metrics.
5.  The result is stored back in Redis, associated with the `job_id`.
6.  The client polls the `/result-problem/{job_id}` endpoint to retrieve the execution outcome once the job is complete.

## Setup and Installation

### 1. Prerequisites

-   Python 3.11+
-   A running Redis instance.

### 2. Clone the Repository

```bash
git clone https://github.com/td-bui/gami-ai-exec.git
cd gami-ai-exec
```

### 3. Set up Environment

It is recommended to use a virtual environment.

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 4. Install Dependencies

The required packages are listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

The application can be configured using environment variables for the Redis connection.

-   `REDIS_HOST`: The hostname of your Redis server (default: `localhost`).
-   `REDIS_PORT`: The port for your Redis server (default: `6379`).
-   `REDIS_USER`: The username for Redis (optional).
-   `REDIS_PASSWORD`: The password for Redis (optional).

## Running the Service Locally

You need to run two separate processes: the FastAPI web server and at least one RQ worker.

**Terminal 1: Start the FastAPI Server**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2: Start the RQ Worker**

```bash
# Ensure your virtual environment is active
python app/worker.py
```

## Running with Docker

The provided `Dockerfile` can be used to run both the API server and the workers.

### 1. Build the Docker Image

```bash
docker build -t gami-ai-exec .
```

### 2. Run the Docker Containers

You need a running Redis instance. If you are using Docker, you can link the containers.

**Step 1: Start Redis (if you don't have one)**

```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

**Step 2: Run the FastAPI Server Container**

This command runs the API server and links it to the Redis container. Note that the `Dockerfile` exposes port 80, which we map to 8001 on the host.

```bash
docker run -d -p 8001:80 \
  --env REDIS_HOST=redis \
  --link redis \
  --name gami-ai-exec-server \
  gami-ai-exec
```

**Step 3: Run the RQ Worker Container**

This command overrides the `Dockerfile`'s default `CMD` to start the worker script instead of the server.

```bash
docker run -d \
  --env REDIS_HOST=redis \
  --link redis \
  --name gami-ai-exec-worker \
  gami-ai-exec python app/worker.py
```

## API Endpoints

### Execute a Problem

-   **Endpoint**: `POST /execute-problem`
-   **Description**: Submits a user's code, a solution's code, and a list of test cases for evaluation.
-   **Request Body**:
    ```json
    {
      "userCode": "def add(a, b): return a + b",
      "solutionCode": "def add(a, b): return a + b",
      "testCases": [
        { "id": 1, "input": "add(1, 2)" },
        { "id": 2, "input": "add(-1, 1)" }
      ]
    }
    ```
-   **Response**:
    ```json
    {
      "job_id": "some-unique-job-id"
    }
    ```

### Get Problem Result

-   **Endpoint**: `GET /result-problem/{job_id}`
-   **Description**: Poll this endpoint to get the results of a problem execution.
-   **Response (`status: "finished"`)**:
    ```json
    {
        "status": "finished",
        "results": [
            {
                "id": 1,
                "input": "add(1, 2)",
                "solutionOutput": "3",
                "userOutput": "3",
                "passed": true,
                "solutionError": "",
                "userError": "",
                "solutionRuntime": 0.01,
                "solutionMemory": 2.5,
                "userRuntime": 0.01,
                "userMemory": 2.5
            }
        ],
        "error": ""
    }
    ```
-   **Response (`status: "pending"`)**:
    ```json
    {
        "status": "pending",
        "results": [],
        "error": ""
    }
    ```