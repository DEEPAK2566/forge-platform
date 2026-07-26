from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class WorkflowCreate(BaseModel):
    name:          str
    description:   Optional[str]       = None
    practice_area: Optional[str]       = None
    good_at:       Optional[List[str]] = []
    # nodes and edges are lists of React Flow objects (any shape)
    nodes:         Optional[List[Any]] = []
    edges:         Optional[List[Any]] = []
    status:        Optional[str]       = "draft"

class WorkflowUpdate(BaseModel):
    name:          Optional[str]       = None
    description:   Optional[str]       = None
    practice_area: Optional[str]       = None
    good_at:       Optional[List[str]] = None
    nodes:         Optional[List[Any]] = None
    edges:         Optional[List[Any]] = None
    status:        Optional[str]       = None

class WorkflowOut(BaseModel):
    id:            int
    user_id:       int
    name:          str
    description:   Optional[str]
    practice_area: Optional[str]
    good_at:       Optional[List[str]]
    nodes:         Optional[List[Any]]
    edges:         Optional[List[Any]]
    status:        Optional[str]
    created_at:    Optional[datetime]

    model_config = {"from_attributes": True}