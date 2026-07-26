from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Workflow(Base):
    """
    The workflows table.
    
    Key design decision: we store the entire React Flow canvas state
    (nodes + edges) as JSON columns rather than separate tables.
    
    Why: workflow topology is deeply nested and changes together.
    Storing it as JSON is simpler than normalizing into 3+ tables,
    and PostgreSQL's JSONB column is fast and queryable.
    
    nodes example: [
      { "id": "node_1", "type": "agentNode", "position": {"x": 100, "y": 200},
        "data": { "agent_id": 3, "agent_name": "Pipeline Monitor",
                  "avatar_emoji": "🤖", "execution_type": "sequential" } }
    ]
    
    edges example: [
      { "id": "edge_1", "source": "node_1", "target": "node_2",
        "type": "smoothstep", "animated": true }
    ]
    """
    __tablename__ = "workflows"

    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # ── Metadata ──────────────────────────────────────────
    name          = Column(String(200), nullable=False)
    description   = Column(Text,        nullable=True)
    practice_area = Column(String(100), nullable=True)
    good_at       = Column(JSON, default=list)

    # ── Canvas state ──────────────────────────────────────
    # nodes = list of React Flow node objects
    nodes = Column(JSON, default=list)
    # edges = list of React Flow edge objects
    edges = Column(JSON, default=list)

    # ── Status ────────────────────────────────────────────
    status     = Column(String(20), default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())