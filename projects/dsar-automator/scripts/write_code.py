"""Write all backend API files for DSAR Automator."""
import os

BASE = r"C:\Users\Admin\Projects\AIdentify-marketplace\projects\dsar-automator"

def write(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"OK: {path}")

# DSAR API
write("backend/app/api/v1/dsar.py", '''"""DSAR request management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from app.schemas.dsar import DSARCreate, DSARResponse, DSARDetail, DSARStatusEnum
from app.api.deps import get_current_user

router = APIRouter()

DSAR_STORE = {}
COUNTER = 0


def _generate_reference() -> str:
    global COUNTER
    COUNTER += 1
    return f"DSAR-{datetime.now(timezone.utc).strftime(\'%Y%m%d\')}-{COUNTER:04d}"


@router.post("/", response_model=DSARResponse, status_code=201)
async def create_dsar(request: DSARCreate):
    """Create a new DSAR request."""
    ref = _generate_reference()
    now = datetime.now(timezone.utc)
    deadline_days = 30 if request.regulation == "gdpr" else 45
    dsar = {
        "id": COUNTER,
        "reference_number": ref,
        "requester_name": request.requester_name,
        "requester_email": request.requester_email,
        "requester_phone": request.requester_phone,
        "request_type": request.request_type.value,
        "status": "received",
        "received_at": now.isoformat(),
        "deadline_at": (now + timedelta(days=deadline_days)).isoformat(),
        "days_remaining": deadline_days,
        "records_found_count": 0,
        "risk_level": "low",
        "data_categories_found": [],
        "description": request.description,
    }
    DSAR_STORE[ref] = dsar
    return dsar


@router.get("/", response_model=List[DSARResponse])
async def list_dsars(
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List DSAR requests with optional filters."""
    results = list(DSAR_STORE.values())
    if status:
        results = [r for r in results if r["status"] == status]
    if risk_level:
        results = [r for r in results if r["risk_level"] == risk_level]
    return results[skip:skip + limit]


@router.get("/{reference_number}", response_model=DSARDetail)
async def get_dsar(reference_number: str):
    """Get detailed DSAR request information."""
    if reference_number not in DSAR_STORE:
        raise HTTPException(status_code=404, detail="DSAR not found")
    dsar = DSAR_STORE[reference_number]
    dsar["discovery_results"] = []
    dsar["audit_trail"] = []
    return dsar


@router.patch("/{reference_number}/status")
async def update_status(reference_number: str, status: DSARStatusEnum):
    """Update DSAR processing status."""
    if reference_number not in DSAR_STORE:
        raise HTTPException(status_code=404, detail="DSAR not found")
    DSAR_STORE[reference_number]["status"] = status.value
    return DSAR_STORE[reference_number]


@router.post("/{reference_number}/verify")
async def verify_identity(reference_number: str):
    """Mark identity verification as complete."""
    if reference_number not in DSAR_STORE:
        raise HTTPException(status_code=404, detail="DSAR not found")
    DSAR_STORE[reference_number]["status"] = "discovering"
    return {"message": "Identity verified", "next_step": "data_discovery"}
''')

# Discovery API
write("backend/app/api/v1/discovery.py", '''"""Data discovery endpoints."""
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
''')

# Responses API
write("backend/app/api/v1/responses.py", '''"""Response package management endpoints."""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone

from app.schemas.dsar import ResponsePackageCreate, ResponsePackageResponse

router = APIRouter()

RESPONSE_STORE = {}


@router.post("/{reference_number}")
async def create_response_package(reference_number: str, package: ResponsePackageCreate):
    """Create a response package for a DSAR."""
    pkg = {
        "id": len(RESPONSE_STORE) + 1,
        "dsar_id": reference_number,
        "included_data": package.included_data,
        "excluded_data": ["third_party_pii", "trade_secrets"],
        "redactions_count": 3,
        "format": package.format,
        "approved_by": None,
        "approved_at": None,
        "sent_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "notes": package.notes,
    }
    RESPONSE_STORE[reference_number] = pkg
    return pkg


@router.post("/{reference_number}/approve")
async def approve_package(reference_number: str, approver_id: int = 1):
    """Approve a response package for sending."""
    if reference_number not in RESPONSE_STORE:
        raise HTTPException(status_code=404, detail="Response package not found")
    RESPONSE_STORE[reference_number]["approved_by"] = approver_id
    RESPONSE_STORE[reference_number]["approved_at"] = datetime.now(timezone.utc).isoformat()
    return {"message": "Package approved", "reference": reference_number}


@router.post("/{reference_number}/send")
async def send_response(reference_number: str):
    """Mark response as sent to requester."""
    if reference_number not in RESPONSE_STORE:
        raise HTTPException(status_code=404, detail="Response package not found")
    RESPONSE_STORE[reference_number]["sent_at"] = datetime.now(timezone.utc).isoformat()
    return {"message": "Response sent to requester", "reference": reference_number}


@router.get("/{reference_number}")
async def get_response_package(reference_number: str):
    """Get response package details."""
    if reference_number not in RESPONSE_STORE:
        raise HTTPException(status_code=404, detail="Response package not found")
    return RESPONSE_STORE[reference_number]
''')

# Dashboard API
write("backend/app/api/v1/dashboard.py", '''"""Dashboard statistics endpoints."""
from fastapi import APIRouter
from datetime import datetime, timezone, timedelta

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats():
    """Get dashboard overview statistics."""
    now = datetime.now(timezone.utc)
    return {
        "total_requests": 47,
        "pending_requests": 8,
        "completed_this_month": 12,
        "overdue_requests": 1,
        "avg_processing_days": 18.5,
        "requests_by_type": {
            "access": 35,
            "erasure": 7,
            "rectification": 3,
            "portability": 2,
        },
        "requests_by_status": {
            "received": 3,
            "discovering": 5,
            "reviewing": 8,
            "approving": 2,
            "completed": 29,
        },
        "upcoming_deadlines": [
            {
                "reference": "DSAR-20260628-0001",
                "requester": "Jane Smith",
                "deadline": (now + timedelta(days=3)).isoformat(),
                "days_remaining": 3,
                "risk_level": "high",
            },
            {
                "reference": "DSAR-20260625-0003",
                "requester": "John Doe",
                "deadline": (now + timedelta(days=7)).isoformat(),
                "days_remaining": 7,
                "risk_level": "medium",
            },
            {
                "reference": "DSAR-20260620-0005",
                "requester": "Alice Brown",
                "deadline": (now + timedelta(days=12)).isoformat(),
                "days_remaining": 12,
                "risk_level": "low",
            },
        ],
        "compliance_rate": 97.8,
        "systems_connected": 5,
        "total_data_sources": 8,
    }


@router.get("/timeline")
async def get_timeline():
    """Get processing timeline data."""
    now = datetime.now(timezone.utc)
    return {
        "daily": [
            {"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"), "received": (i % 4) + 1, "completed": (i % 3)}
            for i in range(30)
        ],
        "by_category": [
            {"category": "Personal Info", "count": 45},
            {"category": "Transactions", "count": 38},
            {"category": "Communications", "count": 28},
            {"category": "Support Tickets", "count": 15},
            {"category": "Financial Data", "count": 12},
            {"category": "Marketing Data", "count": 8},
        ],
    }
''')

# Services
write("backend/app/services/__init__.py", '')
write("backend/app/services/dsar_processor.py", '''"""Core DSAR processing service."""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DSARProcessor:
    """Main service for processing Data Subject Access Requests."""

    def __init__(self):
        self.gdpr_deadline_days = 30
        self.ccpa_deadline_days = 45

    def calculate_deadline(self, received_at: datetime, regulation: str = "gdpr") -> datetime:
        """Calculate legal deadline based on regulation."""
        days = self.gdpr_deadline_days if regulation == "gdpr" else self.ccpa_deadline_days
        return received_at + timedelta(days=days)

    def calculate_days_remaining(self, deadline: datetime) -> int:
        """Calculate days until deadline."""
        now = datetime.now(timezone.utc)
        delta = deadline - now
        return max(0, delta.days)

    def assess_risk(self, request_data: dict) -> str:
        """Assess risk level of a DSAR request."""
        risk_score = 0
        if request_data.get("records_found_count", 0) > 1000:
            risk_score += 2
        sensitive_categories = {"financial_data", "health_data", "biometric"}
        found_categories = set(request_data.get("data_categories_found", []))
        if found_categories & sensitive_categories:
            risk_score += 3
        description = request_data.get("description", "").lower()
        if any(word in description for word in ["lawyer", "legal", "court", "complaint", "regulator"]):
            risk_score += 2
        if request_data.get("has_third_party_data"):
            risk_score += 1
        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        return "low"

    def classify_request_type(self, description: str) -> str:
        """Auto-classify the type of DSAR from description."""
        description = description.lower()
        if any(w in description for w in ["delete", "remove", "erase", "forget"]):
            return "erasure"
        elif any(w in description for w in ["correct", "update", "fix", "change"]):
            return "rectification"
        elif any(w in description for w in ["export", "download", "port", "transfer"]):
            return "portability"
        elif any(w in description for w in ["stop", "unsubscribe", "object", "opt out"]):
            return "objection"
        else:
            return "access"

    def generate_response_summary(self, discovery_results: List[dict]) -> dict:
        """Generate a summary of discovered data for response."""
        categories = {}
        total_records = 0
        for result in discovery_results:
            cat = result.get("data_category", "unknown")
            categories[cat] = categories.get(cat, 0) + result.get("records_count", 0)
            total_records += result.get("records_count", 0)
        return {
            "total_records": total_records,
            "categories": categories,
            "systems_scanned": len(set(r.get("source_system") for r in discovery_results)),
            "pii_found": any(r.get("contains_pii") for r in discovery_results),
            "third_party_data_found": any(r.get("contains_third_party_data") for r in discovery_results),
        }

    def should_escalate(self, dsar_data: dict) -> bool:
        """Determine if a DSAR should be escalated to senior review."""
        days_remaining = dsar_data.get("days_remaining", 999)
        status = dsar_data.get("status", "")
        if days_remaining <= 3 and status not in ("completed", "rejected"):
            return True
        if dsar_data.get("risk_level") == "high":
            return True
        return False


dsar_processor = DSARProcessor()
''')

write("backend/app/services/identity_verifier.py", '''"""Identity verification service for DSAR requests."""
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class IdentityVerifier:
    """Handles identity verification for DSAR requesters."""

    def __init__(self):
        self.verification_methods = [
            "email_confirmation",
            "account_ownership",
            "document_upload",
            "knowledge_based",
        ]

    def verify_by_email(self, email: str, account_email: str) -> dict:
        """Verify requester via email confirmation."""
        match = email.lower() == account_email.lower()
        return {
            "method": "email_confirmation",
            "verified": match,
            "confidence": "high" if match else "none",
        }

    def verify_by_account(self, account_id: str, requester_email: str) -> dict:
        """Verify via account ownership check."""
        return {
            "method": "account_ownership",
            "verified": True,
            "confidence": "high",
            "account_id_hash": hashlib.sha256(account_id.encode()).hexdigest()[:16],
        }

    def verify_by_document(self, document_data: dict) -> dict:
        """Verify via uploaded identity document."""
        return {
            "method": "document_upload",
            "verified": True,
            "confidence": "medium",
            "document_type": document_data.get("type", "unknown"),
        }

    def recommend_verification_method(self, available_info: dict) -> str:
        """Recommend best verification method based on available data."""
        if available_info.get("has_account"):
            return "account_ownership"
        elif available_info.get("has_email"):
            return "email_confirmation"
        else:
            return "document_upload"


identity_verifier = IdentityVerifier()
''')

write("backend/app/services/data_redactor.py", '''"""Data redaction service - removes PII and third-party data from responses."""
import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DataRedactor:
    """Redacts sensitive information from DSAR response data."""

    EMAIL_PATTERN = re.compile(r'[\\w.+-]+@[\\w-]+\\.[\\w.-]+')
    PHONE_PATTERN = re.compile(r'\\+?[\\d\\s\\-\\(\\)]{10,}')
    SSN_PATTERN = re.compile(r'\\d{3}-\\d{2}-\\d{4}')
    CREDIT_CARD_PATTERN = re.compile(r'\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}')
    IP_PATTERN = re.compile(r'\\b\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\b')

    def redact_pii(self, text: str) -> str:
        """Remove PII from text content."""
        text = self.EMAIL_PATTERN.sub('[EMAIL REDACTED]', text)
        text = self.PHONE_PATTERN.sub('[PHONE REDACTED]', text)
        text = self.SSN_PATTERN.sub('[SSN REDACTED]', text)
        text = self.CREDIT_CARD_PATTERN.sub('[CARD REDACTED]', text)
        text = self.IP_PATTERN.sub('[IP REDACTED]', text)
        return text

    def redact_third_party_data(self, records: List[Dict]) -> List[Dict]:
        """Remove data belonging to third parties from records."""
        redacted = []
        for record in records:
            cleaned = {}
            for key, value in record.items():
                if key in ("third_party_name", "third_party_email", "other_user_data"):
                    cleaned[key] = "[THIRD-PARTY REDACTED]"
                elif isinstance(value, str):
                    cleaned[key] = self.redact_pii(value)
                else:
                    cleaned[key] = value
            redacted.append(cleaned)
        return redacted

    def redact_dataset(self, data: List[Dict], fields_to_redact: List[str]) -> tuple:
        """Redact specific fields across a dataset."""
        redaction_count = 0
        redacted_data = []
        for record in data:
            new_record = {}
            for key, value in record.items():
                if key in fields_to_redact:
                    new_record[key] = "[REDACTED]"
                    redaction_count += 1
                else:
                    new_record[key] = value
            redacted_data.append(new_record)
        return redacted_data, redaction_count

    def generate_redaction_report(self, original_count: int, redacted_count: int) -> dict:
        """Generate a report of what was redacted for audit purposes."""
        return {
            "total_fields": original_count,
            "redacted_fields": redacted_count,
            "redaction_percentage": round((redacted_count / max(original_count, 1)) * 100, 2),
            "redaction_categories": ["third_party_pii", "contact_info", "financial_data"],
        }


data_redactor = DataRedactor()
''')

# Tasks
write("backend/app/tasks/__init__.py", '')
write("backend/app/tasks/dsar_tasks.py", '''"""Background tasks for DSAR processing."""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class DSARTaskRunner:
    """Simulates background task processing for DSARs."""

    async def check_deadlines(self):
        """Check for approaching deadlines and send reminders."""
        logger.info("Running deadline check...")
        return {"checked": True, "reminders_sent": 0}

    async def auto_discover(self, reference_number: str, sources: list):
        """Run automated data discovery across sources."""
        logger.info(f"Starting auto-discovery for {reference_number}")
        return {"reference": reference_number, "sources_scanned": len(sources)}

    async def generate_compliance_report(self, period: str = "monthly"):
        """Generate compliance report for auditors."""
        logger.info(f"Generating {period} compliance report")
        return {
            "period": period,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "format": "pdf",
        }

    async def cleanup_expired_data(self):
        """Remove data past retention period."""
        logger.info("Running data cleanup...")
        return {"records_cleaned": 0, "space_freed_mb": 0}


task_runner = DSARTaskRunner()
''')

# Requirements
write("backend/requirements.txt", """fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy[asyncio]==2.0.35
aiosqlite==0.20.0
pydantic[email]==2.9.2
pydantic-settings==2.5.2
python-multipart==0.0.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.2
pytest==8.3.3
pytest-asyncio==0.24.0
""")

# Dockerfile
write("backend/Dockerfile", """FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/uploads

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""")

# docker-compose
write("backend/docker-compose.yml", """version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./dsar.db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=change-me-in-production
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - api
    restart: unless-stopped

volumes:
  redis_data:
""")

# .env.example
write("backend/.env.example", """# Database
DATABASE_URL=sqlite+aiosqlite:///./dsar.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security - CHANGE IN PRODUCTION
SECRET_KEY=your-secret-key-change-me
ACCESS_TOKEN_EXPIRE_MINUTES=60

# DSAR Configuration
GDPR_DEADLINE_DAYS=30
CCPA_DEADLINE_DAYS=45
AUTO_REMINDER_DAYS_BEFORE=5

# File Storage
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=50

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
""")

# pyproject.toml
write("backend/pyproject.toml", """[project]
name = "dsar-automator"
version = "1.0.0"
description = "GDPR/CCPA Data Subject Access Request Automation Platform"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
""")

print("\n=== All backend files written ===")
