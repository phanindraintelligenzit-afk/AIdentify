"""API routes."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import get_settings
from app.models.report import Report, DataSource, ReportSchedule, ReportSource
from app.schemas.report import (
    DataSourceCreate, DataSourceResponse,
    ReportCreate, ReportUpdate, ReportResponse,
    GenerateRequest, HealthResponse,
)
from app.services.report_generator import generate_report_content, TEMPLATES

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(db: AsyncSession = Depends(get_db)):
    report_count = await db.scalar(select(func.count(Report.id)))
    ds_count = await db.scalar(select(func.count(DataSource.id)))
    sched_count = await db.scalar(select(func.count(ReportSchedule.id)))
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        total_reports=report_count or 0,
        total_data_sources=ds_count or 0,
        scheduled_reports=sched_count or 0,
    )


@router.get("/templates")
async def list_templates():
    return {"templates": [{"id": k, "name": v} for k, v in TEMPLATES.items()]}


# Data Sources
@router.post("/data-sources", response_model=DataSourceResponse, status_code=201)
async def create_data_source(payload: DataSourceCreate, db: AsyncSession = Depends(get_db)):
    ds = DataSource(
        name=payload.name,
        source_type=payload.source_type,
        config=payload.config,
        status="active",
    )
    db.add(ds)
    await db.commit()
    await db.refresh(ds)
    return ds


@router.get("/data-sources", response_model=list[DataSourceResponse])
async def list_data_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DataSource).order_by(DataSource.created_at.desc()))
    return result.scalars().all()


@router.get("/data-sources/{source_id}", response_model=DataSourceResponse)
async def get_data_source(source_id: int, db: AsyncSession = Depends(get_db)):
    ds = await db.get(DataSource, source_id)
    if not ds:
        raise HTTPException(404, "Data source not found")
    return ds


@router.delete("/data-sources/{source_id}", status_code=204)
async def delete_data_source(source_id: int, db: AsyncSession = Depends(get_db)):
    ds = await db.get(DataSource, source_id)
    if not ds:
        raise HTTPException(404, "Data source not found")
    await db.delete(ds)
    await db.commit()


# Reports
@router.post("/reports", response_model=ReportResponse, status_code=201)
async def create_report(payload: ReportCreate, db: AsyncSession = Depends(get_db)):
    report = Report(
        title=payload.title,
        description=payload.description,
        template_type=payload.template_type,
        output_format=payload.output_format,
        status="draft",
    )
    db.add(report)
    await db.flush()

    if payload.data_source_ids:
        for ds_id in payload.data_source_ids:
            ds = await db.get(DataSource, ds_id)
            if ds:
                await db.execute(
                    ReportSource.__table__.insert().values(
                        report_id=report.id, data_source_id=ds_id
                    )
                )

    await db.commit()

    # Re-fetch with eagerly loaded relationship
    result = await db.execute(
        select(Report).options(selectinload(Report.data_sources)).where(Report.id == report.id)
    )
    return result.scalar_one()


@router.get("/reports", response_model=list[ReportResponse])
async def list_reports(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Report).options(selectinload(Report.data_sources)).order_by(Report.created_at.desc())
    if status_filter:
        query = query.where(Report.status == status_filter)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).options(selectinload(Report.data_sources)).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not found")
    return report


@router.patch("/reports/{report_id}", response_model=ReportResponse)
async def update_report(report_id: int, payload: ReportUpdate, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(report, k, v)
    await db.commit()
    await db.refresh(report)
    return report


@router.delete("/reports/{report_id}", status_code=204)
async def delete_report(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    await db.delete(report)
    await db.commit()


# Generate
@router.post("/generate", response_model=ReportResponse)
async def generate_report(payload: GenerateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).options(selectinload(Report.data_sources)).where(Report.id == payload.report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not found")

    report.status = "generating"
    await db.commit()

    try:
        sources_data = [
            {"id": ds.id, "name": ds.name, "source_type": ds.source_type, "config": ds.config}
            for ds in report.data_sources
        ]

        content, metrics = generate_report_content(
            title=report.title,
            template_type=report.template_type,
            data_sources=sources_data,
            output_format=report.output_format,
        )

        report.generated_content = content
        report.metrics = metrics
        report.status = "completed"
        report.generated_at = func.now()
        await db.commit()
        await db.refresh(report)
        return report
    except Exception as e:
        report.status = "error"
        await db.commit()
        raise HTTPException(500, f"Generation failed: {str(e)}")


@router.get("/reports/{report_id}/content")
async def get_report_content(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    if not report.generated_content:
        raise HTTPException(400, "Report not yet generated")
    return {"content": report.generated_content, "format": report.output_format}
