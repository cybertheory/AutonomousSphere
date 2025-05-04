FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Expose port
EXPOSE 8081

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]