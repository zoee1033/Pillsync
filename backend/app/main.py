from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import Base, engine

# Import all models
from app.models import *

# Scheduler
from app.scheduler.scheduler import start_scheduler, stop_scheduler

# Routers
from app.routes.auth_routes import router as auth_router
from app.routes.profile_routes import router as profile_router
from app.routes.treatment_routes import router as treatment_router
from app.routes.medicine_routes import router as medicine_router
from app.routes.reminder_routes import router as reminder_router
from app.routes.history_routes import router as history_router
from app.routes.notification_routes import router as notification_router
from app.routes.device_token_routes import router as device_token_router
from app.routes.ocr_routes import router as ocr_router
from app.routes.analytics_routes import router as analytics_router
from app.routes.websocket_routes import router as websocket_router
from app.routes.sse_routes import router as sse_router
from app.routes.caregiver_routes import router as caregiver_router
from app.routes.admin_routes import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.logging_config import setup_logging
    setup_logging()

    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Auto-migrate optional profile columns on users table
    with engine.begin() as conn:
        for col_def in [
            "ADD COLUMN IF NOT EXISTS age INTEGER",
            "ADD COLUMN IF NOT EXISTS gender VARCHAR(20)",
            "ADD COLUMN IF NOT EXISTS blood_group VARCHAR(10)",
            "ADD COLUMN IF NOT EXISTS weight VARCHAR(20)",
            "ADD COLUMN IF NOT EXISTS height VARCHAR(20)",
            "ADD COLUMN IF NOT EXISTS medical_conditions TEXT",
            "ADD COLUMN IF NOT EXISTS allergies TEXT",
            "ADD COLUMN IF NOT EXISTS emergency_contact VARCHAR(100)",
            "ADD COLUMN IF NOT EXISTS primary_doctor VARCHAR(100)",
            "ADD COLUMN IF NOT EXISTS hospital VARCHAR(100)",
            "ADD COLUMN IF NOT EXISTS language VARCHAR(50) DEFAULT 'English'",
            "ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC'",
            "ADD COLUMN IF NOT EXISTS reminder_preferences TEXT",
        ]:
            conn.execute(text(f"ALTER TABLE users {col_def};"))

    # Start background scheduler
    start_scheduler()

    import logging
    logging.info("PillSync Backend & Scheduler initialized successfully.")

    yield

    stop_scheduler()
    logging.info("PillSync Backend Stopped.")


app = FastAPI(
    title="PillSync API",
    version="1.0.0",
    description="AI Powered Medicine Reminder Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(treatment_router)
app.include_router(medicine_router)
app.include_router(reminder_router)
app.include_router(history_router)
app.include_router(notification_router)
app.include_router(device_token_router)
app.include_router(ocr_router)
app.include_router(analytics_router)
app.include_router(websocket_router)
app.include_router(sse_router)
app.include_router(caregiver_router)
app.include_router(admin_router)



@app.get("/")
def home():
    return {
        "message": "Welcome to PillSync API 🚀"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/db-test")
def database():
    with engine.connect() as connection:
        version = connection.execute(
            text("SELECT version();")
        ).scalar()

    return {
        "database": "Connected Successfully",
        "version": version
    }