from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.database import Base


class RunRecord(Base):
    __tablename__ = "runs"

    run_id = Column(String(128), primary_key=True, index=True)
    sandbox_name = Column(String(128), nullable=False, index=True)
    problem_id = Column(String(128), nullable=False)
    state = Column(String(32), nullable=False)
    execution_target = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "run_id": self.run_id,
            "sandbox_name": self.sandbox_name,
            "problem_id": self.problem_id,
            "state": self.state,
            "execution_target": self.execution_target,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
