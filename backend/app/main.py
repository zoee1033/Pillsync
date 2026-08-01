from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import Base, engine

# Import all models
from app.models import *

# Scheduler
from app.scheduler.scheduler import start_scheduler

# Routers
from app.routes.auth_routes import router as auth_router
from app.routes.profile_routes import router as profile_router
from app.routes.treatment_routes import router as treatment_router
from app.routes.medicine_routes import router as medicine_router
from app.routes.reminder_routes import router as reminder_router
from app.routes.history_routes import router as history_router
from app.routes.notification_routes import router as notification_router
from app.routes.device_token_routes import router as device_token_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Start background scheduler
    start_scheduler()

    print("✅ PillSync Backend Started")
    print("✅ Scheduler Started")

    yield

    print("🛑 PillSync Backend Stopped")


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