FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/
COPY scripts/ scripts/

EXPOSE 8080

CMD ["uvicorn", "src.deepthought.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
