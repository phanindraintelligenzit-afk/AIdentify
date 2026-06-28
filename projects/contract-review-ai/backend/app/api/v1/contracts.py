from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
import shutil
from datetime import datetime

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.contract import Contract, ContractStatus, Playbook, ClauseRule
from app.schemas.contract import (
    ContractCreate, ContractUpdate, ContractResponse, ContractWithDetails,
    UploadResponse, ContractAnalysisResponse, PlaybookCreate, PlaybookUpdate,
    PlaybookResponse, PlaybookWithRules, ClauseRuleCreate, ClauseRuleUpdate,
    ClauseRuleResponse, HealthResponse
)
from app.tasks.contract_tasks import process_contract_task
from app.core.config import settings
import structlog

logger = structlog.get_logger()

router = APIRouter()


# ==================== Health Check ====================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        database="connected",
        redis="connected"
    )


# ==================== Contract Upload & Processing ====================

@router.post("/contracts/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    contract_type: str = Form("nda"),
    playbook_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a contract for analysis"""
    
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, DOCX"
        )
    
    # Validate file size (max 50MB)
    max_size = 50 * 1024 * 1024
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(status_code=400, detail="File too large. Max 50MB.")
    
    # Save file
    upload_dir = settings.UPLOAD_DIR / str(current_user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_id = uuid.uuid4()
    file_ext = os.path.splitext(file.filename)[1].lower()
    saved_filename = f"{file_id}{file_ext}"
    file_path = upload_dir / saved_filename
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Create contract record
    contract = Contract(
        filename=saved_filename,
        original_filename=file.filename,
        file_size=len(file_content),
        content_type=file.content_type,
        contract_type=contract_type,
        playbook_id=uuid.UUID(playbook_id) if playbook_id else None,
        status=ContractStatus.UPLOADED,
        owner_id=current_user.id,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    
    # Queue processing task
    task = process_contract_task.delay(
        contract_id=str(contract.id),
        file_path=str(file_path),
        contract_type=contract_type,
        playbook_id=playbook_id
    )
    
    logger.info("contract_uploaded", contract_id=str(contract.id), filename=file.filename, user_id=str(current_user.id))
    
    return UploadResponse(
        contract_id=contract.id,
        job_id=task.id,
        message="Contract uploaded successfully. Processing started.",
        status=ContractStatus.UPLOADED
    )


@router.get("/contracts", response_model=List[ContractResponse])
async def list_contracts(
    skip: int = 0,
    limit: int = 50,
    status: Optional[ContractStatus] = None,
    contract_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's contracts"""
    query = db.query(Contract).filter(Contract.owner_id == current_user.id)
    
    if status:
        query = query.filter(Contract.status == status)
    if contract_type:
        query = query.filter(Contract.contract_type == contract_type)
    
    contracts = query.order_by(Contract.created_at.desc()).offset(skip).limit(limit).all()
    return contracts


@router.get("/contracts/{contract_id}", response_model=ContractWithDetails)
async def get_contract(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get contract with full analysis details"""
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.owner_id == current_user.id
    ).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return contract


@router.get("/contracts/{contract_id}/analysis", response_model=ContractAnalysisResponse)
async def get_contract_analysis(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get contract analysis results"""
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.owner_id == current_user.id
    ).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract.status != ContractStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Contract analysis not yet completed")
    
    return ContractAnalysisResponse(
        contract_id=contract.id,
        clause_analysis=contract.clause_analysis or [],
        risk_summary=contract.risk_summary or {},
        redline_docx_url=f"/api/v1/contracts/{contract.id}/download/docx" if contract.redline_docx_path else None,
        redline_pdf_url=f"/api/v1/contracts/{contract.id}/download/pdf" if contract.redline_pdf_path else None,
    )


@router.get("/contracts/{contract_id}/download/docx")
async def download_redline_docx(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download redlined DOCX"""
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.owner_id == current_user.id
    ).first()
    
    if not contract or not contract.redline_docx_path:
        raise HTTPException(status_code=404, detail="Redlined document not found")
    
    if not os.path.exists(contract.redline_docx_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        contract.redline_docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{os.path.splitext(contract.original_filename)[0]}_redlined.docx"
    )


@router.get("/contracts/{contract_id}/download/pdf")
async def download_redline_pdf(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download redlined PDF"""
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.owner_id == current_user.id
    ).first()
    
    if not contract or not contract.redline_pdf_path:
        raise HTTPException(status_code=404, detail="Redlined PDF not found")
    
    if not os.path.exists(contract.redline_pdf_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        contract.redline_pdf_path,
        media_type="application/pdf",
        filename=f"{os.path.splitext(contract.original_filename)[0]}_redlined.pdf"
    )


@router.delete("/contracts/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a contract"""
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.owner_id == current_user.id
    ).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Delete files
    for path in [contract.redline_docx_path, contract.redline_pdf_path]:
        if path and os.path.exists(path):
            os.remove(path)
    
    # Delete original file
    original_path = settings.UPLOAD_DIR / str(current_user.id) / contract.filename
    if original_path.exists():
        original_path.unlink()
    
    db.delete(contract)
    db.commit()
    
    logger.info("contract_deleted", contract_id=str(contract_id), user_id=str(current_user.id))


# ==================== Playbook Management ====================

@router.post("/playbooks", response_model=PlaybookResponse, status_code=status.HTTP_201_CREATED)
async def create_playbook(
    playbook: PlaybookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new playbook"""
    # If this is set as default, unset other defaults
    if playbook.is_default:
        db.query(Playbook).filter(
            Playbook.owner_id == current_user.id,
            Playbook.is_default == True
        ).update({"is_default": False})
    
    db_playbook = Playbook(
        **playbook.model_dump(),
        owner_id=current_user.id,
    )
    db.add(db_playbook)
    db.commit()
    db.refresh(db_playbook)
    
    return db_playbook


@router.get("/playbooks", response_model=List[PlaybookResponse])
async def list_playbooks(
    skip: int = 0,
    limit: int = 50,
    contract_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's playbooks"""
    query = db.query(Playbook).filter(Playbook.owner_id == current_user.id)
    
    if contract_type:
        query = query.filter(Playbook.contract_type == contract_type)
    
    playbooks = query.order_by(Playbook.created_at.desc()).offset(skip).limit(limit).all()
    return playbooks


@router.get("/playbooks/{playbook_id}", response_model=PlaybookWithRules)
async def get_playbook(
    playbook_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get playbook with all rules"""
    playbook = db.query(Playbook).filter(
        Playbook.id == playbook_id,
        Playbook.owner_id == current_user.id
    ).first()
    
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    # Load rules
    rules = db.query(ClauseRule).filter(ClauseRule.playbook_id == playbook_id).order_by(ClauseRule.order).all()
    playbook.rules = rules
    
    return playbook


@router.put("/playbooks/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook(
    playbook_id: uuid.UUID,
    playbook_update: PlaybookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a playbook"""
    playbook = db.query(Playbook).filter(
        Playbook.id == playbook_id,
        Playbook.owner_id == current_user.id
    ).first()
    
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    update_data = playbook_update.model_dump(exclude_unset=True)
    
    # Handle default flag
    if update_data.get("is_default"):
        db.query(Playbook).filter(
            Playbook.owner_id == current_user.id,
            Playbook.is_default == True
        ).update({"is_default": False})
    
    for field, value in update_data.items():
        setattr(playbook, field, value)
    
    playbook.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(playbook)
    
    return playbook


@router.delete("/playbooks/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playbook(
    playbook_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a playbook"""
    playbook = db.query(Playbook).filter(
        Playbook.id == playbook_id,
        Playbook.owner_id == current_user.id
    ).first()
    
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    db.delete(playbook)
    db.commit()


# ==================== Clause Rules ====================

@router.post("/playbooks/{playbook_id}/rules", response_model=ClauseRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_clause_rule(
    playbook_id: uuid.UUID,
    rule: ClauseRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a rule to a playbook"""
    playbook = db.query(Playbook).filter(
        Playbook.id == playbook_id,
        Playbook.owner_id == current_user.id
    ).first()
    
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    db_rule = ClauseRule(
        **rule.model_dump(),
        playbook_id=playbook_id,
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    return db_rule


@router.put("/playbooks/{playbook_id}/rules/{rule_id}", response_model=ClauseRuleResponse)
async def update_clause_rule(
    playbook_id: uuid.UUID,
    rule_id: uuid.UUID,
    rule_update: ClauseRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a clause rule"""
    rule = db.query(ClauseRule).join(Playbook).filter(
        ClauseRule.id == rule_id,
        ClauseRule.playbook_id == playbook_id,
        Playbook.owner_id == current_user.id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    update_data = rule_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    rule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rule)
    
    return rule


@router.delete("/playbooks/{playbook_id}/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clause_rule(
    playbook_id: uuid.UUID,
    rule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a clause rule"""
    rule = db.query(ClauseRule).join(Playbook).filter(
        ClauseRule.id == rule_id,
        ClauseRule.playbook_id == playbook_id,
        Playbook.owner_id == current_user.id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db.delete(rule)
    db.commit()


# ==================== Job Status ====================

@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get processing job status"""
    from app.models.contract import ProcessingJob
    from app.models.contract import Contract
    
    job = db.query(ProcessingJob).join(Contract).filter(
        ProcessingJob.task_id == job_id,
        Contract.owner_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.task_id,
        "contract_id": job.contract_id,
        "status": job.status,
        "progress": job.progress,
        "current_step": job.current_step,
        "result": job.result,
        "error": job.error,
    }


# ==================== Dashboard Stats ====================

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics"""
    from sqlalchemy import func
    
    total_contracts = db.query(func.count(Contract.id)).filter(
        Contract.owner_id == current_user.id
    ).scalar()
    
    completed = db.query(func.count(Contract.id)).filter(
        Contract.owner_id == current_user.id,
        Contract.status == ContractStatus.COMPLETED
    ).scalar()
    
    processing = db.query(func.count(Contract.id)).filter(
        Contract.owner_id == current_user.id,
        Contract.status == ContractStatus.PROCESSING
    ).scalar()
    
    failed = db.query(func.count(Contract.id)).filter(
        Contract.owner_id == current_user.id,
        Contract.status == ContractStatus.FAILED
    ).scalar()
    
    # Average risk score
    avg_risk = db.query(func.avg(Contract.risk_summary["overall_risk_score"].astext.cast(float))).filter(
        Contract.owner_id == current_user.id,
        Contract.status == ContractStatus.COMPLETED
    ).scalar() or 0
    
    # Contracts by type
    by_type = db.query(Contract.contract_type, func.count(Contract.id)).filter(
        Contract.owner_id == current_user.id
    ).group_by(Contract.contract_type).all()
    
    return {
        "total_contracts": total_contracts,
        "completed": completed,
        "processing": processing,
        "failed": failed,
        "average_risk_score": round(float(avg_risk), 1),
        "by_type": dict(by_type),
    }