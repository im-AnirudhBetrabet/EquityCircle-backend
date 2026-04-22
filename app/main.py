from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from contextlib import asynccontextmanager
from app.services.scheduler import start_scheduler
from app.services.logger import sys_logger

@asynccontextmanager
async def lifespan(app:FastAPI):
    sys_logger.info("Initializing StoxCircle Server")

    start_scheduler()

    yield

    sys_logger.info("Shutting down server")

def get_application() -> FastAPI:

    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "https://stox-circle.vercel.app/"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    @application.get("/health", tags=["System"])
    def health_check():
        return {
            "status" : "online",
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION
        }

    application.include_router(api_router, prefix=settings.API_V1_STR)
    return application


app = get_application()