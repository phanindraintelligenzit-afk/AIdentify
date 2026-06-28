import structlog
from celery import shared_task
from datetime import datetime
from uuid import UUID
from typing import Dict, Any, List
import json
import os

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.contract import Contract, ContractStatus, ProcessingJob
from app.services.parser import ContractParser
from app.services.analyzer import ContractAnalyzer
from app.services.playbook import PlaybookEngine
from app.services.redline import RedlineGenerator

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_contract(self, contract_id: str, playbook_name: str = None):
    """Process a single contract through the analysis pipeline"""
    db = SessionLocal()
    try:
        contract = db.query(Contract).filter(Contract.id == UUID(contract_id)).first()
        if not contract:
            logger.error("contract_not_found", contract_id=contract_id)
            return {"error": "Contract not found"}
        
        # Update status to processing
        contract.status = ContractStatus.PROCESSING
        db.commit()
        
        # Create/update processing job
        job = db.query(ProcessingJob).filter(ProcessingJob.contract_id == contract.id).first()
        if not job:
            job = ProcessingJob(contract_id=contract.id, task_id=self.request.id)
            db.add(job)
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.progress = 10
        job.current_step = "extracting_text"
        db.commit()
        
        # Step 1: Extract text from file
        logger.info("extracting_text", contract_id=contract_id)
        file_path = contract.file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Contract file not found: {file_path}")
        
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        
        # Extract text
        parser = ContractParser()
        if contract.content_type == "application/pdf":
            text = parser.parse_pdf(file_bytes)
        elif contract.content_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword"
        ]:
            text = parser.parse_docx(file_bytes)
        else:
            text = file_bytes.decode("utf-8", errors="ignore")
        
        contract.extracted_text = text
        db.commit()
        
        # Update progress
        job.progress = 30
        job.current_step = "extracting_clauses"
        db.commit()
        
        # Step 2: Extract clauses
        logger.info("extracting_clauses", contract_id=contract_id)
        extractor = ClauseExtractor()
        clauses = extractor.extract_clauses(text)
        
        # Update progress
        job.progress = 50
        job.current_step = "analyzing_clauses"
        db.commit()
        
        # Step 3: Analyze against playbook
        logger.info("analyzing_clauses", contract_id=contract_id, clause_count=len(clauses))
        playbook_engine = PlaybookEngine()
        
        if playbook_name:
            playbook = playbook_engine.get_playbook(playbook_name)
        else:
            playbook = playbook_engine.get_default_playbook(contract.contract_type.value)
        
        analyzer = ContractAnalyzer(playbook_engine=playbook_engine)
        analysis_results, risk_summary = analyzer.analyze(
            text,
            contract_type=contract.contract_type.value,
            playbook_name=playbook.name if playbook else None
        )
        
        # Convert results to serializable format
        clause_analysis = []
        for result in analysis_results:
            clause_analysis.append({
                "clause_name": result.clause_name,
                "clause_text": result.clause_text,
                "risk_level": result.risk_level.value,
                "issues": result.issues,
                "matched_rules": result.matched_rules,
                "redline_suggestion": result.redline_suggestion,
                "explanation": result.explanation,
                "confidence": result.confidence,
            })
        
        contract.clause_analysis = clause_analysis
        contract.risk_summary = {
            "total_clauses": risk_summary.total_clauses,
            "high_risk": risk_summary.high_risk,
            "medium_risk": risk_summary.medium_risk,
            "low_risk": risk_summary.low_risk,
            "approved": risk_summary.approved,
            "overall_risk_score": risk_summary.overall_risk_score,
            "risk_breakdown": risk_summary.risk_breakdown,
        }
        
        db.commit()
        
        # Update progress
        job.progress = 70
        job.current_step = "generating_redline"
        db.commit()
        
        # Step 4: Generate redline document
        logger.info("generating_redline", contract_id=contract_id)
        redline_gen = RedlineGenerator()
        
        # Generate redline DOCX
        redline_docx_path = file_path.replace(".pdf", "_redline.docx").replace(".docx", "_redline.docx")
        redline_gen.generate_summary_docx(
            analysis_results=analysis_results,
            risk_summary=risk_summary,
            contract_info={
                "filename": contract.original_filename,
                "contract_type": contract.contract_type.value,
                "analysis_date": datetime.utcnow().isoformat(),
            },
            output_path=redline_docx_path
        )
        
        contract.redline_docx_path = redline_docx_path
        db.commit()
        
        # Update progress
        job.progress = 90
        job.current_step = "finalizing"
        db.commit()
        
        # Step 5: Complete
        contract.status = ContractStatus.COMPLETED
        contract.completed_at = datetime.utcnow()
        contract.processing_time_seconds = int((datetime.utcnow() - job.started_at).total_seconds())
        
        job.status = "completed"
        job.progress = 100
        job.current_step = "completed"
        job.completed_at = datetime.utcnow()
        job.result = contract.risk_summary
        
        db.commit()
        
        logger.info("contract_processing_completed", contract_id=contract_id)
        
        return {
            "contract_id": contract_id,
            "status": "completed",
            "risk_summary": contract.risk_summary,
            "redline_docx_path": redline_docx_path,
        }
        
    except Exception as exc:
        logger.error("contract_processing_failed", contract_id=contract_id, error=str(exc))
        
        # Update contract status
        contract = db.query(Contract).filter(Contract.id == UUID(contract_id)).first()
        if contract:
            contract.status = ContractStatus.FAILED
            contract.error_message = str(exc)
            db.commit()
        
        # Update job
        job = db.query(ProcessingJob).filter(ProcessingJob.contract_id == UUID(contract_id)).first()
        if job:
            job.status = "failed"
            job.error = str(exc)
            job.completed_at = datetime.utcnow()
            db.commit()
        
        # Retry on transient errors
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {"error": str(exc), "contract_id": contract_id}
        
    finally:
        db.close()


@celery_app.task(bind=True)
def batch_process(self, contract_ids: List[str], playbook_name: str = None):
    """Process multiple contracts in batch"""
    results = []
    for contract_id in contract_ids:
        result = process_contract.delay(contract_id, playbook_name)
        results.append({
            "contract_id": contract_id,
            "task_id": result.id,
        })
    return {"batch_id": self.request.id, "contracts": results}


# Health check task
@celery_app.task
def health_check():
    return {"status": "healthy", "worker": "contract_review_worker"}