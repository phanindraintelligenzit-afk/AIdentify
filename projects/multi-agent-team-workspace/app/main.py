# Multi-Agent Team Workspace

"""
FastAPI application for managing tasks assigned to humans or AI agents.
Features shared context, handoff protocols, and audit trails.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import tasks, context, handoffs, audit

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multi-Agent Team Workspace",
    description="A workspace for managing tasks assigned to humans or AI agents.",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(tasks.router, prefix="/api")
app.include_router(context.router, prefix="/api")
app.include_router(handoffs.router, prefix="/api")
app.include_router(audit.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/")
async def root():
    return {
        "message": "Multi-Agent Team Workspace",
        "docs": "/docs",
        "dashboard": "/dashboard",
    }
