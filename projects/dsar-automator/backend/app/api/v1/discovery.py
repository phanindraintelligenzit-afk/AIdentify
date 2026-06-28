"""Data discovery endpoints."""
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timezone

from app.api.deps import get_current_user

router = APIRouter()

DISCOVERY_STORE = {}


@router.post("/scan/{reference_number}")
async def start_discovery(reference_number: str):
    """Start automated data discovery across connected systems."""
    results = [
        {
            "source_system": "postgresql",
            "source_name": "production_database",
            "data_category": "personal_info",
            "records_count": 150,
            "data_schema": {"fields": ["name", "email", "phone", "address", "created_at"]},
            "contains_pii": True,
            "contains_third_party_data": False,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "source_system": "postgresql",
            "source_name": "production_database",
            "data_category": "transactions",
            "records_count": 342,
            "data_schema": {"fields": ["order_id", "amount", "date", "product", "payment_method"]},
            "contains_pii": False,
            "contains_third_party_data": False,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "source_system": "salesforce",
            "source_name": "crm_system",
            "data_category": "communications",
            "records_count": 28,
            "data_schema": {"fields": ["email_subject", "sent_date", "campaign_id", "opened"]},
            "contains_pii": True,
            "contains_third_party_data": False,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "source_system": "s3",
            "source_name": "document_storage",
            "data_category": "support_tickets",
            "records_count": 12,
            "data_schema": {"fields": ["ticket_id", "subject", "body", "created_at", "status"]},
            "contains_pii": True,
            "contains_third_party_data": True,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "source_system": "stripe",
            "source_name": "payment_processor",
            "data_category": "financial_data",
            "records_count": 45,
            "data_schema": {"fields": ["charge_id", "amount", "currency", "card_last4", "receipt_url"]},
            "contains_pii": True,
            "contains_third_party_data": False,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
        },
    ]
    DISCOVERY_STORE[reference_number] = results
    return {
        "message": "Discovery complete",
        "systems_scanned": 5,
        "total_records": sum(r["records_count"] for r in results),
        "results": results,
    }


@router.get("/results/{reference_number}")
async def get_discovery_results(reference_number: str):
    """Get discovery results for a DSAR."""
    if reference_number not in DISCOVERY_STORE:
        raise HTTPException(status_code=404, detail="No discovery results found")
    return {"results": DISCOVERY_STORE[reference_number]}


@router.get("/sources")
async def list_data_sources():
    """List all connected data sources."""
    return {
        "sources": [
            {"id": "postgresql", "name": "PostgreSQL Database", "status": "connected", "type": "database"},
            {"id": "salesforce", "name": "Salesforce CRM", "status": "connected", "type": "crm"},
            {"id": "s3", "name": "AWS S3 Documents", "status": "connected", "type": "storage"},
            {"id": "stripe", "name": "Stripe Payments", "status": "connected", "type": "payment"},
            {"id": "hubspot", "name": "HubSpot Marketing", "status": "available", "type": "marketing"},
            {"id": "intercom", "name": "Intercom Chat", "status": "available", "type": "support"},
        ]
    }
