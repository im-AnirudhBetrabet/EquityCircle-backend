from fastapi import APIRouter
from app.api.v1 import cohorts, trades


api_router = APIRouter()

api_router.include_router(cohorts.router, prefix="/cohorts", tags=["Cohorts"])
api_router.include_router(trades.router , prefix="/trades" , tags=["Trades"])
