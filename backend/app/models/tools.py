from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Tool(Base):
    """
    The tools table in PostgreSQL.
    Each tool = a Python class that agents can call to do real-world tasks.
    user_id links it to the person who created it.
    """
    __tablename__ = "tools"

    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # ── Metadata ──────────────────────────────────────────
    name        = Column(String(200), nullable=False)
    description = Column(Text,        nullable=True)

    # ── Code ──────────────────────────────────────────────
    # tool_class: the Python class name (e.g. "GitHubValidationTool")
    tool_class  = Column(String(200), nullable=True)
    # code: the full Python code the user writes in the Monaco editor
    code        = Column(Text, nullable=True)

    # ── Categorization ─────────────────────────────────────
    practice_area = Column(String(100), nullable=True)
    good_at       = Column(JSON, default=list)
    # function_type: what kind of thing this tool does
    # Options: data_retrieval, computation, action_executor, content_generator
    function_type = Column(String(50), nullable=True)
    # methodology: how the tool is meant to be used
    # Options: quick_use, chained
    methodology   = Column(String(50), nullable=True)

    # ── Status ─────────────────────────────────────────────
    status     = Column(String(20), default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())