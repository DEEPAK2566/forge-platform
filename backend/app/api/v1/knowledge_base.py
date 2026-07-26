from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.knowledge_base import KnowledgeBase, KBDocument
from app.models.user import User
from app.schemas.knowledge_base import KBCreate, KBUpdate, KBOut
from app.api.v1.auth import get_current_user
from app.services.rag_service import (
    add_documents_to_collection,
    delete_collection,
    extract_text,
    chunk_text,
)

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])


@router.post("/", response_model=KBOut, status_code=201)
def create_kb(
    data: KBCreate,
    db:   Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    POST /knowledge-bases/
    Creates a new Knowledge Base record.
    Files are added separately via the /upload endpoint.
    """
    kb = KnowledgeBase(user_id=current_user.id, **data.model_dump())
    db.add(kb)
    db.commit()
    db.refresh(kb)

    # Set the ChromaDB collection name now that we have the ID
    kb.collection_name = f"kb_{kb.id}"
    db.commit()
    db.refresh(kb)
    return kb


@router.post("/{kb_id}/upload")
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    db:   Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    POST /knowledge-bases/{id}/upload
    Uploads a file → extracts text → chunks it → stores in ChromaDB.
    """
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == current_user.id
    ).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Read the uploaded file into memory
    content = await file.read()

    # Create document record with status=processing
    doc = KBDocument(
        kb_id     = kb_id,
        filename  = file.filename,
        file_size = len(content),
        status    = "processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        # 1. Extract text from the file
        print(f"[KB Upload] Extracting text from: {file.filename}")
        text = extract_text(content, file.filename)

        if not text.strip():
            raise ValueError("No text could be extracted from this file.")

        print(f"[KB Upload] Extracted {len(text)} characters")

        # 2. Split into overlapping chunks
        chunks = chunk_text(text, chunk_size=kb.chunk_size or 1000)

        if not chunks:
            raise ValueError("File produced no text chunks after splitting.")

        print(f"[KB Upload] Created {len(chunks)} chunks")

        # 3. Unique ID for each chunk in ChromaDB
        chunk_ids = [f"doc_{doc.id}_chunk_{i}" for i in range(len(chunks))]

        # 4. Metadata stored alongside each vector
        metadatas = [
            {
                "filename":    file.filename,
                "chunk_index": i,
                "doc_id":      str(doc.id),
                "kb_id":       str(kb_id),
            }
            for i in range(len(chunks))
        ]

        # 5. Store in ChromaDB — embedding happens here
        print(f"[KB Upload] Storing in ChromaDB collection: {kb.collection_name}")
        add_documents_to_collection(
            kb.collection_name,
            chunks,
            metadatas,
            chunk_ids,
        )

        # 6. Mark as ready
        doc.chunk_count = len(chunks)
        doc.status      = "ready"
        db.commit()

        print(f"[KB Upload] ✓ Done — {len(chunks)} chunks stored")

        return {
            "message":    f"'{file.filename}' processed successfully",
            "chunks":     len(chunks),
            "characters": len(text),
        }

    except Exception as e:
        # Log the full error in the terminal
        import traceback
        print(f"[KB Upload] ERROR for {file.filename}:")
        traceback.print_exc()

        # Save error to DB so it shows in the UI
        doc.status        = "error"
        doc.error_message = str(e)
        db.commit()

        raise HTTPException(
            status_code = 500,
            detail      = f"Processing failed: {str(e)}",
        )

@router.get("/", response_model=List[KBOut])
def list_kbs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """GET /knowledge-bases/ — all KBs for the logged-in user."""
    kbs = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.user_id == current_user.id)
        .order_by(KnowledgeBase.created_at.desc())
        .all()
    )
    # Load documents for each KB
    for kb in kbs:
        kb.documents = db.query(KBDocument).filter(KBDocument.kb_id == kb.id).all()
    return kbs


@router.get("/count")
def count_kbs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    count = db.query(KnowledgeBase).filter(
        KnowledgeBase.user_id == current_user.id
    ).count()
    return {"count": count}


@router.get("/{kb_id}", response_model=KBOut)
def get_kb(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == current_user.id
    ).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    kb.documents = db.query(KBDocument).filter(KBDocument.kb_id == kb_id).all()
    return kb


@router.delete("/{kb_id}", status_code=204)
def delete_kb(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == current_user.id
    ).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Delete ChromaDB collection (vectors)
    if kb.collection_name:
        delete_collection(kb.collection_name)

    # Delete all documents from PostgreSQL
    db.query(KBDocument).filter(KBDocument.kb_id == kb_id).delete()

    # Delete KB record
    db.delete(kb)
    db.commit()