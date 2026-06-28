import os
import json
import subprocess
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="AIdentify Mission Control", version="1.0.0")

# Setup templates and static files
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Data paths
AIDENTIFY_DIR = Path(r"C:\Users\Admin\Projects\AIdentify-marketplace")
KNOWLEDGE_DIR = Path(r"C:\Users\admin\knowledge")
MARKETPLACE_DATA = Path(r"C:\Users\Admin\Projects\AIdentify-marketplace\config\projects.json")

# Pydantic models
class AgentStatus(BaseModel):
    name: str
    status: str  # online, offline, busy
    last_seen: Optional[str] = None
    current_task: Optional[str] = None
    model: Optional[str] = None

class PipelineStatus(BaseModel):
    phase: str
    status: str
    current_project: Optional[str] = None
    progress: int = 0
    last_run: Optional[str] = None

class CronJob(BaseModel):
    name: str
    schedule: str
    status: str
    last_run: Optional[str] = None
    next_run: Optional[str] = None

class MarketplaceProject(BaseModel):
    id: str
    name: str
    status: str
    category: str
    github_url: str
    created_at: str

class DashboardData(BaseModel):
    agents: List[AgentStatus]
    pipeline: Optional[PipelineStatus]
    crons: List[CronJob]
    projects: List[MarketplaceProject]
    knowledge_stats: Dict[str, int]
    timestamp: str

# Helper functions
def get_telegram_bot_status():
    """Check if Telegram bots are running by checking gateway logs"""
    agents = [
        {"name": "OWL (Orchestrator)", "profile": "default", "model": "qwen2.5-coder:7b"},
        {"name": "Researcher", "profile": "researcher", "model": "deepseek-r1:7b"},
        {"name": "Writer", "profile": "writer", "model": "qwen2.5-coder:7b"},
        {"name": "SocialAF", "profile": "social", "model": "qwen2.5-coder:7b"},
        {"name": "OutreachAF", "profile": "outreach", "model": "qwen2.5-coder:7b"},
    ]
    
    agents_data = []
    for agent in agents:
        pid_file = Path(f"/c/Users/Admin/AppData/Local/hermes/profiles/{agent['profile']}/gateway.pid")
        if pid_file.exists():
            try:
                with open(pid_file) as f:
                    pid = json.load(f)["pid"]
                # Check if process is alive
                try:
                    subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], 
                                 capture_output=True, check=True)
                    status = "online"
                except:
                    status = "offline"
            except:
                status = "offline"
        else:
            status = "offline"
        
        agents_data.append({
            "name": agent["name"],
            "status": status,
            "model": agent["model"],
            "last_seen": datetime.now().isoformat()
        })
    return agents_data

def get_pipeline_status():
    """Get current pipeline status"""
    # Check cron output for latest pipeline run
    output_dir = Path(r"C:\Users\Admin\AppData\Local\hermes\cron\output")
    pipeline_status = {
        "phase": "idle",
        "status": "idle",
        "current_project": None,
        "progress": 0,
        "last_run": None
    }
    
    # Check cron output
    pipeline_output = Path(r"C:\Users\Admin\AppData\Local\hermes\cron\output\61beb7fe5017")
    if pipeline_output.exists():
        files = sorted(pipeline_output.glob("*.md"))
        if files:
            latest = sorted(files)[-1]
            content = latest.read_text()
            # Parse for status
            if "BUILD" in content:
                phase = "BUILD"
                status = "running"
            elif "TEST" in content:
                phase = "TEST"
                status = "running"
            elif "PUSH" in content:
                phase = "PUSH"
                status = "running"
            elif "SUCCESS" in content or "✅" in content:
                phase = "DONE"
                status = "success"
            else:
                phase = "SCAN"
                status = "running"
            return {
                "phase": phase,
                "status": status,
                "current_project": "current",
                "progress": 50,
                "last_run": datetime.fromtimestamp(latest.stat().st_mtime).isoformat()
            }
    return {
        "phase": "idle",
        "status": "idle",
        "current_project": None,
        "progress": 0,
        "last_run": None
    }

def get_cron_jobs():
    """Get cron job status from Hermes"""
    cron_dir = Path(r"C:\Users\Admin\AppData\Local\hermes\cron")
    crons = []
    
    # Known crons
    known_crons = [
        {"name": "Business Opportunity Scanner", "schedule": "8:30 AM", "id": "19c6f1409d2f"},
        {"name": "Autonomous Pipeline", "schedule": "9:00 AM", "id": "61beb7fe5017"},
        {"name": "Knowledge Base Improvement", "schedule": "2:00 AM", "id": "108ce83aeaad"},
    ]
    
    for cron in known_crons:
        output_dir = Path(f"C:/Users/Admin/AppData/Local/hermes/cron/output/{cron['id']}")
        last_run = None
        if output_dir.exists():
            files = list(output_dir.glob("*.txt"))
            if files:
                latest = sorted(files, key=lambda f: f.stat().st_mtime)[-1]
                last_run = datetime.fromtimestamp(latest.stat().st_mtime).isoformat()
        
        crons.append({
            "name": cron["name"],
            "schedule": cron["schedule"],
            "status": "enabled",
            "last_run": last_run,
            "next_run": "tomorrow"  # simplified
        })
    return crons

def get_marketplace_projects():
    """Load projects from marketplace data"""
    if MARKETPLACE_DATA.exists():
        data = json.loads(MARKETPLACE_DATA.read_text())
        projects = []
        for pid, data in data.items():
            projects.append({
                "id": pid,
                "name": data.get("name", pid),
                "status": data.get("status", "unknown"),
                "category": data.get("category", "unknown"),
                "github_url": data.get("github_url", ""),
                "created_at": data.get("created_at", ""),
            }
        return projects
    return []

def get_knowledge_stats():
    """Get knowledge base statistics"""
    stats = {}
    for folder in ["wiki", "sources", "journal", "crm", "people", "tools", "topics"]:
        path = Path(rf"C:\Users\admin\knowledge\{folder}")
        if path.exists():
            count = len(list(path.rglob("*.md")))
            stats[folder] = count
        else:
            stats[folder] = 0
    stats["total"] = sum(stats.values())
    return stats

# API Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "AIdentify Mission Control"
    })

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard():
    """Get all dashboard data"""
    agents = get_telegram_bot_status()
    pipeline = get_pipeline_status()
    crons = get_cron_jobs()
    projects = get_marketplace_projects()
    knowledge_stats = get_knowledge_stats()
    
    return DashboardData(
        agents=agents,
        pipeline=pipeline,
        crons=crons,
        projects=projects,
        knowledge_stats=knowledge_stats,
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/agents", response_model=List[AgentStatus])
async def get_agents():
    return get_telegram_bot_status()

@app.get("/api/pipeline", response_model=PipelineStatus)
async def get_pipeline():
    return get_pipeline_status()

@app.get("/api/crons", response_model=List[CronJob])
async def get_crons():
    return get_cron_jobs()

@app.get("/api/projects", response_model=List[MarketplaceProject])
async def get_projects():
    return get_marketplace_projects()

@app.get("/api/knowledge/stats")
async def get_stats():
    return get_knowledge_stats()

@app.post("/api/trigger/scan")
async def trigger_scan():
    """Trigger a fresh opportunity scan"""
    try:
        # Run the scanner
        result = subprocess.run(
            ["python3", "scripts/opportunity_scanner.py", "--quick"],
            cwd=r"C:\Users\Admin\Projects\AIdentify-marketplace",
            capture_output=True, text=True, timeout=60
        )
        return {"success": True, "output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trigger/pipeline")
async def trigger_pipeline():
    """Trigger the autonomous pipeline"""
    try:
        # This would trigger the pipeline
        return {"success": True, "message": "Pipeline triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge/process")
async def trigger_knowledge_process():
    """Trigger knowledge base processing"""
    try:
        # This would trigger the knowledge base processing
        return {"success": True, "message": "Knowledge processing triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)