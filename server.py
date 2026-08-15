"""FastAPI web server for AI Study Room Scheduling Agent."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.orchestrator import Orchestrator
from agents.user_behavior_agent import UserBehaviorAgent
from agents.resource_scheduler import ResourceSchedulerAgent
from agents.anomaly_detector import AnomalyDetectorAgent
from agents.task_executor import TaskExecutorAgent

# ── Pydantic models ──────────────────────────────────────────────

class ReserveRequest(BaseModel):
    user_id: str
    request_text: str
    preferred_area: Optional[str] = None
    duration_minutes: Optional[int] = 120

class CancelRequest(BaseModel):
    user_id: str

class ReleaseRequest(BaseModel):
    user_id: str

# ── Global orchestrator ──────────────────────────────────────────

orchestrator: Optional[Orchestrator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    orchestrator = Orchestrator()
    orchestrator.register_agent(UserBehaviorAgent())
    orchestrator.register_agent(ResourceSchedulerAgent())
    orchestrator.register_agent(AnomalyDetectorAgent())
    orchestrator.register_agent(TaskExecutorAgent())
    logging.info("Multi-Agent system initialized")
    yield

app = FastAPI(title="AI Study Room Agent", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Helper: convert Seat to dict ─────────────────────────────────

def seat_to_dict(seat) -> dict:
    return {
        "seat_id": seat.seat_id,
        "area": seat.area,
        "floor": seat.floor,
        "has_power": seat.has_power,
        "is_quiet_zone": seat.is_quiet_zone,
        "is_window_seat": seat.is_window_seat,
        "status": seat.status.value,
        "current_user_id": seat.current_user_id,
        "reservation_until": seat.reservation_until.isoformat() if seat.reservation_until else None,
        "daily_usage_count": seat.daily_usage_count,
        "quality_score": seat.quality_score,
    }

# ── API Routes ───────────────────────────────────────────────────

@app.get("/api/status")
def get_status():
    """System overview statistics."""
    scheduler = orchestrator.get_agent("scheduler_agent")
    executor = orchestrator.get_agent("executor_agent")
    anomaly = orchestrator.get_agent("anomaly_agent")

    stats = scheduler.get_stats() if scheduler else {}
    estats = executor.get_stats() if executor else {}
    areport = anomaly.get_report() if anomaly else {}

    return {
        "timestamp": datetime.now().isoformat(),
        "cycles": orchestrator.step_count,
        "seats": stats,
        "execution": estats,
        "anomaly": {
            "total_anomalies": areport.get("total_anomalies", 0),
            "blacklisted_users": areport.get("blacklisted_users", 0),
            "active_monitoring": areport.get("active_monitoring", 0),
        },
    }

@app.get("/api/seats")
def get_seats():
    """Get all seats with current status."""
    scheduler = orchestrator.get_agent("scheduler_agent")
    if not scheduler:
        raise HTTPException(500, "Scheduler agent not found")
    return {"seats": [seat_to_dict(s) for s in scheduler.seats]}

@app.get("/api/areas")
def get_areas():
    """Get area utilization summary."""
    scheduler = orchestrator.get_agent("scheduler_agent")
    if not scheduler:
        raise HTTPException(500, "Scheduler agent not found")
    summary = {}
    for area in ["A", "B", "C"]:
        area_seats = [s for s in scheduler.seats if s.area == area]
        available = sum(1 for s in area_seats if s.is_available())
        total = len(area_seats)
        summary[area] = {
            "total": total,
            "available": available,
            "occupied": total - available,
            "utilization": round((total - available) / total * 100, 1) if total else 0,
        }
    return {"areas": summary}

@app.post("/api/reserve")
def reserve(req: ReserveRequest):
    """Process a reservation request through the multi-agent pipeline."""
    if not req.user_id or not req.request_text:
        raise HTTPException(400, "user_id and request_text are required")

    responses = orchestrator.run_cycle(req.request_text, meta={
        "user_id": req.user_id,
        "preferred_area": req.preferred_area,
        "duration_minutes": req.duration_minutes,
    })

    # Find the execution result and analysis details
    result = {"status": "unknown", "detail": {}, "agent_log": []}
    for resp in responses:
        entry = {
            "sender": resp.sender,
            "type": resp.msg_type.value,
            "content": resp.content,
        }
        result["agent_log"].append(entry)

        if resp.msg_type.value == "execution_result":
            result["status"] = resp.content.get("status", "unknown")
            result["detail"] = resp.content
        elif resp.msg_type.value == "analysis_result":
            result["analysis"] = resp.content.get("analysis", {})
        elif resp.msg_type.value == "feedback":
            if "error" in resp.content:
                result["status"] = "error"
                result["detail"] = resp.content

    return result

@app.post("/api/cancel")
def cancel(req: CancelRequest):
    """Cancel a reservation."""
    if not req.user_id:
        raise HTTPException(400, "user_id is required")
    responses = orchestrator.run_cycle("cancel my reservation",
                                       meta={"user_id": req.user_id})
    result = {"status": "unknown", "detail": {}, "agent_log": []}
    for resp in responses:
        entry = {"sender": resp.sender, "type": resp.msg_type.value, "content": resp.content}
        result["agent_log"].append(entry)
        if resp.msg_type.value == "execution_result":
            result["status"] = resp.content.get("status", "unknown")
            result["detail"] = resp.content
    return result

@app.post("/api/release")
def release(req: ReleaseRequest):
    """Release a seat."""
    if not req.user_id:
        raise HTTPException(400, "user_id is required")
    responses = orchestrator.run_cycle("release my seat",
                                       meta={"user_id": req.user_id})
    result = {"status": "unknown", "detail": {}, "agent_log": []}
    for resp in responses:
        entry = {"sender": resp.sender, "type": resp.msg_type.value, "content": resp.content}
        result["agent_log"].append(entry)
        if resp.msg_type.value == "execution_result":
            result["status"] = resp.content.get("status", "unknown")
            result["detail"] = resp.content
    return result

@app.get("/api/history")
def get_history():
    """Get execution history."""
    executor = orchestrator.get_agent("executor_agent")
    scheduler = orchestrator.get_agent("scheduler_agent")
    anomaly = orchestrator.get_agent("anomaly_agent")

    return {
        "executions": executor.execution_log[-50:] if executor else [],
        "allocations": scheduler.allocation_history[-50:] if scheduler else [],
        "anomalies": anomaly.anomaly_log[-50:] if anomaly else [],
    }

@app.get("/")
def index():
    """Serve the main frontend page."""
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
