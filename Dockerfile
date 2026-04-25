# === Base Image ===
FROM python:3.13-slim

# === Environment Variables ===
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# === Install dependencies ===
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl git gcc build-essential libffi-dev && rm -rf /var/lib/apt/lists/*

# === Clone Repo ===
RUN git clone https://github.com/sahiixx/Coral-BlackboxAI-Agent.git /app/Coral-BlackboxAI-Agent
WORKDIR /app/Coral-BlackboxAI-Agent

# === Set up Python environment ===
RUN python -m venv .venv
ENV VIRTUAL_ENV=/app/Coral-BlackboxAI-Agent/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies using pip
RUN pip install --upgrade pip && \
    pip install langchain langchain-core langchain-community pydantic httpx anthropic PyGithub langchain-mcp-adapters

# === Add fake .env ===
RUN printf "BLACKBOXAI_API_KEY=demo-key\nBLACKBOXAI_URL=https://api.blackbox.ai\nMODEL_NAME=blackboxai/openai/gpt-4.1-mini\n" > .env

# === Run Agent ===
CMD ["python", "main.py"]
