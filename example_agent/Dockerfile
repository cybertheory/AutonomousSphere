FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Expose port
EXPOSE 8080

# Set environment variables with defaults that can be overridden
ENV AGENT_NAME=ExampleAgent
ENV AGENT_URL=http://example-agent:8080
ENV REGISTRY_URL=http://registry:8081
ENV CHAT_SERVICE_URL=http://api:8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]