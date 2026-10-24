import re
from typing import Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict

ALLOWED_STATES = {"created", "ready", "running", "succeeded", "failed", "deleted"}
ALLOWED_TARGET = "celesto_sandbox"


class RunCreate(BaseModel):
    run_id: str = Field(..., min_length=1, description="Unique run identifier")
    sandbox_name: str = Field(..., description="Sandbox name matching sbx- followed by at least 8 lowercase alphanumeric characters")
    problem_id: str = Field(..., min_length=1, description="Problem identifier")
    state: str = Field(..., description="Lifecycle state")
    execution_target: str = Field(..., description="Must be exactly celesto_sandbox")

    @field_validator("sandbox_name")
    @classmethod
    def validate_sandbox_name(cls, v: str) -> str:
        if not v.startswith("sbx-"):
            raise ValueError("sandbox_name must start with 'sbx-'")
        suffix = v[4:]
        if len(suffix) < 8 or not re.match(r"^[a-z0-9]+$", suffix):
            raise ValueError("sandbox_name suffix must contain at least 8 lowercase alphanumeric characters")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        if v not in ALLOWED_STATES:
            raise ValueError(f"state must be one of {sorted(ALLOWED_STATES)}")
        return v

    @field_validator("execution_target")
    @classmethod
    def validate_execution_target(cls, v: str) -> str:
        if v != ALLOWED_TARGET:
            raise ValueError(f"execution_target must be exactly '{ALLOWED_TARGET}'")
        return v


class RunResponse(BaseModel):
    run_id: str
    sandbox_name: str
    problem_id: str
    state: str
    execution_target: str
    created_at: str | None = None

    model_config = ConfigDict(from_attributes=True)
