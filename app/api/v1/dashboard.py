from fastapi import APIRouter, HTTPException, Depends
from app.db.supabase import supabase
from app.core.security import get_current_user
from app.services.finance import get_live_prices
from app.services.math_engine import calculate_equity_splits

router = APIRouter()

@router.get("/summary/{group_id}")
def get_dashboard_summary(group_id: str, current_user = Depends(get_current_user)):
    """
    The Master endpoint. Assembles all data needed for the dashboard.
    """
    try:
        cohorts_res    = supabase.table("cohorts").select("*").eq("group_id", group_id).eq("status", "OPEN").execute()
        active_cohorts = cohorts_res.data

        cohort_ids = [c["id"] for c in cohorts_res]
        active_trades = []
        if cohort_ids:
            trades_res    = supabase.table("trades").select("*").in_("cohort_id", cohort_ids).eq("status", "OPEN").execute()
            active_trades = trades_res.data

            tickers     = [t["ticker_symbol"] for t in active_trades]
            live_prices = get_live_prices(tickers)

            for t in active_trades:
                t["current_price"] = live_prices.get(t["ticker_symbol"], 0.0)

        ledger_res  = supabase.table("ledger").select("*").eq("group_id", group_id).execute()
        equity_data = calculate_equity_splits(ledger_res.data) if ledger_res.data else { "total_pool": 0, "member_splits": {}}

        closed_trades_res = supabase.table("trades").select("*").in_("cohort_id", cohort_ids).eq("status", "CLOSED").order("sell_date", desc=True).limit(5).execute()

        return {
            "pool_equity"    : equity_data["total_pool"],
            "member_splits"  : equity_data["member_splits"],
            "active_cohorts" : active_cohorts,
            "active_holdings": active_trades,
            "recent_history" : closed_trades_res.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



