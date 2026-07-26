from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Guardrail(Base):
    """
    Guardrails — safety and compliance rules attached to agents.
    When an agent runs, these rules are injected into the system prompt
    to constrain what the agent can say or do.
    """
    __tablename__ = "guardrails"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    name          = Column(String(200), nullable=False)
    description   = Column(Text, nullable=True)   # what this guardrail does
    rules         = Column(Text, nullable=True)    # the actual rules text
    practice_area = Column(String(100), nullable=True)

    status        = Column(String(20), default="draft")
    created_at    = Column(DateTime(timezone=True), server_default=func.now())