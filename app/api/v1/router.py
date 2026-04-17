from fastapi import APIRouter
from app.api.v1 import cohorts, trades, ledger, auth, dashboard, groups


api_router = APIRouter()

api_router.include_router(cohorts.router  , prefix="/cohorts"  , tags=["Cohorts"])
api_router.include_router(trades.router   , prefix="/trades"   , tags=["Trades"])
api_router.include_router(ledger.router   , prefix="/ledger"   , tags=["Ledger"])
api_router.include_router(auth.router     , prefix="/auth"     , tags=["Auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(groups.router   , prefix="/groups"   , tags=["Groups"])