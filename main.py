from fastapi import FastAPI
from datetime import datetime, timezone, timedelta
from urllib.parse import unquote
import json, os

app = FastAPI()
DATA_FILE = "applog.json"
CST = timezone(timedelta(hours=8))

def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {}

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False)

@app.get("/toggle/{app_name}")
def toggle(app_name: str):
    app_name = unquote(app_name)
    data = load()
    now = datetime.now(CST)
    now_str = now.isoformat()
    if app_name not in data:
        data[app_name] = {"status": "closed", "sessions": []}
    app_data = data[app_name]
    if app_data["status"] == "closed":
        app_data["status"] = "open"
        app_data["last_open"] = now_str
        save(data)
        return {"app": app_name, "action": "opened"}
    else:
        open_time = datetime.fromisoformat(app_data["last_open"])
        duration = int((now - open_time).total_seconds() / 60)
        app_data["status"] = "closed"
        app_data["sessions"].append({"date": now.strftime("%Y-%m-%d"), "open": app_data["last_open"], "close": now_str, "minutes": duration})
        cutoff = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        app_data["sessions"] = [s for s in app_data["sessions"] if s["date"] >= cutoff]
        save(data)
        return {"app": app_name, "action": "closed", "duration_minutes": duration}

@app.get("/report")
def report():
    data = load()
    now = datetime.now(CST)
    today = now.strftime("%Y-%m-%d")
    result = {}
    for app_name, app_data in data.items():
        today_sessions = [s for s in app_data.get("sessions", []) if s["date"] == today]
        total = sum(s["minutes"] for s in today_sessions)
        result[app_name] = {"count": len(today_sessions), "minutes": total}
    return {"date": today, "report": result}

@app.get("/health")
def health():
    return {"status": "ok"}
