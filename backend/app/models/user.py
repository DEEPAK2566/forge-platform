from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    # __tablename__ tells SQLAlchemy what to name the table in PostgreSQL
    __tablename__ = "users"

    # Column definitions — each becomes one column in the database table
    # primary_key=True  → this column uniquely identifies each row
    # index=True        → makes searching by this column faster
    # unique=True       → no two rows can have the same value
    # nullable=False    → this field is required, cannot be empty
    # default=True      → if not provided, use this value

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    full_name       = Column(String, nullable=True)      # optional
    hashed_password = Column(String, nullable=False)     # we never store plain passwords
    is_active       = Column(Boolean, default=True)
    
    # server_default=func.now() → the database sets this to current time automatically
    created_at = Column(DateTime(timezone=True), server_default=func.now())