from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import src.database as db
from src.models import SensorData

app = FastAPI(title="Fleet Dashboard")

@app.on_event("startup")
def startup():
    db.init_db()

app.mount("/web", StaticFiles(directory="web"), name="web")

@app.get("/", response_class=HTMLResponse)
def index():
    return Path("web/index.html").read_text()

@app.post("/api/devices/{device_id}/metrics")
def post_metrics(device_id: str, data: SensorData):
    db.upsert_device(device_id)
    db.insert_metrics(device_id, data.model_dump())
    return {"ok": True, "device_id": device_id}

@app.get("/api/fleet/status")
def fleet_status():
    devices = db.get_all_devices()
    return {
        "total_devices": len(devices),
        "healthy": len([d for d in devices if d['status'] == 'healthy']),
        "warning": len([d for d in devices if d['status'] == 'warning']),
        "error": len([d for d in devices if d['status'] == 'error']),
        "devices": devices
    }

@app.get("/api/devices/{device_id}/metrics")
def device_metrics(device_id: str):
    metrics = db.get_device_metrics(device_id)
    return {"device_id": device_id, "metrics": metrics}

@app.get("/api/alerts")
def alerts():
    return {"alerts": db.get_alerts()}
