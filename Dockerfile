FROM python:3.11

WORKDIR /app

# Install dependencies first (better caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Cloud Run uses PORT=8080
ENV PORT=8080

# Start FastAPI with uvicorn
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port $PORT"]
