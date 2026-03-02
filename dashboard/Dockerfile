# Stage 1: Build Angular Frontend
FROM node:20 AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npx @angular/cli@17 build --configuration production

# Stage 2: Serve with FastAPI
FROM python:3.11-slim
WORKDIR /app

# Install FastAPI dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy compiled frontend from Stage 1
COPY --from=frontend-build /app/frontend/dist/frontend/browser ./frontend/dist/frontend/browser

# Start Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "3000"]
