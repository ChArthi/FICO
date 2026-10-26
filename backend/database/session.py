"""
Database Engine and Session Management.
Supports MySQL 8.0 with automatic fallback to SQLite for zero-failure resilience.
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.core.config import settings

logger = logging.getLogger("fico.database")

DATABASE_URL = settings.DATABASE_URL
FALLBACK_SQLITE_URL = settings.FALLBACK_SQLITE_URL

try:
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=False
    )
    # Validate connection immediately
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print(f"[Database] Successfully connected to primary DB: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
except Exception as e:
    print(f"[Database Warning] Failed to connect to primary DB: {e}. Falling back to SQLite.")
    DATABASE_URL = FALLBACK_SQLITE_URL
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for obtaining an isolated SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
