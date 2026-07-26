from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ToolCreate(BaseModel):
    name:          str
    description:   Optional[str]       = None
    tool_class:    Optional[str]       = None
    code:          Optional[str]       = None
    practice_area: Optional[str]       = None
    good_at:       Optional[List[str]] = []
    function_type: Optional[str]       = None
    methodology:   Optional[str]       = None
    status:        Optional[str]       = "draft"

class ToolUpdate(BaseModel):
    """All fields optional — only send what changed."""
    name:          Optional[str]       = None
    description:   Optional[str]       = None
    tool_class:    Optional[str]       = None
    code:          Optional[str]       = None
    practice_area: Optional[str]       = None
    good_at:       Optional[List[str]] = None
    function_type: Optional[str]       = None
    methodology:   Optional[str]       = None
    status:        Optional[str]       = None

class ToolOut(BaseModel):
    id:            int
    user_id:       int
    name:          str
    description:   Optional[str]
    tool_class:    Optional[str]
    code:          Optional[str]
    practice_area: Optional[str]
    good_at:       Optional[List[str]]
    function_type: Optional[str]
    methodology:   Optional[str]
    status:        Optional[str]
    created_at:    Optional[datetime]

    model_config = {"from_attributes": True}