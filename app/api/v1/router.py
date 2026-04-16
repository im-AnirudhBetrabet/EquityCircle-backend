from fastapi import APIRouter
from app.api.v1 import cohorts


api_router = APIRouter()

api_router.include_router(cohorts.router, prefix="/cohorts", tags=["Cohorts"])

