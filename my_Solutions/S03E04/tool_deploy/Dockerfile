FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /S03E04-tool-app

# Copy only requirements first (better caching)
COPY requirements.txt .

RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]