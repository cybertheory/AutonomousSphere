# Use minimal Python base
FROM python:3.11-slim

# System-level dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set environment
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false && poetry install --no-root

# Copy source code
COPY . .

# Expose AppService port (as configured in `config.yaml`)
EXPOSE 29333

# Default startup command
CMD ["python", "main.py"]
