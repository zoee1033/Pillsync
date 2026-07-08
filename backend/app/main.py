from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

# Import models
from app.models.user import User

# Import router
from app.routes.auth_routes import router as auth_router
from app.routes.profile_routes import router as profile_router

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PillSync API",
    version="1.0.0",
    description="AI Powered Medicine Reminder Platform"
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

# Include routes
app.include_router(auth_router)
app.include_router(profile_router)



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