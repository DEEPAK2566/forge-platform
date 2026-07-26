from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class KBCreate(BaseModel):
    name:          str
    description:   Optional[str]       = None
    search_type:   Optional[str]       = "quick_search"
    chunk_size:    Optional[int]       = 1000
    practice_area: Optional[str]       = None
    good_at:       Optional[List[str]] = []
    methodology:   Optional[str]       = None
    status:        Optional[str]       = "draft"

class KBUpdate(BaseModel):
    name:          Optional[str]       = None
    description:   Optional[str]       = None
    search_type:   Optional[str]       = None
    chunk_size:    Optional[int]       = None
    practice_area: Optional[str]       = None
    good_at:       Optional[List[str]] = None
    methodology:   Optional[str]       = None
    status:        Optional[str]       = None

class KBDocumentOut(BaseModel):
    id:            int
    kb_id:         int
    filename:      str
    file_size:     Optional[int]
    chunk_count:   Optional[int]
    status:        Optional[str]
    error_message: Optional[str]
    created_at:    Optional[datetime]
    model_config = {"from_attributes": True}

class KBOut(BaseModel):
    id:              int
    user_id:         int
    name:            str
    description:     Optional[str]
    search_type:     Optional[str]
    chunk_size:      Optional[int]
    practice_area:   Optional[str]
    good_at:         Optional[List[str]]
    methodology:     Optional[str]
    collection_name: Optional[str]
    status:          Optional[str]
    created_at:      Optional[datetime]
    documents:       Optional[List[KBDocumentOut]] = []
    model_config = {"from_attributes": True}