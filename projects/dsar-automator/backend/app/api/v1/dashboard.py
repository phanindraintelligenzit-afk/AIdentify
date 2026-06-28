"""Dashboard statistics endpoints."""
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
