from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_v1_router
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic (e.g. database connectivity check or bot startup)
    yield
    # Shutdown logic


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CRM та система управління доставками торфу для сімейного підприємства",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["System"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy"}
