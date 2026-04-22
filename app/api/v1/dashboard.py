from fastapi import APIRouter, HTTPException, Depends
from app.db.supabase import supabase
from app.core.security import get_current_user, verify_group_membership
from app.services.finance import get_live_prices
from app.services.math_engine import calculate_equity_splits
from app.services.logger import sys_logger
router = APIRouter()

@router.get("/summary/{group_id}")
def get_dashboard_summary(group_id: str, current_user = Depends(get_current_user)):
    """
    The Master endpoint. Assembles all data needed for the dashboard.
    """
    try:
        user_role = verify_group_membership(current_user.id, group_id)

        group_res      = supabase.table("groups").select("name, created_at").eq("id", group_id).single().execute()
        group_data     = group_res.data

        members_res  = supabase.table("group_members").select("user_id, role, profiles(display_name)").eq("group_id", group_id).execute()
        members_data = members_res.data

        cohorts_res = supabase.table("cohorts").select("*").eq("group_id", group_id).order("created_at").execute()
        cohorts     = cohorts_res.data

        active_cohorts = [c for c in cohorts if c["status"] == "OPEN"]
        pending_requests = int()
        if user_role == "admin":
            req_res = supabase.table("group_requests").select("id, created_at, profiles(display_name)").eq("group_id", group_id).eq("status", "PENDING").execute()
            pending_requests = len(req_res.data)

        active_cohort_ids = [c["id"] for c in active_cohorts if c["status"] == "OPEN"]
        cohort_ids        = [c["id"] for c in cohorts]
        active_trades     = []

        if active_cohort_ids:
            trades_res    = supabase.table("trades").select("*").in_("cohort_id", active_cohort_ids).eq("status", "OPEN").execute()
            active_trades = trades_res.data

            tickers     = [t["ticker_symbol"] for t in active_trades]
            live_prices = get_live_prices(tickers)

            for t in active_trades:
                t["current_price"] = live_prices.get(t["ticker_symbol"], 0.0)

        ledger_res  = supabase.table("ledger").select("*").eq("group_id", group_id).execute()
        equity_data = calculate_equity_splits(ledger_res.data) if ledger_res.data else { "total_pool": 0, "member_splits": {}}

        response      = supabase.rpc("get_cohort_pool_totals_by_group", {"p_group_id": group_id}).execute()
        cohort_totals = response.data

        totals_map = {
            item["cohort_id"]: item["total_pool"]
            for item in cohort_totals
        }

        # Step 2: Merge into active_cohorts
        for cohort in active_cohorts:
            cohort["total_pool"] = totals_map.get(cohort["id"], 0.0)

        closed_trades_res = supabase.table("trades").select("*").in_("cohort_id", cohort_ids).eq("status", "CLOSED").order("sell_date", desc=True).limit(5).execute()
        closed_trades     = closed_trades_res.data

        running_pnl  = 0.0
        realized_pnl = 0.0
        for c in closed_trades:
            temp = (round(c["quantity"] * c["sell_price"], 2)) - (round(c["quantity"] * c["buy_price"], 2))
            realized_pnl += temp

        for a in active_trades:
            temp = (round(a["quantity"] * a["current_price"], 2)) - (round(a["quantity"] * a["buy_price"], 2))
            running_pnl += temp

        if user_role == "admin":
            return {
                "user_role"       : user_role,
                "group_info"      : group_data,
                "member_info"     : members_data,
                "pool_equity"     : equity_data["total_pool"],
                "member_splits"   : equity_data["member_splits"],
                "active_cohorts"  : active_cohorts,
                "active_holdings" : active_trades,
                "recent_history"  : closed_trades,
                "pending_requests": pending_requests,
                "profit_statement": {
                    "running" : round(float(running_pnl), 2),
                    "realized": round(float(realized_pnl), 2)
                }
            }
        else:
            return {
                "user_role"       : user_role,
                "group_info"      : group_data,
                "member_info"     : members_data,
                "pool_equity"     : equity_data["total_pool"],
                "member_splits"   : equity_data["member_splits"],
                "active_cohorts"  : active_cohorts,
                "active_holdings" : active_trades,
                "recent_history"  : closed_trades_res.data,
                "profit_statement": {
                    "running" : round(float(running_pnl), 2),
                    "realized": round(float(realized_pnl), 2)
                }
            }

    except Exception as e:
        sys_logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))



