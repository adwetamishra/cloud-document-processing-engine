
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.documents import router as documents_router
from app.api.s3 import router as s3_router
from app.api.azure import router as azure_router
from app.api.saas import router as saas_router
from app.db.database import Base, engine
from app.models.document import Document


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables during startup
    Base.metadata.create_all(bind=engine)

    yield

    # Release database connections during shutdown
    engine.dispose()


app = FastAPI(
    title="Cloud Document Processing Engine",
    description="An API for uploading and processing documents from cloud storage.",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(documents_router)
app.include_router(s3_router)
app.include_router(azure_router)
app.include_router(saas_router)


@app.get("/")
def home():
    return {
        "message": "Cloud Document Processing Engine is running!",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Cloud Document Processing Engine"
    }
