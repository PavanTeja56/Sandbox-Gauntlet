import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL

# Normalize postgresql:// to postgresql+psycopg2:// if psycopg2 is installed
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgresql://") and "+psycopg2" not in db_url and "+asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

try:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3} if "postgresql" in db_url else {}
    )
    with engine.connect() as conn:
        pass
except Exception as e:
    logger.warning(f"Could not connect to configured DATABASE_URL: {e}. Using SQLite fallback for offline operations.")
    db_url = "sqlite:///./sandbox_ledger.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables and ensure seeded record sbx-seeddemo1 is present."""
    from app.models import RunRecord
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        existing = db.query(RunRecord).filter(RunRecord.sandbox_name == "sbx-seeddemo1").first()
        if not existing:
            seed_row = RunRecord(
                run_id="seed-run-001",
                sandbox_name="sbx-seeddemo1",
                problem_id="seed_demonstration",
                state="deleted",
                execution_target="celesto_sandbox",
            )
            db.add(seed_row)
            db.commit()
            logger.info("Seeded record sbx-seeddemo1 inserted.")
    finally:
        db.close()
