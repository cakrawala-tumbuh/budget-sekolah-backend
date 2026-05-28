# ── Stage: test ───────────────────────────────────────────────────────────────
# Gunakan stage ini untuk menjalankan pytest di dalam container.
# docker build --target test -t budget-backend-ypii:test .
# docker run --rm budget-backend-ypii:test
FROM python:3.12-slim AS test

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY app/ ./app/
COPY tests/ ./tests/

CMD ["python", "-m", "pytest", "tests/", "-v"]

# ── Stage: production (default) ───────────────────────────────────────────────
FROM python:3.12-slim AS production

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
