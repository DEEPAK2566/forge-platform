from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GuardrailCreate(BaseModel):
    name:          str
    description:   Optional[str] = None
    rules:         Optional[str] = None
    practice_area: Optional[str] = None
    status:        Optional[str] = "draft"

class GuardrailUpdate(BaseModel):
    name:          Optional[str] = None
    description:   Optional[str] = None
    rules:         Optional[str] = None
    practice_area: Optional[str] = None
    status:        Optional[str] = None

class GuardrailOut(BaseModel):
    id:            int
    user_id:       int
    name:          str
    description:   Optional[str]
    rules:         Optional[str]
    practice_area: Optional[str]
    status:        Optional[str]
    created_at:    Optional[datetime]
    model_config = {"from_attributes": True}