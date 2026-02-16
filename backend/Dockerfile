FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY scripts/ scripts/

RUN pip install --no-cache-dir .

EXPOSE 8080

CMD ["uvicorn", "deepthought.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
