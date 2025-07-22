FROM python:3.11-slim

WORKDIR /app

COPY . .

# Install FastAPI, Uvicorn, and popular DSA/scientific libraries
RUN pip install --no-cache-dir fastapi uvicorn redis rq \
    numpy pandas matplotlib scipy networkx sympy

RUN useradd -m runner
USER runner

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]