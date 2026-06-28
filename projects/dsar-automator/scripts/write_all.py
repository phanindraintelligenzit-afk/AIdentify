"""Write tests and frontend for DSAR Automator."""
import os

BASE = r"C:\Users\Admin\Projects\AIdentify-marketplace\projects\dsar-automator"

def write(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"OK: {path}")

# === TESTS ===
write("backend/tests/__init__.py", '')
write("backend/tests/conftest.py", '''"""Test fixtures."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
''')

write("backend/tests/test_api.py", '''"""Tests for DSAR API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "dsar-automator"


@pytest.mark.anyio
async def test_create_dsar(client):
    payload = {
        "requester_name": "John Doe",
        "requester_email": "john@example.com",
        "request_type": "access",
        "regulation": "gdpr",
        "description": "I want to know what data you have on me.",
    }
    resp = await client.post("/api/v1/dsar/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["reference_number"].startswith("DSAR-")
    assert data["status"] == "received"
    assert data["days_remaining"] == 30
    assert data["risk_level"] == "low"


@pytest.mark.anyio
async def test_create_dsar_ccpa(client):
    payload = {
        "requester_name": "Jane Smith",
        "requester_email": "jane@example.com",
        "request_type": "erasure",
        "regulation": "ccpa",
        "description": "Delete all my personal data.",
    }
    resp = await client.post("/api/v1/dsar/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["days_remaining"] == 45


@pytest.mark.anyio
async def test_list_dsars(client):
    resp = await client.get("/api/v1/dsar/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.anyio
async def test_get_dsar_not_found(client):
    resp = await client.get("/api/v1/dsar/DSAR-99999999-9999")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_dashboard_stats(client):
    resp = await client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_requests" in data
    assert "pending_requests" in data
    assert "compliance_rate" in data


@pytest.mark.anyio
async def test_discovery_sources(client):
    resp = await client.get("/api/v1/discovery/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert "sources" in data
    assert len(data["sources"]) == 6


@pytest.mark.anyio
async def test_discovery_scan(client):
    resp = await client.post("/api/v1/discovery/scan/DSAR-20260628-0001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["systems_scanned"] == 5
    assert data["total_records"] == 577


@pytest.mark.anyio
async def test_response_package(client):
    payload = {"included_data": ["personal_info", "transactions"], "format": "json"}
    resp = await client.post("/api/v1/responses/DSAR-20260628-0001", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["approved_by"] is None
    assert data["redactions_count"] == 3
''')

write("backend/tests/test_services.py", '''"""Tests for DSAR processing services."""
import pytest
from app.services.dsar_processor import dsar_processor
from app.services.identity_verifier import identity_verifier
from app.services.data_redactor import data_redactor
from datetime import datetime, timezone, timedelta


class TestDSARProcessor:
    def test_calculate_deadline_gdpr(self):
        now = datetime.now(timezone.utc)
        deadline = dsar_processor.calculate_deadline(now, "gdpr")
        delta = deadline - now
        assert delta.days == 30

    def test_calculate_deadline_ccpa(self):
        now = datetime.now(timezone.utc)
        deadline = dsar_processor.calculate_deadline(now, "ccpa")
        delta = deadline - now
        assert delta.days == 45

    def test_calculate_days_remaining(self):
        future = datetime.now(timezone.utc) + timedelta(days=10)
        assert dsar_processor.calculate_days_remaining(future) == 10

    def test_assess_risk_low(self):
        data = {"records_found_count": 10, "data_categories_found": ["personal_info"]}
        assert dsar_processor.assess_risk(data) == "low"

    def test_assess_risk_high_sensitive_data(self):
        data = {
            "records_found_count": 100,
            "data_categories_found": ["health_data", "financial_data"],
            "description": "My lawyer will handle this",
        }
        assert dsar_processor.assess_risk(data) == "high"

    def test_classify_request_type_erasure(self):
        assert dsar_processor.classify_request_type("Please delete all my data") == "erasure"

    def test_classify_request_type_rectification(self):
        assert dsar_processor.classify_request_type("I need to correct my address") == "rectification"

    def test_classify_request_type_portability(self):
        assert dsar_processor.classify_request_type("Export my data as JSON") == "portability"

    def test_classify_request_type_access(self):
        assert dsar_processor.classify_request_type("What info do you have?") == "access"

    def test_should_escalate_close_deadline(self):
        data = {"days_remaining": 2, "status": "reviewing", "risk_level": "low"}
        assert dsar_processor.should_escalate(data) is True

    def test_should_escalate_high_risk(self):
        data = {"days_remaining": 20, "status": "reviewing", "risk_level": "high"}
        assert dsar_processor.should_escalate(data) is True

    def test_should_not_escalate_normal(self):
        data = {"days_remaining": 20, "status": "reviewing", "risk_level": "low"}
        assert dsar_processor.should_escalate(data) is False


class TestIdentityVerifier:
    def test_verify_by_email_match(self):
        result = identity_verifier.verify_by_email("user@example.com", "user@example.com")
        assert result["verified"] is True
        assert result["confidence"] == "high"

    def test_verify_by_email_mismatch(self):
        result = identity_verifier.verify_by_email("other@example.com", "user@example.com")
        assert result["verified"] is False

    def test_verify_by_account(self):
        result = identity_verifier.verify_by_account("acc_123", "user@example.com")
        assert result["verified"] is True

    def test_recommend_method_with_account(self):
        result = identity_verifier.recommend_verification_method({"has_account": True})
        assert result == "account_ownership"

    def test_recommend_method_no_info(self):
        result = identity_verifier.recommend_verification_method({})
        assert result == "document_upload"


class TestDataRedactor:
    def test_redact_email(self):
        text = "Contact john.doe@example.com for info"
        result = data_redactor.redact_pii(text)
        assert "john.doe@example.com" not in result
        assert "[EMAIL REDACTED]" in result

    def test_redact_phone(self):
        text = "Call +1-800-555-1234"
        result = data_redactor.redact_pii(text)
        assert "[PHONE REDACTED]" in result

    def test_redact_ssn(self):
        text = "SSN: 123-45-6789"
        result = data_redactor.redact_pii(text)
        assert "[SSN REDACTED]" in result

    def test_redact_credit_card(self):
        text = "Card: 4111-1111-1111-1111"
        result = data_redactor.redact_pii(text)
        assert "[CARD REDACTED]" in result

    def test_redact_third_party_fields(self):
        records = [{"name": "John", "third_party_name": "Jane", "data": "test"}]
        result = data_redactor.redact_third_party_data(records)
        assert result[0]["third_party_name"] == "[THIRD-PARTY REDACTED]"

    def test_redact_dataset_fields(self):
        records = [{"a": 1, "b": 2, "c": 3}]
        result, count = data_redactor.redact_dataset(records, ["b", "c"])
        assert count == 2
        assert result[0]["b"] == "[REDACTED]"

    def test_redaction_report(self):
        report = data_redactor.generate_redaction_report(10, 3)
        assert report["redacted_fields"] == 3
        assert report["redaction_percentage"] == 30.0
''')

# === FRONTEND ===
write("frontend/package.json", '''{
  "name": "dsar-automator-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.0",
    "recharts": "^2.12.7",
    "lucide-react": "^0.441.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.41",
    "tailwindcss": "^3.4.10",
    "typescript": "^5.5.3",
    "vite": "^5.4.1"
  }
}
''')

write("frontend/vite.config.ts", '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
''')

write("frontend/tsconfig.json", '''{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
''')

write("frontend/tailwind.config.js", '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          50: '#f6f6f7',
          100: '#e2e3e5',
          200: '#c4c5ca',
          300: '#9fa1a9',
          400: '#7b7d87',
          500: '#61636d',
          600: '#4d4e57',
          700: '#3f4047',
          800: '#2d2e33',
          900: '#1a1b1f',
          950: '#0f1012',
        },
        accent: {
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
        },
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444',
      },
    },
  },
  plugins: [],
}
''')

write("frontend/postcss.config.js", '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
''')

write("frontend/index.html", '''<!DOCTYPE html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>DataGuard - DSAR Automator</title>
  </head>
  <body class="bg-dark-950 text-dark-100">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
''')

write("frontend/src/main.tsx", '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
''')

write("frontend/src/index.css", '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
}

body {
  margin: 0;
  min-height: 100vh;
}

@layer utilities {
  .scrollbar-thin::-webkit-scrollbar {
    width: 6px;
  }
  .scrollbar-thin::-webkit-scrollbar-track {
    background: #1a1b1f;
  }
  .scrollbar-thin::-webkit-scrollbar-thumb {
    background: #3f4047;
    border-radius: 3px;
  }
}
''')

write("frontend/src/App.tsx", '''import { useState } from 'react'
import { Shield, LayoutDashboard, FileSearch, Package, Settings, Plus, Bell, Search } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import DSARList from './pages/DSARList'
import CreateDSAR from './pages/CreateDSAR'
import DiscoveryPage from './pages/DiscoveryPage'

type Page = 'dashboard' | 'dsar' | 'create' | 'discovery'

function App() {
  const [page, setPage] = useState<Page>('dashboard')

  const navItems = [
    { id: 'dashboard' as Page, icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'dsar' as Page, icon: FileSearch, label: 'DSAR Requests' },
    { id: 'create' as Page, icon: Plus, label: 'New Request' },
    { id: 'discovery' as Page, icon: Shield, label: 'Data Discovery' },
  ]

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-dark-900 border-r border-dark-700 flex flex-col">
        <div className="p-4 border-b border-dark-700">
          <div className="flex items-center gap-2">
            <Shield className="w-8 h-8 text-accent-500" />
            <div>
              <h1 className="text-lg font-bold text-white">DataGuard</h1>
              <p className="text-xs text-dark-400">DSAR Automator</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setPage(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                page === item.id
                  ? 'bg-accent-600 text-white'
                  : 'text-dark-300 hover:bg-dark-800 hover:text-white'
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </nav>
        <div className="p-3 border-t border-dark-700">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-dark-800">
            <div className="w-8 h-8 rounded-full bg-accent-600 flex items-center justify-center text-white text-sm font-medium">
              DP
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white truncate">DPO Admin</p>
              <p className="text-xs text-dark-400 truncate">dpo@company.com</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <header className="sticky top-0 z-10 bg-dark-900/80 backdrop-blur border-b border-dark-700 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
              <input
                type="text"
                placeholder="Search requests..."
                className="pl-9 pr-4 py-2 bg-dark-800 border border-dark-600 rounded-lg text-sm text-white placeholder-dark-400 focus:outline-none focus:border-accent-500 w-64"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button className="relative p-2 text-dark-300 hover:text-white hover:bg-dark-800 rounded-lg">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-danger rounded-full" />
            </button>
          </div>
        </header>

        <div className="p-6">
          {page === 'dashboard' && <Dashboard />}
          {page === 'dsar' && <DSARList />}
          {page === 'create' && <CreateDSAR />}
          {page === 'discovery' && <DiscoveryPage />}
        </div>
      </main>
    </div>
  )
}

export default App
''')

write("frontend/src/pages/Dashboard.tsx", '''import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { AlertTriangle, CheckCircle, Clock, TrendingUp, Database, Shield } from 'lucide-react'

const timelineData = Array.from({ length: 14 }, (_, i) => ({
  date: `${28 - i}d`,
  received: Math.floor(Math.random() * 5) + 1,
  completed: Math.floor(Math.random() * 4),
}))

const categoryData = [
  { name: 'Personal Info', value: 45, color: '#3b82f6' },
  { name: 'Transactions', value: 38, color: '#22c55e' },
  { name: 'Communications', value: 28, color: '#f59e0b' },
  { name: 'Support', value: 15, color: '#8b5cf6' },
  { name: 'Financial', value: 12, color: '#ef4444' },
  { name: 'Marketing', value: 8, color: '#06b6d4' },
]

const statusData = [
  { name: 'Completed', value: 29, color: '#22c55e' },
  { name: 'Reviewing', value: 8, color: '#f59e0b' },
  { name: 'Discovering', value: 5, color: '#3b82f6' },
  { name: 'Received', value: 3, color: '#8b5cf6' },
  { name: 'Approving', value: 2, color: '#06b6d4' },
]

const upcomingDeadlines = [
  { ref: 'DSAR-20260628-0001', requester: 'Jane Smith', days: 3, risk: 'high' },
  { ref: 'DSAR-20260625-0003', requester: 'John Doe', days: 7, risk: 'medium' },
  { ref: 'DSAR-20260620-0005', requester: 'Alice Brown', days: 12, risk: 'low' },
  { ref: 'DSAR-20260618-0007', requester: 'Bob Wilson', days: 15, risk: 'low' },
]

export default function Dashboard() {
  const stats = [
    { label: 'Total Requests', value: 47, icon: Shield, color: 'text-accent-400', bg: 'bg-accent-500/10' },
    { label: 'Pending', value: 8, icon: Clock, color: 'text-warning', bg: 'bg-warning/10' },
    { label: 'Completed', value: 29, icon: CheckCircle, color: 'text-success', bg: 'bg-success/10' },
    { label: 'Overdue', value: 1, icon: AlertTriangle, color: 'text-danger', bg: 'bg-danger/10' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Dashboard</h2>
        <p className="text-dark-400 mt-1">GDPR/CCPA DSAR compliance overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-dark-900 border border-dark-700 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dark-400">{stat.label}</p>
                <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${stat.bg}`}>
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Compliance Rate Banner */}
      <div className="bg-gradient-to-r from-accent-600/20 to-accent-500/5 border border-accent-500/30 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TrendingUp className="w-6 h-6 text-accent-400" />
          <div>
            <p className="text-white font-medium">Compliance Rate: 97.8%</p>
            <p className="text-sm text-dark-300">Average processing time: 18.5 days (GDPR limit: 30 days)</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-success">5 / 5</p>
          <p className="text-xs text-dark-400">Systems Connected</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-dark-900 border border-dark-700 rounded-xl p-4">
          <h3 className="text-white font-medium mb-4">Request Volume (14 days)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#3f4047" />
              <XAxis dataKey="date" stroke="#7b7d87" fontSize={12} />
              <YAxis stroke="#7b7d87" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1b1f', border: '1px solid #3f4047', borderRadius: '8px' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="received" fill="#3b82f6" radius={[2, 2, 0, 0]} name="Received" />
              <Bar dataKey="completed" fill="#22c55e" radius={[2, 2, 0, 0]} name="Completed" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-dark-900 border border-dark-700 rounded-xl p-4">
          <h3 className="text-white font-medium mb-4">Data Categories Discovered</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={3}
                dataKey="value"
              >
                {categoryData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1b1f', border: '1px solid #3f4047', borderRadius: '8px' }}
                labelStyle={{ color: '#fff' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-3 mt-2 justify-center">
            {categoryData.map((cat) => (
              <div key={cat.name} className="flex items-center gap-1.5 text-xs text-dark-300">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                {cat.name}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Upcoming Deadlines */}
      <div className="bg-dark-900 border border-dark-700 rounded-xl p-4">
        <h3 className="text-white font-medium mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4 text-warning" />
          Upcoming Deadlines
        </h3>
        <div className="space-y-3">
          {upcomingDeadlines.map((item) => (
            <div key={item.ref} className="flex items-center justify-between py-2 border-b border-dark-700 last:border-0">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${
                  item.risk === 'high' ? 'bg-danger' : item.risk === 'medium' ? 'bg-warning' : 'bg-success'
                }`} />
                <div>
                  <p className="text-sm text-white">{item.requester}</p>
                  <p className="text-xs text-dark-400">{item.ref}</p>
                </div>
              </div>
              <div className="text-right">
                <p className={`text-sm font-medium ${
                  item.days <= 5 ? 'text-danger' : item.days <= 10 ? 'text-warning' : 'text-dark-200'
                }`}>
                  {item.days} days remaining
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
''')

write("frontend/src/pages/DSARList.tsx", '''import { useState } from 'react'
import { Search, Filter, ChevronRight, AlertTriangle, CheckCircle, Clock } from 'lucide-react'

const mockDSARs = [
  { id: 'DSAR-20260628-0001', requester: 'Jane Smith', email: 'jane@example.com', type: 'access', regulation: 'GDPR', status: 'reviewing', days: 3, risk: 'high', received: '2026-06-28' },
  { id: 'DSAR-20260625-0003', requester: 'John Doe', email: 'john@example.com', type: 'erasure', regulation: 'CCPA', status: 'discovering', days: 7, risk: 'medium', received: '2026-06-25' },
  { id: 'DSAR-20260620-0005', requester: 'Alice Brown', email: 'alice@example.com', type: 'access', regulation: 'GDPR', status: 'approving', days: 12, risk: 'low', received: '2026-06-20' },
  { id: 'DSAR-20260618-0007', requester: 'Bob Wilson', email: 'bob@example.com', type: 'portability', regulation: 'GDPR', status: 'completed', days: 15, risk: 'low', received: '2026-06-18' },
  { id: 'DSAR-20260615-0009', requester: 'Carol Davis', email: 'carol@example.com', type: 'rectification', regulation: 'CCPA', status: 'received', days: 18, risk: 'low', received: '2026-06-15' },
  { id: 'DSAR-20260612-0011', requester: 'David Lee', email: 'david@example.com', type: 'access', regulation: 'GDPR', status: 'completed', days: 21, risk: 'low', received: '2026-06-12' },
  { id: 'DSAR-20260610-0013', requester: 'Eva Martinez', email: 'eva@example.com', type: 'erasure', regulation: 'GDPR', status: 'completed', days: 23, risk: 'low', received: '2026-06-10' },
  { id: 'DSAR-20260608-0015', requester: 'Frank Chen', email: 'frank@example.com', type: 'access', regulation: 'CCPA', status: 'completed', days: 25, risk: 'low', received: '2026-06-08' },
]

const statusColors: Record<string, string> = {
  received: 'bg-dark-600 text-dark-200',
  discovering: 'bg-accent-600/20 text-accent-400',
  reviewing: 'bg-warning/20 text-warning',
  approving: 'bg-purple-500/20 text-purple-300',
  completed: 'bg-success/20 text-success',
}

const riskColors: Record<string, string> = {
  high: 'text-danger',
  medium: 'text-warning',
  low: 'text-success',
}

export default function DSARList() {
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')

  const filtered = mockDSARs.filter((d) => {
    const matchSearch = d.requester.toLowerCase().includes(search.toLowerCase()) || d.id.toLowerCase().includes(search.toLowerCase())
    const matchStatus = filterStatus === 'all' || d.status === filterStatus
    return matchSearch && matchStatus
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">DSAR Requests</h2>
        <p className="text-dark-400 mt-1">Manage and track all data subject access requests</p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
          <input
            type="text"
            placeholder="Search by name or reference..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-sm text-white placeholder-dark-400 focus:outline-none focus:border-accent-500"
          />
        </div>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-sm text-white focus:outline-none focus:border-accent-500"
        >
          <option value="all">All Status</option>
          <option value="received">Received</option>
          <option value="discovering">Discovering</option>
          <option value="reviewing">Reviewing</option>
          <option value="approving">Approving</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-dark-900 border border-dark-700 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase">Reference</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase">Requester</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase">Type</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase">Status</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase">Risk</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase">Days Left</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase"></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((dsar) => (
              <tr key={dsar.id} className="border-b border-dark-700/50 hover:bg-dark-800/50 transition-colors">
                <td className="px-4 py-3">
                  <p className="text-sm font-mono text-white">{dsar.id}</p>
                  <p className="text-xs text-dark-400">{dsar.received}</p>
                </td>
                <td className="px-4 py-3">
                  <p className="text-sm text-white">{dsar.requester}</p>
                  <p className="text-xs text-dark-400">{dsar.email}</p>
                </td>
                <td className="px-4 py-3">
                  <p className="text-sm text-dark-200 capitalize">{dsar.type}</p>
                  <p className="text-xs text-dark-400">{dsar.regulation}</p>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[dsar.status]}`}>
                    {dsar.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-medium ${riskColors[dsar.risk]}`}>
                    {dsar.risk}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <p className={`text-sm font-medium ${dsar.days <= 5 ? 'text-danger' : dsar.days <= 10 ? 'text-warning' : 'text-dark-200'}`}>
                    {dsar.days}d
                  </p>
                </td>
                <td className="px-4 py-3">
                  <ChevronRight className="w-4 h-4 text-dark-400" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center py-8 text-dark-400">No requests found</div>
        )}
      </div>
    </div>
  )
}
''')

write("frontend/src/pages/CreateDSAR.tsx", '''import { useState } from 'react'
import { ArrowRight, Check } from 'lucide-react'

export default function CreateDSAR() {
  const [step, setStep] = useState(1)
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    type: 'access',
    regulation: 'gdpr',
    description: '',
  })
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = () => {
    setSubmitted(true)
  }

  if (submitted) {
    return (
      <div className="max-w-lg mx-auto mt-12 text-center">
        <div className="w-16 h-16 bg-success/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <Check className="w-8 h-8 text-success" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">DSAR Request Created</h2>
        <p className="text-dark-300 mb-4">
          Reference: <span className="font-mono text-accent-400">DSAR-20260628-0001</span>
        </p>
        <p className="text-sm text-dark-400 mb-6">
          Deadline: 30 days from now (GDPR). The request has been queued for processing.
        </p>
        <button
          onClick={() => { setSubmitted(false); setStep(1); setForm({ name: '', email: '', phone: '', type: 'access', regulation: 'gdpr', description: '' }) }}
          className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-500 transition-colors"
        >
          Create Another Request
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">New DSAR Request</h2>
        <p className="text-dark-400 mt-1">Create a new Data Subject Access Request</p>
      </div>

      {/* Progress */}
      <div className="flex items-center gap-2">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step >= s ? 'bg-accent-600 text-white' : 'bg-dark-700 text-dark-400'
            }`}>
              {s}
            </div>
            {s < 3 && <div className={`w-12 h-0.5 ${step > s ? 'bg-accent-600' : 'bg-dark-700'}`} />}
          </div>
        ))}
        <span className="ml-4 text-sm text-dark-400">
          {step === 1 ? 'Requester Info' : step === 2 ? 'Request Details' : 'Review'}
        </span>
      </div>

      <div className="bg-dark-900 border border-dark-700 rounded-xl p-6">
        {step === 1 && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Requester Information</h3>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Full Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-accent-500"
                placeholder="John Doe"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Email Address *</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-accent-500"
                placeholder="john@example.com"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Phone (optional)</label>
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-accent-500"
                placeholder="+1 234 567 8900"
              />
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Request Details</h3>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Regulation</label>
              <select
                value={form.regulation}
                onChange={(e) => setForm({ ...form, regulation: e.target.value })}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-accent-500"
              >
                <option value="gdpr">GDPR (EU)</option>
                <option value="ccpa">CCPA (California)</option>
                <option value="lgpd">LGPD (Brazil)</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Request Type</label>
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-accent-500"
              >
                <option value="access">Right of Access (Art. 15)</option>
                <option value="erasure">Right to Erasure (Art. 17)</option>
                <option value="rectification">Right to Rectification (Art. 16)</option>
                <option value="portability">Right to Data Portability (Art. 20)</option>
                <option value="objection">Right to Object (Art. 21)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Description</label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={4}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-accent-500 resize-none"
                placeholder="Describe the request details..."
              />
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Review & Confirm</h3>
            <div className="bg-dark-800 rounded-lg p-4 space-y-2">
              <div className="flex justify-between">
                <span className="text-dark-400">Name:</span>
                <span className="text-white">{form.name || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-400">Email:</span>
                <span className="text-white">{form.email || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-400">Regulation:</span>
                <span className="text-white uppercase">{form.regulation}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-400">Type:</span>
                <span className="text-white capitalize">{form.type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-400">Deadline:</span>
                <span className="text-white">{form.regulation === 'gdpr' ? '30 days' : '45 days'}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-between">
        <button
          onClick={() => setStep(Math.max(1, step - 1))}
          className={`px-4 py-2 rounded-lg text-sm ${step === 1 ? 'invisible' : 'bg-dark-700 text-dark-200 hover:bg-dark-600'}`}
        >
          Back
        </button>
        {step < 3 ? (
          <button
            onClick={() => setStep(step + 1)}
            className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-500 text-sm flex items-center gap-2"
          >
            Next <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            className="px-4 py-2 bg-success text-white rounded-lg hover:bg-success/90 text-sm"
          >
            Create Request
          </button>
        )}
      </div>
    </div>
  )
}
''')

write("frontend/src/pages/DiscoveryPage.tsx", '''import { useState } from 'react'
import { Database, Check, X, AlertTriangle, Server, HardDrive, Cloud, CreditCard, MessageSquare, Megaphone } from 'lucide-react'

const dataSources = [
  { id: 'postgresql', name: 'PostgreSQL Database', type: 'database', status: 'connected', records: 492, icon: Database },
  { id: 'salesforce', name: 'Salesforce CRM', type: 'crm', status: 'connected', records: 28, icon: Server },
  { id: 's3', name: 'AWS S3 Documents', type: 'storage', status: 'connected', records: 12, icon: Cloud },
  { id: 'stripe', name: 'Stripe Payments', type: 'payment', status: 'connected', records: 45, icon: CreditCard },
  { id: 'hubspot', name: 'HubSpot Marketing', type: 'marketing', status: 'available', records: 0, icon: Megaphone },
  { id: 'intercom', name: 'Intercom Chat', type: 'support', status: 'available', records: 0, icon: MessageSquare },
]

const discoveryResults = [
  { source: 'PostgreSQL', category: 'Personal Info', records: 150, pii: true, thirdParty: false },
  { source: 'PostgreSQL', category: 'Transactions', records: 342, pii: false, thirdParty: false },
  { source: 'Salesforce', category: 'Communications', records: 28, pii: true, thirdParty: false },
  { source: 'AWS S3', category: 'Support Tickets', records: 12, pii: true, thirdParty: true },
  { source: 'Stripe', category: 'Financial Data', records: 45, pii: true, thirdParty: false },
]

export default function DiscoveryPage() {
  const [scanning, setScanning] = useState(false)
  const [scanned, setScanned] = useState(true)

  const handleScan = () => {
    setScanning(true)
    setScanned(false)
    setTimeout(() => {
      setScanning(false)
      setScanned(true)
    }, 2000)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Data Discovery</h2>
          <p className="text-dark-400 mt-1">Scan connected systems for personal data</p>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-500 text-sm disabled:opacity-50"
        >
          {scanning ? 'Scanning...' : 'Run Discovery Scan'}
        </button>
      </div>

      {/* Data Sources */}
      <div className="bg-dark-900 border border-dark-700 rounded-xl p-4">
        <h3 className="text-white font-medium mb-4">Connected Data Sources</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {dataSources.map((source) => (
            <div key={source.id} className="bg-dark-800 rounded-lg p-3 flex items-center gap-3">
              <div className={`p-2 rounded-lg ${source.status === 'connected' ? 'bg-success/10' : 'bg-dark-700'}`}>
                <source.icon className={`w-5 h-5 ${source.status === 'connected' ? 'text-success' : 'text-dark-400'}`} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate">{source.name}</p>
                <p className="text-xs text-dark-400 capitalize">{source.type}</p>
              </div>
              {source.status === 'connected' ? (
                <Check className="w-4 h-4 text-success" />
              ) : (
                <X className="w-4 h-4 text-dark-500" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Discovery Results */}
      {scanned && (
        <div className="bg-dark-900 border border-dark-700 rounded-xl p-4">
          <h3 className="text-white font-medium mb-4">
            Discovery Results — DSAR-20260628-0001
          </h3>
          <div className="space-y-3">
            {discoveryResults.map((result, i) => (
              <div key={i} className="flex items-center justify-between py-3 border-b border-dark-700 last:border-0">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-accent-500" />
                  <div>
                    <p className="text-sm text-white">{result.category}</p>
                    <p className="text-xs text-dark-400">{result.source}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm text-white">{result.records} records</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {result.pii && (
                      <span className="px-2 py-0.5 bg-warning/20 text-warning text-xs rounded-full">PII</span>
                    )}
                    {result.thirdParty && (
                      <span className="px-2 py-0.5 bg-danger/20 text-danger text-xs rounded-full flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" />
                        3rd Party
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-dark-700 flex items-center justify-between">
            <p className="text-sm text-dark-300">
              Total: <span className="text-white font-medium">577 records</span> across 5 systems
            </p>
            <button className="px-3 py-1.5 bg-accent-600 text-white text-sm rounded-lg hover:bg-accent-500">
              Generate Response Package
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
''')

# CI workflow
os.makedirs('.github/workflows', exist_ok=True)
write(".github/workflows/ci.yml", '''name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          
      - name: Run tests
        run: |
          cd backend
          python -m pytest tests/ -v --noconftest

  docker:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: |
          cd backend
          docker build -t dsar-automator:test .
''')

# .gitignore
write(".gitignore", '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg-info/
dist/
build/
*.egg

# Virtual Environment
.venv/
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local

# Database
*.db
*.sqlite3

# Uploads
uploads/

# Node
node_modules/
dist/

# OS
.DS_Store
Thumbs.db

# Data
data/
''')

# README
write("README.md", '''# DataGuard DSAR Automator

Automate GDPR/CCPA Data Subject Access Request (DSAR) processing with AI-powered data discovery, identity verification, and response generation.

## Problem

Companies receiving Data Subject Access Requests (DSARs) from customers must respond within:
- **GDPR**: 30 days (EU)
- **CCPA**: 45 days (California)

Manual processing costs **$50-200/hour** and takes **2-5 hours per request**. With growing privacy regulations worldwide, DPOs and legal teams are overwhelmed.

## Solution

DataGuard DSAR Automator handles the entire DSAR workflow:

1. **Request Intake** — Auto-classify request type (access, erasure, rectification, portability, objection)
2. **Identity Verification** — Multi-method verification (email, account ownership, document)
3. **Data Discovery** — Scan connected systems (databases, CRMs, file storage, payment processors)
4. **Data Redaction** — Auto-redact third-party PII and sensitive data
5. **Response Generation** — Generate compliant response packages
6. **Deadline Tracking** — Automated reminders and escalation for approaching deadlines

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   React UI  │────▶│  FastAPI API │────▶│  Data Discovery │
│  (Dashboard)│◀────│   (Python)   │◀────│    Service      │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
                    ┌──────▼───────┐     ┌─────────────────┐
                    │  PostgreSQL  │     │  Task Queue     │
                    │  (Database)  │     │  (Redis/Celery) │
                    └──────────────┘     └─────────────────┘
```

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2
- **Frontend**: React 18, TypeScript, Tailwind CSS (dark theme), Recharts
- **Database**: PostgreSQL (SQLite for dev)
- **Task Queue**: Redis + Celery
- **Deployment**: Docker, docker-compose

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional)

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app/main.py
```

API runs at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

UI runs at `http://localhost:5173`

### Docker

```bash
cd backend
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /api/v1/dsar/ | Create DSAR request |
| GET | /api/v1/dsar/ | List DSAR requests |
| GET | /api/v1/dsar/{ref} | Get DSAR details |
| PATCH | /api/v1/dsar/{ref}/status | Update status |
| POST | /api/v1/dsar/{ref}/verify | Verify identity |
| POST | /api/v1/discovery/scan/{ref} | Run data discovery |
| GET | /api/v1/discovery/sources | List data sources |
| POST | /api/v1/responses/{ref} | Create response package |
| POST | /api/v1/responses/{ref}/approve | Approve response |
| GET | /api/v1/dashboard/stats | Dashboard statistics |

## Environment Variables

See `backend/.env.example` for all configuration options.

## Testing

```bash
cd backend
python -m pytest tests/ -v --noconftest
```

## Who Buys This

- **Data Protection Officers (DPOs)** at mid-market SaaS companies
- **Legal/Compliance teams** at companies with EU/CA customers
- **Privacy consultancies** managing DSARs for multiple clients
- **Startups** preparing for SOC2/GDPR compliance audits

## Pricing (SaaS)

- **Starter**: $500/mo — Up to 50 DSARs/month, 3 data sources
- **Growth**: $1,500/mo — Up to 200 DSARs/month, 10 data sources
- **Enterprise**: $3,000/mo — Unlimited DSARs, unlimited sources, SSO

## License

MIT
''')

print("\n=== All project files written ===")
