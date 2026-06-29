"""Tests for the Vendor Risk Assessment Agent."""
import pytest
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from services import (
    calculate_assessment_score,
    calculate_vendor_risk_score,
    score_to_risk_level,
    generate_risk_recommendations,
    CATEGORY_WEIGHTS,
)
from services import (
    get_template,
    get_all_templates,
    process_assessment_responses,
    ASSESSMENT_TEMPLATES,
)


class TestRiskScorer:
    """Test the risk scoring engine."""
    
    def test_score_to_risk_level_low(self):
        assert score_to_risk_level(20) == "low"
        assert score_to_risk_level(0) == "low"
        assert score_to_risk_level(44) == "low"
    
    def test_score_to_risk_level_medium(self):
        assert score_to_risk_level(45) == "medium"
        assert score_to_risk_level(60) == "medium"
        assert score_to_risk_level(74) == "medium"
    
    def test_score_to_risk_level_high(self):
        assert score_to_risk_level(75) == "high"
        assert score_to_risk_level(85) == "high"
        assert score_to_risk_level(100) == "high"
    
    def test_calculate_assessment_score_perfect(self):
        """All 5s = perfect score = 0 risk."""
        responses = {
            "security": {"q1": 5, "q2": 5},
            "compliance": {"q1": 5, "q2": 5},
        }
        score, level = calculate_assessment_score(responses)
        assert score == 0.0
        assert level == "low"
    
    def test_calculate_assessment_score_worst(self):
        """All 1s = worst score = 100 risk."""
        responses = {
            "security": {"q1": 1, "q2": 1},
            "compliance": {"q1": 1, "q2": 1},
        }
        score, level = calculate_assessment_score(responses)
        assert score == 100.0
        assert level == "high"
    
    def test_calculate_assessment_score_mixed(self):
        """Mixed scores produce intermediate risk."""
        responses = {
            "security": {"q1": 3, "q2": 4},
            "compliance": {"q1": 2, "q2": 3},
        }
        score, level = calculate_assessment_score(responses)
        assert 0 < score < 100
        assert level in ("low", "medium", "high")
    
    def test_calculate_assessment_score_empty(self):
        """Empty responses return default medium risk."""
        score, level = calculate_assessment_score({})
        assert score == 50.0
        assert level == "medium"
    
    def test_calculate_assessment_score_none(self):
        """None responses return default medium risk."""
        score, level = calculate_assessment_score(None)
        assert score == 50.0
        assert level == "medium"
    
    def test_calculate_vendor_risk_score_no_findings(self):
        """Vendor with no findings keeps assessment score."""
        score, level = calculate_vendor_risk_score(
            assessment_score=30.0,
            open_findings=[],
            is_critical=False,
        )
        assert score == 30.0
        assert level == "low"
    
    def test_calculate_vendor_risk_score_with_critical_finding(self):
        """Critical finding adds penalty."""
        findings = [{"severity": "critical"}]
        score, level = calculate_vendor_risk_score(
            assessment_score=30.0,
            open_findings=findings,
            is_critical=False,
        )
        assert score == 55.0  # 30 + 25
        assert level == "medium"
    
    def test_calculate_vendor_risk_score_critical_vendor(self):
        """Critical vendor flag adds bonus."""
        score, level = calculate_vendor_risk_score(
            assessment_score=50.0,
            open_findings=[],
            is_critical=True,
        )
        assert score == 60.0  # 50 + 10
        assert level == "medium"
    
    def test_calculate_vendor_risk_score_auto_critical(self):
        """Score >= 90 becomes critical level."""
        findings = [{"severity": "critical"}, {"severity": "critical"}, {"severity": "critical"}]
        score, level = calculate_vendor_risk_score(
            assessment_score=50.0,
            open_findings=findings,
            is_critical=True,
        )
        assert score >= 90
        assert level == "critical"
    
    def test_calculate_vendor_risk_score_capped(self):
        """Score is capped at 100."""
        findings = [{"severity": "critical"}] * 10
        score, level = calculate_vendor_risk_score(
            assessment_score=80.0,
            open_findings=findings,
            is_critical=True,
        )
        assert score <= 100.0


class TestAssessmentService:
    """Test assessment templates and processing."""
    
    def test_get_template_standard(self):
        template = get_template("standard")
        assert "categories" in template
        assert "security" in template["categories"]
        assert "compliance" in template["categories"]
    
    def test_get_template_quick(self):
        template = get_template("quick")
        assert len(template["categories"]) == 3
    
    def test_get_template_critical(self):
        template = get_template("critical")
        assert len(template["categories"]) == 6
    
    def test_get_template_fallback(self):
        """Unknown template falls back to standard."""
        template = get_template("nonexistent")
        assert template == ASSESSMENT_TEMPLATES["standard"]
    
    def test_get_all_templates(self):
        templates = get_all_templates()
        assert len(templates) == 3
        names = [t["name"] for t in templates]
        assert "standard" in names
        assert "quick" in names
        assert "critical" in names
    
    def test_process_assessment_responses(self):
        responses = {
            "security": {"q1": 4, "q2": 5},
            "compliance": {"q1": 3},
        }
        result = process_assessment_responses(responses)
        assert "score" in result
        assert "risk_level" in result
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
    
    def test_process_low_scores_generates_recommendations(self):
        """Low scores should generate recommendations."""
        responses = {
            "security": {"q1": 1, "q2": 2},
        }
        result = process_assessment_responses(responses)
        assert len(result["recommendations"]) > 0
        assert result["recommendations"][0]["category"] == "security"
    
    def test_process_high_scores_no_recommendations(self):
        """High scores should not generate recommendations."""
        responses = {
            "security": {"q1": 5, "q2": 5},
        }
        result = process_assessment_responses(responses)
        assert len(result["recommendations"]) == 0


class TestFastAPIEndpoints:
    """Test FastAPI endpoints using TestClient."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset state before each test."""
        from api.vendors import VENDORS, FINDINGS
        from api.assessments import ASSESSMENTS
        VENDORS.clear()
        FINDINGS.clear()
        ASSESSMENTS.clear()
    
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        response = client.get("/api/dashboard/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()
    
    def test_create_vendor(self, client):
        response = client.post("/api/vendors", json={
            "name": "Test Vendor Inc",
            "domain": "testvendor.com",
            "category": "cloud",
            "contact_email": "security@testvendor.com",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Vendor Inc"
        assert data["risk_level"] == "medium"
        assert data["risk_score"] == 50.0
    
    def test_list_vendors(self, client):
        # Create a vendor first
        client.post("/api/vendors", json={"name": "Vendor A"})
        response = client.get("/api/vendors")
        assert response.status_code == 200
        assert len(response.json()) >= 1
    
    def test_get_vendor(self, client):
        create_resp = client.post("/api/vendors", json={"name": "Vendor B"})
        vendor_id = create_resp.json()["id"]
        response = client.get(f"/api/vendors/{vendor_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Vendor B"
    
    def test_get_vendor_not_found(self, client):
        response = client.get("/api/vendors/nonexistent-id")
        assert response.status_code == 404
    
    def test_update_vendor(self, client):
        create_resp = client.post("/api/vendors", json={"name": "Vendor C"})
        vendor_id = create_resp.json()["id"]
        response = client.patch(f"/api/vendors/{vendor_id}", json={
            "risk_level": "high",
            "risk_score": 80.0,
        })
        assert response.status_code == 200
        assert response.json()["risk_level"] == "high"
        assert response.json()["risk_score"] == 80.0
    
    def test_delete_vendor(self, client):
        create_resp = client.post("/api/vendors", json={"name": "Vendor D"})
        vendor_id = create_resp.json()["id"]
        response = client.delete(f"/api/vendors/{vendor_id}")
        assert response.status_code == 204
        # Verify deleted
        get_resp = client.get(f"/api/vendors/{vendor_id}")
        assert get_resp.status_code == 404
    
    def test_create_assessment(self, client):
        create_resp = client.post("/api/vendors", json={"name": "Vendor E"})
        vendor_id = create_resp.json()["id"]
        response = client.post("/api/assessments", json={
            "vendor_id": vendor_id,
            "template": "standard",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["vendor_id"] == vendor_id
        assert data["status"] == "pending"
    
    def test_list_templates(self, client):
        response = client.get("/api/assessments/templates")
        assert response.status_code == 200
        assert len(response.json()) == 3
    
    def test_get_template_detail(self, client):
        response = client.get("/api/assessments/templates/standard")
        assert response.status_code == 200
        assert "categories" in response.json()
    
    def test_dashboard_stats(self, client):
        # Create some data
        client.post("/api/vendors", json={"name": "V1", "is_critical": True})
        client.post("/api/vendors", json={"name": "V2"})
        
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_vendors"] >= 2
        assert data["critical_vendors"] >= 1
    
    def test_create_finding(self, client):
        create_resp = client.post("/api/vendors", json={"name": "Vendor F"})
        vendor_id = create_resp.json()["id"]
        response = client.post(f"/api/vendors/{vendor_id}/findings", json={
            "category": "security",
            "severity": "high",
            "title": "No SOC 2 certification",
            "description": "Vendor lacks SOC 2 Type II certification",
            "recommendation": "Request SOC 2 report or consider alternative vendor",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["severity"] == "high"
        assert data["title"] == "No SOC 2 certification"
    
    def test_full_assessment_workflow(self, client):
        """Test complete workflow: vendor → assessment → submit → verify score update."""
        # 1. Create vendor
        v_resp = client.post("/api/vendors", json={
            "name": "Acme Cloud",
            "category": "infrastructure",
            "is_critical": True,
        })
        vendor_id = v_resp.json()["id"]
        
        # 2. Create assessment
        a_resp = client.post("/api/assessments", json={
            "vendor_id": vendor_id,
            "template": "quick",
        })
        assessment_id = a_resp.json()["id"]
        
        # 3. Send assessment
        client.post(f"/api/assessments/{assessment_id}/send")
        
        # 4. Submit responses (poor scores = high risk)
        submit_resp = client.post(f"/api/assessments/{assessment_id}/submit", json={
            "responses": {
                "security": {"q1": 2, "q2": 1},
                "compliance": {"q1": 3},
                "financial": {"q1": 2},
            }
        })
        assert submit_resp.status_code == 200
        assert submit_resp.json()["status"] == "completed"
        assert submit_resp.json()["score"] > 50  # High risk from poor responses
        
        # 5. Verify vendor risk was updated
        v_get = client.get(f"/api/vendors/{vendor_id}")
        assert v_get.json()["risk_score"] > 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
