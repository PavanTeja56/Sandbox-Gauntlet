from fastapi import APIRouter
from sqlalchemy import text
from app.database import engine

router = APIRouter()


@router.get("/health")
def health():
    # Application liveness
    return {"status": "ok"}


@router.get("/health/ready")
def readiness():
    # Dependency readiness check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ready"}
    except Exception as e:
        return {"status": "degraded", "database": str(e)}
