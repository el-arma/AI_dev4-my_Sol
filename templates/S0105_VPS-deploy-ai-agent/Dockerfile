FROM python:3.12-slim

WORKDIR /chatLLM

# Copy only requirements first (better caching)
COPY requirements.txt .

RUN pip install uv && uv pip install --system --no-cache -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]