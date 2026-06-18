from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from datetime import datetime, timezone, timedelta
import httpx, os

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok", "message": "小克上线啦"}

CST = timezone(timedelta(hours=8))
SUPABASE_URL = "https://tzycnotzddttithceexi.supabase.co"
SUPABASE_KEY = "sb_publishable_w_N1p1DFQj4Qow8osWdscw_qphHqXa1"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

@app.get("/toggle/{app_name:path}")
async def toggle(app_name: str):
    now = datetime.now(CST)
    now_str = now.isoformat()
    
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SUPABASE_URL}/rest/v1/app_sessions",
            params={"app_name": f"eq.{app_name}", "closed_at": "is.null", "order": "opened_at.desc", "limit": "1"},
            headers=HEADERS
        )
        rows = r.json()
        
        if not rows:
            await client.post(
                f"{SUPABASE_URL}/rest/v1/app_sessions",
                json={"app_name": app_name, "opened_at": now_str},
                headers=HEADERS
            )
            return {"app": app_name, "action": "opened"}
        else:
            row = rows[0]
            open_time = datetime.fromisoformat(row["opened_at"])
            duration = int((now - open_time).total_seconds() / 60)
            await client.patch(
                f"{SUPABASE_URL}/rest/v1/app_sessions",
                params={"id": f"eq.{row['id']}"},
                json={"closed_at": now_str, "minutes": duration},
                headers=HEADERS
            )
            return {"app": app_name, "action": "closed", "duration_minutes": duration}

@app.get("/report")
async def report():
    now = datetime.now(CST)
    today = now.strftime("%Y-%m-%d")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SUPABASE_URL}/rest/v1/app_sessions",
            params={"opened_at": f"gte.{today}", "order": "opened_at.desc"},
            headers=HEADERS
        )
        rows = r.json()
    result = {}
    for row in rows:
        name = row["app_name"]
        if name not in result:
            result[name] = {"count": 0, "minutes": 0}
        if row["closed_at"]:
            result[name]["count"] += 1
            result[name]["minutes"] += row["minutes"] or 0
    return {"date": today, "report": result}

@app.get("/sessions")
async def sessions():
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SUPABASE_URL}/rest/v1/app_sessions",
            params={"order": "opened_at.desc", "limit": "20"},
            headers=HEADERS
        )
        return r.json()

@app.get("/health")
def health():
    return {"status": "ok"}

mcp = FastApiMCP(app)
mcp.mount()
