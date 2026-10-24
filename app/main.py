from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api import api_router
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and seed row on startup
    init_db()
    yield


app = FastAPI(
    title="Sandbox Gauntlet Control Plane",
    description="The Crash-Test Arena for AI Agents — Run Ledger & Control Plane",
    version="1.0.0",
    lifespan=lifespan
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # The hackathon specification requires HTTP 400 for invalid inputs
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({
            "detail": exc.errors(),
            "message": "Invalid request payload according to specification"
        })
    )


app.include_router(api_router)
