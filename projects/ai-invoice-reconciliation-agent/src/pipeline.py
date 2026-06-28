"""Pipeline for Ai Invoice Reconciliation Agent."""
from fastapi import FastAPI
from src.agents.data_extractor import data_extractor
from src.agents.reconciliation_agent import reconciliation_agent
from src.agents.report_generator import report_generator
from src.agents.audit_trail import audit_trail

app = FastAPI(title="Ai Invoice Reconciliation Agent")

@app.post("/run")
def run_pipeline(input_data: dict):
    """Run the full agent pipeline."""
    result = input_data
    result = data_extractor(result)  # Extract transactions from bank feeds, invoices, receipts
    result = reconciliation_agent(result)  # Match transactions, flag anomalies, auto-categorize
    result = report_generator(result)  # Generate P&L, cash flow, balance sheet reports
    result = audit_trail(result)  # Maintain audit trail, flag compliance issues, generate audit packages
    return {"status": "complete", "result": result}

@app.get("/health")
def health():
    return {"status": "ok"}
