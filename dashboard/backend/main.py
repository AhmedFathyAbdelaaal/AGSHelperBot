from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI(title="AGSHelperBot Dashboard API")

# DB Paths (Assuming backend is run from within the same container, or we mount /app/data)
# We will use /app/data in Docker, for local testing we will construct path relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))

def get_db_connection(db_name: str):
    db_path = os.path.join(DATA_DIR, db_name)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/status")
def get_user_statuses():
    try:
        conn = get_db_connection("statuses.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, status, timestamp FROM user_status")
        rows = cursor.fetchall()
        conn.close()
        return [{"user_id": row["user_id"], "status": row["status"], "timestamp": row["timestamp"]} for row in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/vclogs")
def get_vclogs(limit: int = 50):
    try:
        conn = get_db_connection("vclogs.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM voice_sessions ORDER BY join_time DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/backuplogs")
def get_backuplogs(limit: int = 50):
    try:
        conn = get_db_connection("backuplogs.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM backup_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        return []

@app.get("/api/requests")
def get_requests():
    try:
        conn = get_db_connection("requests.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, type, user_id, title, description, status, created_at FROM requests ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/reports")
def get_reports(limit: int = 50):
    try:
        conn = get_db_connection("reports.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, username, content_main, content_notes, timestamp FROM reports ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        return {"error": str(e)}

# Serve Angular static files in production (only if directory exists)
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist", "frontend", "browser")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

    # Catch all route for Angular HTML5 routing (so deep links work)
    @app.exception_handler(404)
    async def custom_404_handler(_, __):
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
