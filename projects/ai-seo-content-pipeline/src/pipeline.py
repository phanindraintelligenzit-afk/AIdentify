"""Pipeline for Ai Seo Content Pipeline."""
from fastapi import FastAPI
from src.agents.content_generator import content_generator
from src.agents.scheduler import scheduler
from src.agents.analytics_agent import analytics_agent

app = FastAPI(title="Ai Seo Content Pipeline")

@app.post("/run")
def run_pipeline(input_data: dict):
    """Run the full agent pipeline."""
    result = input_data
    result = content_generator(result)  # Generate platform-specific content from briefs and trends
    result = scheduler(result)  # Optimize posting schedule by platform, audience, engagement data
    result = analytics_agent(result)  # Track performance, generate insights, recommend optimizations
    return {"status": "complete", "result": result}

@app.get("/health")
def health():
    return {"status": "ok"}
