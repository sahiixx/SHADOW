
# === Base Image ===
FROM python:3.10-slim

# === Environment Variables ===
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_HOME=/app

# === Install dependencies ===
WORKDIR /app
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/app sh
ENV PATH="/app:${PATH}"

# === Clone Repo ===
RUN git clone https://github.com/sahiixx/Coral-BlackboxAI-Agent.git .
WORKDIR /app/Coral-BlackboxAI-Agent

# === Set up Python environment ===
RUN python -m venv .venv
ENV VIRTUAL_ENV=/app/Coral-BlackboxAI-Agent/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies using uv
RUN pip install uv && uv sync

# === Add fake .env ===
RUN echo "BLACKBOXAI_API_KEY=demo-key\nBLACKBOXAI_URL=https://api.blackbox.ai\nMODEL_NAME=blackboxai/openai/gpt-4.1-mini" > .env

# === Run Agent ===
CMD ["uv", "run", "python", "main.py"]
