"""Scan service — orchestrates scanning and persistence."""
import time
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import Scan, Finding, ScanStatus, Severity
from app.schemas.scan import ScanCreate, DashboardStats
from app.services.sast_engine import SASTScanner, ScanMatch


class ScanService:
    """Service layer for scan operations."""
    
    def __init__(self):
        self.scanner = SASTScanner()
    
    async def create_scan(self, db: AsyncSession, data: ScanCreate) -> Scan:
        """Create a new scan record."""
        scan = Scan(
            repository=data.repository,
            branch=data.branch,
            status=ScanStatus.PENDING,
        )
        db.add(scan)
        await db.flush()
        return scan
    
    async def run_scan(self, db: AsyncSession, scan_id: int, code: Optional[str] = None) -> Scan:
        """Execute a scan and store results."""
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one()
        
        scan.status = ScanStatus.RUNNING
        await db.flush()
        
        start_time = time.time()
        
        try:
            if code:
                # Direct code scan
                matches = self.scanner.scan_code(code)
                scan.total_files = 1
                scan.scanned_files = 1
            else:
                # Directory scan
                matches, files_scanned = self.scanner.scan_directory(scan.repository)
                scan.total_files = files_scanned
                scan.scanned_files = files_scanned
            
            # Store findings
            severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
            
            for match in matches:
                finding = Finding(
                    scan_id=scan.id,
                    file_path=match.file_path,
                    line_number=match.line_number,
                    rule_id=match.rule_id,
                    severity=match.severity,
                    title=match.title,
                    description=match.description,
                    remediation=match.remediation,
                    cwe_id=match.cwe_id,
                    owasp_category=match.owasp_category,
                    code_snippet=match.code_snippet,
                    confidence=match.confidence,
                )
                db.add(finding)
                sev = match.severity.value
                if sev in severity_counts:
                    severity_counts[sev] += 1
            
            # Update scan summary
            scan.critical_count = severity_counts["critical"]
            scan.high_count = severity_counts["high"]
            scan.medium_count = severity_counts["medium"]
            scan.low_count = severity_counts["low"]
            scan.info_count = severity_counts["info"]
            scan.total_findings = len(matches)
            scan.scan_duration_seconds = round(time.time() - start_time, 2)
            scan.completed_at = datetime.utcnow()
            scan.status = ScanStatus.COMPLETED
            
            # Calculate risk score (0-100)
            scan.risk_score = self._calculate_risk_score(matches)
            
        except Exception as e:
            scan.status = ScanStatus.FAILED
            scan.description = str(e) if hasattr(scan, 'description') else None
        
        await db.flush()
        return scan
    
    def _calculate_risk_score(self, matches: List[ScanMatch]) -> float:
        """Calculate overall risk score from 0-100."""
        if not matches:
            return 0.0
        
        weights = {
            Severity.CRITICAL: 10,
            Severity.HIGH: 5,
            Severity.MEDIUM: 2,
            Severity.LOW: 0.5,
            Severity.INFO: 0.1,
        }
        
        total = sum(weights.get(m.severity, 1) for m in matches)
        # Normalize: 50+ weighted findings = score of 100
        score = min(100.0, (total / 50.0) * 100)
        return round(score, 1)
    
    async def get_scan(self, db: AsyncSession, scan_id: int) -> Optional[Scan]:
        """Get a scan by ID."""
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        return result.scalar_one_or_none()
    
    async def list_scans(self, db: AsyncSession, limit: int = 50) -> List[Scan]:
        """List recent scans."""
        result = await db.execute(
            select(Scan).order_by(Scan.created_at.desc()).limit(limit)
        )
        return result.scalars().all()
    
    async def get_findings(self, db: AsyncSession, scan_id: int) -> List[Finding]:
        """Get all findings for a scan."""
        result = await db.execute(
            select(Finding).where(Finding.scan_id == scan_id).order_by(Finding.severity)
        )
        return result.scalars().all()
    
    async def get_dashboard_stats(self, db: AsyncSession) -> DashboardStats:
        """Compute dashboard statistics."""
        # Total scans
        total_result = await db.execute(select(func.count(Scan.id)))
        total_scans = total_result.scalar() or 0
        
        # Total findings by severity
        findings_result = await db.execute(
            select(Finding.severity, func.count(Finding.id)).group_by(Finding.severity)
        )
        severity_counts = {row[0].value: row[1] for row in findings_result.all()}
        
        total_findings = sum(severity_counts.values())
        
        # Average risk score
        risk_result = await db.execute(
            select(func.avg(Scan.risk_score)).where(Scan.status == ScanStatus.COMPLETED)
        )
        avg_risk = risk_result.scalar() or 0.0
        
        # Top rules
        rules_result = await db.execute(
            select(Finding.rule_id, Finding.title, func.count(Finding.id))
            .group_by(Finding.rule_id, Finding.title)
            .order_by(func.count(Finding.id).desc())
            .limit(5)
        )
        top_rules = [
            {"rule_id": row[0], "title": row[1], "count": row[2]}
            for row in rules_result.all()
        ]
        
        # Scans this week
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_result = await db.execute(
            select(func.count(Scan.id)).where(Scan.created_at >= week_ago)
        )
        scans_this_week = week_result.scalar() or 0
        
        return DashboardStats(
            total_scans=total_scans,
            total_findings=total_findings,
            critical_findings=severity_counts.get("critical", 0),
            high_findings=severity_counts.get("high", 0),
            medium_findings=severity_counts.get("medium", 0),
            low_findings=severity_counts.get("low", 0),
            avg_risk_score=round(avg_risk, 1),
            scans_this_week=scans_this_week,
            top_rules=top_rules,
            severity_distribution=severity_counts,
        )
