FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir fastapi uvicorn redis rq \
    numpy pandas matplotlib scipy networkx sympy

RUN useradd -m runner
USER runner

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]