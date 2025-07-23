FROM python:3.11-slim

WORKDIR /app

# Set the PYTHONPATH environment variable to include the current directory
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Copy all code including app/ directory
COPY . .

# Install dependencies (add requirements.txt if you have one)
RUN pip install --no-cache-dir fastapi uvicorn redis rq \
    numpy pandas matplotlib scipy networkx sympy

# Create a non-root user for security
RUN useradd -m runner
USER runner

# Expose port 80 for Railway HTTP health checks and logs
EXPOSE 80

# Start FastAPI app (main.py is in app/ directory)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]