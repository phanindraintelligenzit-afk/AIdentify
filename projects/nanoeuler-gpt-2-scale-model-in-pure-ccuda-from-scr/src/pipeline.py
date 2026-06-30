"""Pipeline for Nanoeuler Gpt 2 Scale Model In Pure Ccuda From Scr."""
from fastapi import FastAPI
from src.agents.agent_1 import agent_1
from src.agents.agent_2 import agent_2
from src.agents.agent_3 import agent_3

app = FastAPI(title="Nanoeuler Gpt 2 Scale Model In Pure Ccuda From Scr")

@app.post("/run")
def run_pipeline(input_data: dict):
    """Run the full agent pipeline."""
    result = input_data
    result = agent_1(result)  # Stage 1 processing for other automation
    result = agent_2(result)  # Stage 2 processing for other automation
    result = agent_3(result)  # Stage 3 processing for other automation
    return {"status": "complete", "result": result}

@app.get("/health")
def health():
    return {"status": "ok"}
