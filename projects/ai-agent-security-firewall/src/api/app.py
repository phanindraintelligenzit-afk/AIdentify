"""FastAPI application and REST API endpoints."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.services.firewall import FirewallEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("aisf.api")

# Global firewall engine
BASE_DIR = Path(__file__).resolve().parent.parent.parent
firewall: FirewallEngine = None  # initialized in lifespan


@asynccontextmanager
async def lifespan(app: FastAPI):
    global firewall
    config_path = os.path.join(BASE_DIR, "config", "settings.yaml")
    firewall = FirewallEngine(config_path=config_path)
    logger.info(f"Firewall initialized with {len(firewall.rules)} rules")
    yield
    logger.info("Firewall shutting down")


def _ensure_firewall():
    """Ensure firewall is initialized (for testing and direct use)."""
    global firewall
    if firewall is None:
        config_path = os.path.join(BASE_DIR, "config", "settings.yaml")
        firewall = FirewallEngine(config_path=config_path)


app = FastAPI(
    title="AI Agent Security Firewall",
    description="Real-time prompt injection and jailbreak detection middleware",
    version="1.0.0",
    lifespan=lifespan,
)


# --- Request/Response Models ---

class ScanRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000, description="Input text to scan")
    context: str = Field(default="", max_length=1000, description="Optional context")

class ScanResponse(BaseModel):
    is_blocked: bool
    highest_severity: str | None
    detections: list[dict]
    processing_time_ms: float
    message: str

class HealthResponse(BaseModel):
    status: str
    rules_loaded: int
    rules_enabled: int
    version: str

class StatsResponse(BaseModel):
    total_requests: int
    blocked_requests: int
    flagged_requests: int
    allowed_requests: int
    block_rate: float
    attack_type_breakdown: dict
    recent_blocks: list
    uptime_seconds: float


# --- API Endpoints ---

@app.post("/api/v1/scan", response_model=ScanResponse)
async def scan_text(request: ScanRequest):
    """Scan input text for prompt injection, jailbreaks, and other attacks."""
    _ensure_firewall()
    result = firewall.scan(request.text)

    detections = []
    for d in result.detections:
        detections.append({
            "attack_type": d.attack_type.value if d.attack_type else None,
            "confidence": round(d.confidence, 3),
            "severity": d.severity.value if d.severity else None,
            "explanation": d.explanation,
            "matched_rules": d.matched_rules[:5],  # Limit for response size
        })

    message = "Input blocked" if result.is_blocked else (
        "Input flagged for review" if result.highest_severity and result.highest_severity.value == "flag" else
        "Input allowed"
    )

    return ScanResponse(
        is_blocked=result.is_blocked,
        highest_severity=result.highest_severity.value if result.highest_severity else None,
        detections=detections,
        processing_time_ms=result.processing_time_ms,
        message=message,
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    _ensure_firewall()
    return HealthResponse(**firewall.get_health())


@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats():
    """Get firewall statistics."""
    _ensure_firewall()
    return StatsResponse(**firewall.get_stats())


# --- Web Dashboard ---

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the web dashboard."""
    html = get_dashboard_html()
    return HTMLResponse(content=html)


def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agent Security Firewall - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        header { text-align: center; margin-bottom: 2rem; }
        header h1 { font-size: 2rem; color: #38bdf8; margin-bottom: 0.5rem; }
        header p { color: #94a3b8; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .stat-card { background: #1e293b; border-radius: 12px; padding: 1.5rem; border: 1px solid #334155; }
        .stat-card h3 { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
        .stat-card .value { font-size: 2rem; font-weight: 700; }
        .stat-card.blocked .value { color: #f87171; }
        .stat-card.flagged .value { color: #fbbf24; }
        .stat-card.allowed .value { color: #4ade80; }
        .stat-card.total .value { color: #38bdf8; }
        .section { background: #1e293b; border-radius: 12px; padding: 1.5rem; border: 1px solid #334155; margin-bottom: 2rem; }
        .section h2 { font-size: 1.2rem; margin-bottom: 1rem; color: #38bdf8; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #334155; font-size: 0.9rem; }
        th { color: #94a3b8; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; }
        .badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
        .badge-block { background: #7f1d1d; color: #fca5a5; }
        .badge-flag { background: #78350f; color: #fcd34d; }
        .badge-allow { background: #14532d; color: #86efac; }
        .attack-type { color: #c4b5fd; font-family: monospace; font-size: 0.85rem; }
        .confidence { font-family: monospace; }
        .preview { color: #94a3b8; font-size: 0.85rem; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .scan-form { display: flex; gap: 1rem; margin-bottom: 1rem; }
        .scan-form input { flex: 1; padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: #e2e8f0; font-size: 0.9rem; }
        .scan-form input:focus { outline: none; border-color: #38bdf8; }
        .scan-form button { padding: 0.75rem 1.5rem; border-radius: 8px; border: none; background: #38bdf8; color: #0f172a; font-weight: 600; cursor: pointer; }
        .scan-form button:hover { background: #7dd3fc; }
        .scan-result { padding: 1rem; border-radius: 8px; margin-top: 1rem; }
        .scan-result.blocked { background: #7f1d1d; border: 1px solid #dc2626; }
        .scan-result.flagged { background: #78350f; border: 1px solid #f59e0b; }
        .scan-result.allowed { background: #14532d; border: 1px solid #22c55e; }
        .refresh-btn { float: right; padding: 0.4rem 0.8rem; border-radius: 6px; border: 1px solid #334155; background: transparent; color: #94a3b8; cursor: pointer; font-size: 0.8rem; }
        .refresh-btn:hover { border-color: #38bdf8; color: #38bdf8; }
        .empty-state { text-align: center; padding: 2rem; color: #64748b; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ AI Agent Security Firewall</h1>
            <p>Real-time prompt injection &amp; jailbreak detection</p>
        </header>

        <div class="stats-grid" id="stats-grid">
            <div class="stat-card total">
                <h3>Total Requests</h3>
                <div class="value" id="total">-</div>
            </div>
            <div class="stat-card blocked">
                <h3>Blocked</h3>
                <div class="value" id="blocked">-</div>
            </div>
            <div class="stat-card flagged">
                <h3>Flagged</h3>
                <div class="value" id="flagged">-</div>
            </div>
            <div class="stat-card allowed">
                <h3>Allowed</h3>
                <div class="value" id="allowed">-</div>
            </div>
        </div>

        <div class="section">
            <h2>🔍 Test Scan</h2>
            <div class="scan-form">
                <input type="text" id="scan-input" placeholder="Enter text to scan for attacks..." />
                <button onclick="performScan()">Scan</button>
            </div>
            <div id="scan-result"></div>
        </div>

        <div class="section">
            <h2>📊 Attack Breakdown</h2>
            <table>
                <thead><tr><th>Attack Type</th><th>Count</th></tr></thead>
                <tbody id="attack-breakdown">
                    <tr><td colspan="2" class="empty-state">No attacks detected yet</td></tr>
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>🚫 Recent Blocks <button class="refresh-btn" onclick="refreshStats()">Refresh</button></h2>
            <table>
                <thead><tr><th>Time</th><th>Attack Type</th><th>Confidence</th><th>Preview</th></tr></thead>
                <tbody id="recent-blocks">
                    <tr><td colspan="4" class="empty-state">No recent blocks</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        async function refreshStats() {
            try {
                const resp = await fetch('/api/v1/stats');
                const data = await resp.json();
                document.getElementById('total').textContent = data.total_requests;
                document.getElementById('blocked').textContent = data.blocked_requests;
                document.getElementById('flagged').textContent = data.flagged_requests;
                document.getElementById('allowed').textContent = data.allowed_requests;

                // Attack breakdown
                const breakdown = document.getElementById('attack-breakdown');
                const entries = Object.entries(data.attack_type_breakdown);
                if (entries.length === 0) {
                    breakdown.innerHTML = '<tr><td colspan="2" class="empty-state">No attacks detected yet</td></tr>';
                } else {
                    breakdown.innerHTML = entries.map(([type, count]) =>
                        `<tr><td class="attack-type">${type}</td><td>${count}</td></tr>`
                    ).join('');
                }

                // Recent blocks
                const blocks = document.getElementById('recent-blocks');
                if (data.recent_blocks.length === 0) {
                    blocks.innerHTML = '<tr><td colspan="4" class="empty-state">No recent blocks</td></tr>';
                } else {
                    blocks.innerHTML = data.recent_blocks.reverse().map(b => {
                        const time = new Date(b.timestamp * 1000).toLocaleTimeString();
                        const types = b.attack_types.map(t => `<span class="attack-type">${t}</span>`).join(', ');
                        return `<tr><td>${time}</td><td>${types}</td><td class="confidence">${(b.confidence * 100).toFixed(1)}%</td><td class="preview" title="${b.preview}">${b.preview}</td></tr>`;
                    }).join('');
                }
            } catch (e) {
                console.error('Failed to refresh stats:', e);
            }
        }

        async function performScan() {
            const input = document.getElementById('scan-input').value;
            if (!input.trim()) return;

            const resultDiv = document.getElementById('scan-result');
            resultDiv.innerHTML = '<div class="scan-result" style="background:#334155;">Scanning...</div>';

            try {
                const resp = await fetch('/api/v1/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: input })
                });
                const data = await resp.json();

                const statusClass = data.is_blocked ? 'blocked' : (data.highest_severity === 'flag' ? 'flagged' : 'allowed');
                const statusLabel = data.is_blocked ? '🚫 BLOCKED' : (data.highest_severity === 'flag' ? '⚠️ FLAGGED' : '✅ ALLOWED');

                let detectionsHtml = '';
                if (data.detections.length > 0) {
                    detectionsHtml = '<br><br><strong>Detections:</strong><ul>' +
                        data.detections.map(d =>
                            `<li><span class="attack-type">${d.attack_type}</span> (${(d.confidence * 100).toFixed(1)}% confidence) - ${d.explanation}</li>`
                        ).join('') + '</ul>';
                }

                resultDiv.innerHTML = `<div class="scan-result ${statusClass}">
                    <strong>${statusLabel}</strong> (${data.processing_time_ms}ms)
                    ${detectionsHtml}
                </div>`;

                refreshStats();
            } catch (e) {
                resultDiv.innerHTML = `<div class="scan-result blocked"><strong>Error:</strong> ${e.message}</div>`;
            }
        }

        // Auto-refresh every 5 seconds
        refreshStats();
        setInterval(refreshStats, 5000);

        // Enter key triggers scan
        document.getElementById('scan-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') performScan();
        });
    </script>
</body>
</html>"""
