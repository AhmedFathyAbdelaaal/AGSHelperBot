FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for sqlite3 or build tools)
# RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory if it doesn't exist (though COPY . . might bring it if empty dir is preserved, but usually not)
RUN mkdir -p data

CMD ["python", "src/main.py"]
