from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Nymintra",
    version="1.0.0"
)
from fastapi.middleware.gzip import GZipMiddleware

# Set up GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Set up CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Nymintra API is running"}
