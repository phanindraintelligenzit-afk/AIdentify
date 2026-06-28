FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e .
COPY src/ src/
COPY tests/ tests/
CMD ["uvicorn", "src.pipeline:app", "--host", "0.0.0.0", "--port", "8000"]
