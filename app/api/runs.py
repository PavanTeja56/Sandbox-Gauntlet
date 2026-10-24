from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import RunRecord
from app.schemas import RunCreate, RunResponse

router = APIRouter()


@router.get("/runs", response_model=list[RunResponse])
def get_runs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Return the persisted run ledger, including seeded records."""
    records = db.query(RunRecord).order_by(RunRecord.created_at.desc()).offset(offset).limit(limit).all()
    return [r.to_dict() for r in records]


@router.post("/runs", status_code=status.HTTP_201_CREATED, response_model=RunResponse)
def create_run(
    payload: RunCreate,
    db: Session = Depends(get_db)
):
    """Record a run in the Run Ledger."""
    existing = db.query(RunRecord).filter(RunRecord.run_id == payload.run_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run with id '{payload.run_id}' already exists."
        )

    record = RunRecord(
        run_id=payload.run_id,
        sandbox_name=payload.sandbox_name,
        problem_id=payload.problem_id,
        state=payload.state,
        execution_target=payload.execution_target
    )
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicate identifier or constraint violation for run_id '{payload.run_id}'."
        )

    return record.to_dict()
