from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# ── Engine ────────────────────────────────────────────────────────
# The engine = the permanent connection to PostgreSQL
# pool_pre_ping=True: before using a connection, test it's alive
#                     prevents errors after the Supabase connection goes idle
if settings.DATABASE_URL:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
else:
    engine = None
    print("WARNING: DATABASE_URL not set in backend/.env")

# ── Session factory ───────────────────────────────────────────────
# Call SessionLocal() to get a fresh database session
# autocommit=False: changes aren't saved until we explicitly say db.commit()
# autoflush=False: don't auto-send pending changes
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None

# ── Base class ────────────────────────────────────────────────────
# All database tables (Agent, Tool, Workflow...) are Python classes
# They must inherit from Base so SQLAlchemy knows to create a table for each
class Base(DeclarativeBase):
    pass

# ── get_db() ──────────────────────────────────────────────────────
# FastAPI calls this before every API endpoint that needs database access
# "yield" means: run setup → give to endpoint → run cleanup no matter what
# This guarantees sessions are always closed — no memory leaks, no dangling connections
def get_db():
    if not SessionLocal:
        raise Exception("DATABASE_URL not set. Check backend/.env")
    db = SessionLocal()   # open session
    try:
        yield db          # endpoint uses it here
    finally:
        db.close()        # always close after

# ── test_connection() ─────────────────────────────────────────────
# Used by /health to verify the database is reachable
def test_connection():
    if not engine:
        return False, "DATABASE_URL is empty"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # simplest SQL — just tests connectivity
        return True, "Connected"
    except Exception as e:
        return False, str(e)