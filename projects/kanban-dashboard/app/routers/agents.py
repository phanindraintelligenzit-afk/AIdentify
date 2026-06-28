"""
Agent router - Endpoints for agent integration, webhooks, and agent-specific operations.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import verify_admin_key, verify_api_key
from app.database import get_db
from app.models import (
    AgentType,
    Board,
    Column,
    Label,
    Tag,
    Task,
    TaskPriority,
    TaskStatus,
    Webhook,
)
from app.schemas import (
    AgentTaskCreate,
    AgentTaskUpdate,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    WebhookCreate,
    WebhookResponse,
)
from app.services import trigger_webhooks
from app.websocket import manager
from app.routers.tasks import _get_task_with_relations, _task_with_activity_response, _log_activity

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ─── Agent Task Endpoints ─────────────────────────────────────────

@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def agent_create_task(
    data: AgentTaskCreate,
    agent: str = Depends(lambda: "owl"),
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """
    Create a task from an agent context.
    Agents can create tasks and assign labels/tags by name.
    """
    # Determine board
    board_id = data.board_id
    if not board_id:
        result = await db.execute(
            select(Board).where(Board.is_active == True).order_by(Board.id)
        )
        board = result.scalar_one_or_none()
        if not board:
            raise HTTPException(status_code=400, detail="No active board found")
        board_id = board.id

    # Determine column (backlog by default)
    result = await db.execute(
        select(Column).where(Column.board_id == board_id).order_by(Column.position)
    )
    column = result.scalar_one_or_none()
    if not column:
        raise HTTPException(status_code=400, detail="No column found")

    from sqlalchemy import func
    pos_result = await db.execute(
        select(func.max(Task.position)).where(Task.column_id == column.id)
    )
    max_pos = pos_result.scalar() or 0

    current_agent = auth.get("agent", "owl")

    task = Task(
        board_id=board_id,
        column_id=column.id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        assignee=current_agent,
        due_date=data.due_date,
        position=max_pos + 1,
    )
    db.add(task)
    await db.flush()

    # Handle labels by name
    if data.labels:
        for label_name in data.labels:
            result = await db.execute(select(Label).where(Label.name == label_name))
            label = result.scalar_one_or_none()
            if not label:
                label = Label(name=label_name)
                db.add(label)
                await db.flush()
            task.labels.append(label)

    # Handle tags by name
    if data.tags:
        for tag_name in data.tags:
            result = await db.execute(select(Tag).where(Tag.name == tag_name))
            tag = result.scalar_one_or_none()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                await db.flush()
            task.tags.append(tag)

    await _log_activity(db, task.id, "created", f"Task created by agent: {current_agent}", current_agent)
    await db.refresh(task)

    task_data = _task_with_activity_response(task)
    await trigger_webhooks("task.created", task_data)
    await manager.broadcast_to_board(board_id, {
        "type": "task_created",
        "task": task_data,
    })

    return task


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def agent_update_task(
    task_id: int,
    data: AgentTaskUpdate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """
    Update a task from an agent context.
    Agents can update status, priority, etc.
    """
    task = await _get_task_with_relations(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    current_agent = auth.get("agent", "owl")
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if value is not None:
            if hasattr(value, 'value'):
                value = value.value
            setattr(task, key, value)

    if data.status == TaskStatus.DONE:
        task.is_completed = True
    elif data.status and data.status != TaskStatus.DONE:
        task.is_completed = False

    await _log_activity(db, task.id, "updated", f"Updated by agent: {current_agent}", current_agent)
    await db.flush()
    await db.refresh(task)

    task_data = _task_with_activity_response(task)
    await trigger_webhooks("task.updated", task_data)
    await manager.broadcast_to_board(task.board_id, {
        "type": "task_updated",
        "task": task_data,
    })

    return task


@router.get("/tasks", response_model=List[TaskResponse])
async def agent_list_tasks(
    agent: Optional[str] = Query(None, description="Filter by assigned agent"),
    status: Optional[TaskStatus] = Query(None),
    board_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """
    List tasks for agent context. Defaults to current agent's tasks.
    """
    query = (
        select(Task)
        .options(
            selectinload(Task.labels),
            selectinload(Task.tags),
        )
    )

    current_agent = auth.get("agent", "owl")
    if agent:
        query = query.where(Task.assignee == agent)
    else:
        query = query.where(Task.assignee == current_agent)

    if status:
        query = query.where(Task.status == status)
    if board_id:
        query = query.where(Task.board_id == board_id)

    query = query.order_by(Task.position, Task.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/workload")
async def agent_workload(
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """Get workload summary for all agents."""
    from sqlalchemy import func

    current_agent = auth.get("agent", "owl")

    result = await db.execute(
        select(Task.assignee, Task.status, func.count(Task.id))
        .where(Task.status != TaskStatus.DONE)
        .group_by(Task.assignee, Task.status)
    )

    workload = {}
    for row in result.all():
        agent_name = row[0] or "unassigned"
        if agent_name not in workload:
            workload[agent_name] = {}
        workload[agent_name][row[1].value] = row[2]

    return {
        "agent": current_agent,
        "workload": workload,
    }


# ─── Webhook Management ───────────────────────────────────────────

@router.get("/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_admin_key),
):
    """List all webhooks."""
    result = await db.execute(select(Webhook).order_by(Webhook.created_at.desc()))
    return result.scalars().all()


@router.post("/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_admin_key),
):
    """Register a new webhook."""
    import secrets

    webhook = Webhook(
        url=data.url,
        events=data.events,
        secret=data.secret or secrets.token_hex(32),
    )
    db.add(webhook)
    await db.flush()
    await db.refresh(webhook)
    return webhook


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_admin_key),
):
    """Delete a webhook."""
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.delete(webhook)


# ─── Agent Info ───────────────────────────────────────────────────

@router.get("/info")
async def agent_info(
    auth: dict = Depends(verify_api_key),
):
    """Get info about the current agent."""
    current_agent = auth.get("agent", "owl")
    role = auth.get("role", "agent")

    agent_details = {
        "researcher": {
            "name": "Research Agent",
            "description": "Handles research tasks, data gathering, and analysis",
            "capabilities": ["web_research", "data_analysis", "summarization"],
            "color": "#8b5cf6",
        },
        "writer": {
            "name": "Content Writer Agent",
            "description": "Creates and edits content, articles, and documentation",
            "capabilities": ["content_creation", "editing", "seo_optimization"],
            "color": "#ec4899",
        },
        "outreach": {
            "name": "Outreach Agent",
            "description": "Manages communications, partnerships, and outreach",
            "capabilities": ["email_outreach", "partnership_building", "follow_ups"],
            "color": "#f59e0b",
        },
        "social": {
            "name": "Social Media Agent",
            "description": "Manages social media presence and engagement",
            "capabilities": ["social_posting", "engagement", "analytics"],
            "color": "#10b981",
        },
        "owl": {
            "name": "Owl (Default Agent)",
            "description": "Default orchestration agent for general tasks",
            "capabilities": ["task_management", "coordination", "general"],
            "color": "#6366f1",
        },
    }

    return {
        "agent": current_agent,
        "role": role,
        "details": agent_details.get(current_agent, agent_details["owl"]),
        "available_agents": list(agent_details.keys()),
    }
