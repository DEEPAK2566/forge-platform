from pydantic import BaseModel
from typing import Optional

# ── Request schemas (data coming IN from the frontend) ──────────

class UserRegister(BaseModel):
    """Shape of data the frontend sends when registering a new user"""
    email:     str
    password:  str
    full_name: Optional[str] = None   # Optional = not required

class UserLogin(BaseModel):
    """Shape of data the frontend sends when logging in"""
    email:    str
    password: str

# ── Response schemas (data going OUT to the frontend) ───────────

class UserOut(BaseModel):
    """User data we are safe to send back — notice: no password field"""
    id:        int
    email:     str
    full_name: Optional[str]

    # from_attributes=True lets Pydantic read from SQLAlchemy model objects
    # Without this, Pydantic wouldn't know how to convert a User DB object to this schema
    model_config = {"from_attributes": True}

class AuthResponse(BaseModel):
    """Sent back after successful login or register"""
    access_token: str       # the JWT token — frontend stores this
    token_type:   str       # always "bearer"
    user:         UserOut   # the user's info