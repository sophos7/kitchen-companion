FROM python:3.14-slim

WORKDIR /app

# Install Node.js for npm
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install npm dependencies (Datadog RUM)
COPY package.json package-lock.json* ./
RUN npm install --production

# Copy application files
COPY src/ ./src/

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
