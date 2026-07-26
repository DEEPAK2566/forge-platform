from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class KnowledgeBase(Base):
    """
    The knowledge_bases table.
    Each KB = a collection of documents an agent can search through.
    ChromaDB stores the actual vectors — we store metadata here.
    """
    __tablename__ = "knowledge_bases"

    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # ── Identity ──────────────────────────────────────────────
    name        = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # ── Embedding settings ────────────────────────────────────
    # search_type: quick_search = smaller chunks, faster
    #              deep_context = larger chunks, more context per result
    search_type  = Column(String(50),  default="quick_search")
    chunk_size   = Column(Integer,     default=1000)  # characters per chunk

    # ── Categorization ────────────────────────────────────────
    practice_area = Column(String(100), nullable=True)
    good_at       = Column(JSON, default=list)
    methodology   = Column(String(50),  nullable=True)

    # ── ChromaDB link ─────────────────────────────────────────
    # The ChromaDB collection name for this KB
    # Format: "kb_{id}" e.g. "kb_3"
    collection_name = Column(String(200), nullable=True)

    # ── Status ────────────────────────────────────────────────
    status     = Column(String(20), default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class KBDocument(Base):
    """
    Each uploaded file inside a knowledge base.
    One KnowledgeBase can have many KBDocuments.
    """
    __tablename__ = "kb_documents"

    id            = Column(Integer, primary_key=True, index=True)
    kb_id         = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False, index=True)

    filename      = Column(String(500), nullable=False)
    file_size     = Column(Integer, nullable=True)   # bytes
    chunk_count   = Column(Integer, default=0)       # how many chunks ChromaDB stored

    # processing = currently being indexed
    # ready      = indexed and searchable
    # error      = something went wrong
    status        = Column(String(20), default="processing")
    error_message = Column(Text, nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())