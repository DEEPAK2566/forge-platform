"""
Discover endpoints — returns published artifacts from all users.
This is the "marketplace" view — anyone logged in can browse everything published.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.agent import Agent
from app.models.workflow import Workflow
from app.models.tools import Tool
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.schemas.agent import AgentOut
from app.schemas.workflow import WorkflowOut
from app.schemas.tools import ToolOut
from app.schemas.knowledge_base import KBOut
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/discover", tags=["Discover"])


@router.get("/agents", response_model=List[AgentOut])
def discover_agents(
    search: str = "",
    limit:  int = 50,
    db:     Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    GET /discover/agents?search=...
    Returns all published agents from all users.
    The 'search' parameter filters by name (case-insensitive).
    """
    query = db.query(Agent).filter(Agent.status == "published")
    if search.strip():
        query = query.filter(Agent.name.ilike(f"%{search}%"))
    return query.order_by(Agent.created_at.desc()).limit(limit).all()


@router.get("/workflows", response_model=List[WorkflowOut])
def discover_workflows(
    search: str = "",
    limit:  int = 50,
    db:     Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET /discover/workflows — all published workflows."""
    query = db.query(Workflow).filter(Workflow.status == "published")
    if search.strip():
        query = query.filter(Workflow.name.ilike(f"%{search}%"))
    return query.order_by(Workflow.created_at.desc()).limit(limit).all()


@router.get("/tools", response_model=List[ToolOut])
def discover_tools(
    search: str = "",
    limit:  int = 50,
    db:     Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET /discover/tools — all published tools."""
    query = db.query(Tool).filter(Tool.status == "published")
    if search.strip():
        query = query.filter(Tool.name.ilike(f"%{search}%"))
    return query.order_by(Tool.created_at.desc()).limit(limit).all()


@router.get("/knowledge-bases", response_model=List[KBOut])
def discover_kbs(
    search: str = "",
    limit:  int = 50,
    db:     Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET /discover/knowledge-bases — all published knowledge bases."""
    query = db.query(KnowledgeBase).filter(KnowledgeBase.status == "published")
    if search.strip():
        query = query.filter(KnowledgeBase.name.ilike(f"%{search}%"))
    return query.order_by(KnowledgeBase.created_at.desc()).limit(limit).all()


@router.get("/stats")
def discover_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET /discover/stats — counts of all published artifacts, shown at top of Discover."""
    return {
        "agents":          db.query(Agent).filter(Agent.status == "published").count(),
        "workflows":       db.query(Workflow).filter(Workflow.status == "published").count(),
        "tools":           db.query(Tool).filter(Tool.status == "published").count(),
        "knowledge_bases": db.query(KnowledgeBase).filter(KnowledgeBase.status == "published").count(),
    }