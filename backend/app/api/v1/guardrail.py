from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.guardrail import Guardrail
from app.models.user import User
from app.schemas.guardrail import GuardrailCreate, GuardrailUpdate, GuardrailOut
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/guardrails", tags=["Guardrails"])


@router.post("/", response_model=GuardrailOut, status_code=201)
def create_guardrail(
    data: GuardrailCreate,
    db:   Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    g = Guardrail(user_id=current_user.id, **data.model_dump())
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@router.get("/", response_model=List[GuardrailOut])
def list_guardrails(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Guardrail)
        .filter(Guardrail.user_id == current_user.id)
        .order_by(Guardrail.created_at.desc())
        .all()
    )


@router.get("/{gid}", response_model=GuardrailOut)
def get_guardrail(
    gid: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    g = db.query(Guardrail).filter(
        Guardrail.id == gid,
        Guardrail.user_id == current_user.id
    ).first()
    if not g:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    return g


@router.put("/{gid}", response_model=GuardrailOut)
def update_guardrail(
    gid: int,
    data: GuardrailUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    g = db.query(Guardrail).filter(
        Guardrail.id == gid,
        Guardrail.user_id == current_user.id
    ).first()
    if not g:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(g, key, value)
    db.commit()
    db.refresh(g)
    return g


@router.delete("/{gid}", status_code=204)
def delete_guardrail(
    gid: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    g = db.query(Guardrail).filter(
        Guardrail.id == gid,
        Guardrail.user_id == current_user.id
    ).first()
    if not g:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    db.delete(g)
    db.commit()